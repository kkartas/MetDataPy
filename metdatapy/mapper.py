from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml

from .units import parse_unit_hint


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

        ts_col = None
        for c in cols:
            lc = lower_map[c]
            if any(re.match(p, lc) for p in self.TIME_CANDIDATES):
                ts_col = c
                break
        if ts_col is None:
            for c in cols:
                if "time" in lower_map[c] or "date" in lower_map[c]:
                    ts_col = c
                    break

        guesses: List[FieldGuess] = []
        for canonical, patterns in self.FIELD_PATTERNS:
            best: Optional[FieldGuess] = None
            for c in cols:
                lc = lower_map[c]
                name_score = 0.0
                if any(re.search(p, lc) for p in patterns):
                    name_score = 0.8
                if name_score == 0:
                    continue
                unit = parse_unit_hint(c)
                unit_bonus = 0.1 if unit is not None else 0.0
                conf = name_score + unit_bonus
                candidate = FieldGuess(canonical, c, unit, conf)
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


