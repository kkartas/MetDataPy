from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from .utils import CANONICAL_INDEX, CANONICAL_VARS, ensure_datetime_utc
from .units import (
    fahrenheit_to_c,
    identity,
    mph_to_ms,
    kmh_to_ms,
    mbar_to_hpa,
    pa_to_hpa,
)
from .qc import qc_range
from .derive import dew_point_c, vpd_kpa


UNIT_CONVERTERS = {
    "temp_c": {"F": fahrenheit_to_c, "C": identity},
    "wspd_ms": {"mph": mph_to_ms, "km/h": kmh_to_ms, "m/s": identity},
    "gust_ms": {"mph": mph_to_ms, "km/h": kmh_to_ms, "m/s": identity},
    "pres_hpa": {"mbar": mbar_to_hpa, "hpa": identity, "pa": pa_to_hpa},
    "rain_mm": {"mm": identity, "inch": lambda x: x * 25.4},
}


class WeatherSet:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @classmethod
    def from_csv(cls, path: str, mapping: Dict) -> "WeatherSet":
        df = pd.read_csv(path)
        return cls.from_mapping(df, mapping)

    @classmethod
    def from_mapping(cls, df: pd.DataFrame, mapping: Dict) -> "WeatherSet":
        ts_col = mapping.get("ts", {}).get("col")
        if ts_col is None or ts_col not in df.columns:
            raise ValueError("Timestamp column not found in mapping or data")
        idx = ensure_datetime_utc(df[ts_col])
        df = df.copy()
        df.index = idx
        df.index.name = CANONICAL_INDEX

        out = pd.DataFrame(index=df.index)
        fields = mapping.get("fields", {})
        for canon, cfg in fields.items():
            if canon not in CANONICAL_VARS:
                continue
            src = cfg.get("col")
            if src not in df.columns:
                continue
            out[canon] = df[src]
        return cls(out)

    def to_utc(self) -> "WeatherSet":
        if self.df.index.tz is None:
            self.df.index = self.df.index.tz_localize("UTC")
        else:
            self.df.index = self.df.index.tz_convert("UTC")
        return self

    def normalize_units(self, mapping: Dict) -> "WeatherSet":
        fields = mapping.get("fields", {})
        for var, cfg in fields.items():
            if var not in self.df.columns:
                continue
            unit = (cfg or {}).get("unit")
            if unit is None:
                continue
            convs = UNIT_CONVERTERS.get(var)
            if not convs:
                continue
            func = convs.get(unit)
            if func is None:
                continue
            self.df[var] = func(self.df[var].astype(float))
        return self

    def insert_missing(self, frequency: Optional[str] = None) -> "WeatherSet":
        freq = frequency or pd.infer_freq(self.df.index)
        if freq is None:
            return self
        full = pd.date_range(self.df.index.min(), self.df.index.max(), freq=freq, tz="UTC")
        before = self.df.index
        self.df = self.df.reindex(full)
        self.df.index.name = CANONICAL_INDEX
        # Mark gaps: True where index not in original
        gap_mask = ~self.df.index.isin(before)
        if "gap" in self.df.columns:
            self.df["gap"] = self.df["gap"].fillna(gap_mask)
        else:
            self.df["gap"] = gap_mask
        return self

    def fix_accum_rain(self) -> "WeatherSet":
        if "rain_mm" not in self.df.columns:
            return self
        s = self.df["rain_mm"].astype(float)
        ds = s.diff()
        # If negative diff, assume counter reset: use current value as new accumulation for that step
        reset_idx = ds[ds < 0].index
        ds.loc[reset_idx] = s.loc[reset_idx]
        # Negative tiny noise -> clamp to 0
        ds = ds.clip(lower=0.0)
        self.df["rain_mm"] = ds.fillna(0.0)
        return self

    def resample(self, rule: str, agg: Optional[dict] = None) -> "WeatherSet":
        agg = agg or {
            "temp_c": "mean",
            "rh_pct": "mean",
            "pres_hpa": "mean",
            "wspd_ms": "mean",
            "wdir_deg": "mean",
            "gust_ms": "max",
            "rain_mm": "sum",
            "solar_wm2": "mean",
            "uv_index": "max",
        }
        grouped = self.df.resample(rule)
        out = grouped.agg(agg)
        # Propagate gap as True if any gap in period
        if "gap" in self.df.columns:
            out["gap"] = grouped["gap"].max()
        # Propagate qc_* flags as any over window
        for col in self.df.columns:
            if isinstance(col, str) and col.startswith("qc_"):
                try:
                    out[col] = grouped[col].max()
                except Exception:
                    pass
        self.df = out
        self.df.index = self.df.index.tz_convert("UTC") if self.df.index.tz is not None else self.df.index.tz_localize("UTC")
        self.df.index.name = CANONICAL_INDEX
        return self

    def calendar_features(self, cyclical: bool = True) -> "WeatherSet":
        idx = self.df.index.tz_convert("UTC") if self.df.index.tz is not None else self.df.index.tz_localize("UTC")
        self.df["hour"] = idx.hour
        self.df["weekday"] = idx.weekday
        self.df["month"] = idx.month
        if cyclical:
            import numpy as np
            self.df["hour_sin"] = np.sin(2 * np.pi * self.df["hour"] / 24.0)
            self.df["hour_cos"] = np.cos(2 * np.pi * self.df["hour"] / 24.0)
            self.df["doy"] = idx.dayofyear
            self.df["doy_sin"] = np.sin(2 * np.pi * self.df["doy"] / 365.25)
            self.df["doy_cos"] = np.cos(2 * np.pi * self.df["doy"] / 365.25)
        return self

    def add_exogenous(self, exo: pd.DataFrame, how: str = "left") -> "WeatherSet":
        # exo should have time index in UTC or tz-aware
        if exo.index.tz is None:
            exo.index = exo.index.tz_localize("UTC")
        else:
            exo.index = exo.index.tz_convert("UTC")
        self.df = self.df.join(exo, how=how)
        return self

    def qc_range(self) -> "WeatherSet":
        self.df = qc_range(self.df)
        return self

    def qc_spike(self) -> "WeatherSet":
        from .qc import qc_spike
        self.df = qc_spike(self.df)
        return self

    def qc_flatline(self) -> "WeatherSet":
        from .qc import qc_flatline
        self.df = qc_flatline(self.df)
        return self

    def qc_consistency(self) -> "WeatherSet":
        from .qc import qc_consistency, qc_any
        self.df = qc_consistency(self.df)
        self.df = qc_any(self.df)
        return self

    def to_dataframe(self) -> pd.DataFrame:
        return self.df

    def derive(self, metrics: list[str]) -> "WeatherSet":
        if "dew_point" in metrics and {"temp_c", "rh_pct"}.issubset(self.df.columns):
            self.df["dew_point_c"] = dew_point_c(self.df["temp_c"], self.df["rh_pct"]).astype(float)
        if "vpd" in metrics and {"temp_c", "rh_pct"}.issubset(self.df.columns):
            self.df["vpd_kpa"] = vpd_kpa(self.df["temp_c"], self.df["rh_pct"]).astype(float)
        if "heat_index" in metrics and {"temp_c", "rh_pct"}.issubset(self.df.columns):
            from .derive import heat_index_c
            self.df["heat_index_c"] = heat_index_c(self.df["temp_c"], self.df["rh_pct"]).astype(float)
        if "wind_chill" in metrics and {"temp_c", "wspd_ms"}.issubset(self.df.columns):
            from .derive import wind_chill_c
            self.df["wind_chill_c"] = wind_chill_c(self.df["temp_c"], self.df["wspd_ms"]).astype(float)
        return self


