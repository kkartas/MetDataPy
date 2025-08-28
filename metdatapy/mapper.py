from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml

from .units import (
    parse_unit_hint,
    fahrenheit_to_c,
    mph_to_ms,
    kmh_to_ms,
    mbar_to_hpa,
    pa_to_hpa,
    identity,
)
from .utils import PLAUSIBLE_BOUNDS


CANONICAL_FIELDS = [
    "temp_c",
    "rh_pct",
    "pres_hpa",
    "wspd_ms",
    "wdir_deg",
    "gust_ms",
    "rain_mm",
    "solar_wm2",
    "uv_index",
]


@dataclass
class FieldGuess:
    canonical: str
    source_col: str
    unit: Optional[str]
    confidence: float


class Mapper:
    """Loads and saves mapping files."""

    @staticmethod
    def load(path: str) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def save(mapping: Dict, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(mapping, f, sort_keys=False, allow_unicode=True)


class Detector:
    """Heuristic mapping detector based on column names and unit hints."""

    TIME_CANDIDATES = [
        r"^time$",
        r"^date$",
        r"^datetime$",
        r"^timestamp$",
        r".*(date[_\s-]*time).*",
    ]

    FIELD_PATTERNS: List[Tuple[str, List[str]]] = [
        ("temp_c", [r"temp", r"temperature"]),
        ("rh_pct", [r"rh", r"humid", r"relative[_\s-]*hum"]),
        ("pres_hpa", [r"press", r"baro", r"hpa", r"mbar"]),
        ("wspd_ms", [r"wind[_\s-]*speed", r"wspd", r"wind[_\s-]*sp"]),
        ("wdir_deg", [r"wind[_\s-]*dir", r"wdir", r"dir"]),
        ("gust_ms", [r"gust", r"wind[_\s-]*gust"]),
        ("rain_mm", [r"rain", r"precip", r"rainfall", r"rr"]),
        ("solar_wm2", [r"solar", r"irradiance", r"radiation", r"w/?m2"]),
        ("uv_index", [r"uv"]) ,
    ]

    def detect(self, df: pd.DataFrame) -> Dict:
        cols = list(df.columns)
        lower_map = {c: c.lower() for c in cols}

        # Timestamp detection with scoring
        ts_col = None
        best_ts_score = -1.0
        for c in cols:
            lc = lower_map[c]
            name_hint = 0.4 if any(re.match(p, lc) for p in self.TIME_CANDIDATES) or ("time" in lc or "date" in lc) else 0.0
            try:
                dt = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                continue
            parse_frac = float(dt.notna().mean())
            mono_bonus = 0.2 if dt.is_monotonic_increasing or dt.is_monotonic else 0.0
            score = name_hint + 0.6 * parse_frac + mono_bonus
            if score > best_ts_score:
                best_ts_score = score
                ts_col = c

        guesses: List[FieldGuess] = []
        for canonical, patterns in self.FIELD_PATTERNS:
            best: Optional[FieldGuess] = None
            for c in cols:
                if c == ts_col:
                    continue
                lc = lower_map[c]
                name_score = 0.0
                if any(re.search(p, lc) for p in patterns):
                    name_score = 0.4
                hinted_unit = parse_unit_hint(c)
                unit_candidates, to_canonical = self._unit_candidates_for(canonical)
                chosen_unit, plaus = self._best_unit_and_plausibility(canonical, df[c], hinted_unit, unit_candidates, to_canonical)
                unit_bonus = 0.1 if hinted_unit else 0.0
                conf = name_score + unit_bonus + (0.6 * plaus)
                if name_score >= 0.4 and plaus >= 0.8:
                    conf += 0.1
                candidate = FieldGuess(canonical, c, chosen_unit, conf)
                if best is None or candidate.confidence > best.confidence:
                    best = candidate
            if best is not None:
                guesses.append(best)

        mapping = {
            "version": 1,
            "ts": {"col": ts_col},
            "fields": {},
        }
        for g in guesses:
            mapping["fields"][g.canonical] = {
                "col": g.source_col,
                "unit": g.unit,
                "confidence": round(g.confidence, 2),
            }
        return mapping

    def detect_from_csv(self, path: str, nrows: int = 1000) -> Dict:
        df = pd.read_csv(path, nrows=nrows)
        return self.detect(df)

    def _unit_candidates_for(self, canonical: str):
        if canonical == "temp_c":
            return ["C", "F"], {
                "C": identity,
                "F": fahrenheit_to_c,
            }
        if canonical in ("wspd_ms", "gust_ms"):
            return ["m/s", "km/h", "mph"], {
                "m/s": identity,
                "km/h": kmh_to_ms,
                "mph": mph_to_ms,
            }
        if canonical == "pres_hpa":
            return ["hpa", "mbar", "pa"], {
                "hpa": identity,
                "mbar": mbar_to_hpa,
                "pa": pa_to_hpa,
            }
        if canonical == "rain_mm":
            return ["mm", "inch"], {
                "mm": identity,
                "inch": lambda x: x * 25.4,
            }
        return [None], {None: identity}

    def _best_unit_and_plausibility(
        self,
        canonical: str,
        series: pd.Series,
        hinted_unit: Optional[str],
        unit_candidates: List[Optional[str]],
        to_canonical: Dict,
    ) -> Tuple[Optional[str], float]:
        try:
            vals = pd.to_numeric(series, errors="coerce")
        except Exception:
            return hinted_unit, 0.0
        vals = vals.dropna()
        if vals.empty:
            return hinted_unit, 0.0

        lo, hi = PLAUSIBLE_BOUNDS.get(canonical, (-float("inf"), float("inf")))

        def plaus_for_unit(u):
            conv = to_canonical.get(u, identity)
            try:
                v = conv(vals)
            except Exception:
                return 0.0
            frac = float(((v >= lo) & (v <= hi)).mean())
            return frac

        best_unit = hinted_unit if hinted_unit in unit_candidates else None
        best_plaus = plaus_for_unit(best_unit) if best_unit is not None else -1.0
        for u in unit_candidates:
            p = plaus_for_unit(u)
            if p > best_plaus:
                best_plaus = p
                best_unit = u
        best_plaus = max(0.0, min(1.0, best_plaus))
        return best_unit, best_plaus


