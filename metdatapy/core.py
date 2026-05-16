from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd

from .io import read_csv
from .utils import CANONICAL_INDEX, CANONICAL_VARS, ensure_datetime_utc, infer_frequency
from .units import (
    fahrenheit_to_c,
    identity,
    mph_to_ms,
    kmh_to_ms,
    mbar_to_hpa,
    pa_to_hpa,
    inches_to_mm,
)
from .qc import qc_range
from .derive import dew_point_c, vpd_kpa


UNIT_CONVERTERS = {
    "temp_c": {"F": fahrenheit_to_c, "C": identity},
    "wspd_ms": {"mph": mph_to_ms, "km/h": kmh_to_ms, "m/s": identity},
    "gust_ms": {"mph": mph_to_ms, "km/h": kmh_to_ms, "m/s": identity},
    "pres_hpa": {"mbar": mbar_to_hpa, "hpa": identity, "pa": pa_to_hpa},
    "rain_mm": {"mm": identity, "inch": inches_to_mm},
    "rain_rate_mmh": {"mm/h": identity, "inch/h": inches_to_mm},
}


class WeatherSet:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @classmethod
    def from_csv(
        cls,
        path: str,
        mapping: Dict,
        nonexistent: str = "raise",
        ambiguous: str = "raise",
    ) -> "WeatherSet":
        df = read_csv(path)
        return cls.from_mapping(
            df,
            mapping,
            nonexistent=nonexistent,
            ambiguous=ambiguous,
        )

    @classmethod
    def from_mapping(
        cls,
        df: pd.DataFrame,
        mapping: Dict,
        nonexistent: str = "raise",
        ambiguous: str = "raise",
    ) -> "WeatherSet":
        ts_cfg = mapping.get("ts") or {}
        ts_col = ts_cfg.get("col")
        if ts_col is None or ts_col not in df.columns:
            raise ValueError("Timestamp column not found in mapping or data")
        tz_hint = ts_cfg.get("timezone") or None
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*parsing datetimes with mixed time zones.*",
                category=FutureWarning,
            )
            try:
                raw = pd.to_datetime(df[ts_col], errors="coerce", utc=False)
            except ValueError as exc:
                if "mixed timezones detected" not in str(exc).lower():
                    raise
                raw = None
        if raw is None:
            is_tz_aware = True
        else:
            try:
                is_tz_aware = getattr(raw.dt, "tz", None) is not None
            except AttributeError:
                is_tz_aware = True
        if not is_tz_aware and tz_hint is None:
            warnings.warn(
                "Timestamp column is naive and no 'timezone' is set under 'ts' in "
                "the mapping; assuming UTC. Add a 'timezone' key (e.g. 'UTC', "
                "'US/Eastern') under 'ts' to declare the source timezone explicitly.",
                UserWarning,
                stacklevel=2,
            )
        idx = ensure_datetime_utc(
            df[ts_col],
            tz_hint=tz_hint,
            nonexistent=nonexistent,
            ambiguous=ambiguous,
        )
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
        from .utils import _normalize_freq_alias
        freq = frequency if frequency is not None else infer_frequency(self.df.index)
        freq = _normalize_freq_alias(freq)
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
            "rain_rate_mmh": "mean",
            "solar_wm2": "mean",
            "uv_index": "max",
        }
        # Normalize frequency strings to use lowercase (pandas 2.0+ requirement)
        # Replace deprecated uppercase 'H' with lowercase 'h' for hours
        rule = rule.replace('H', 'h')
        # Filter aggregation dict to only include columns that exist
        agg = {k: v for k, v in agg.items() if k in self.df.columns}
        grouped = self.df.resample(rule)
        out = grouped.agg(agg) if agg else pd.DataFrame(index=grouped.groups.keys())
        # Propagate gap as True if any gap in period
        if "gap" in self.df.columns:
            out["gap"] = grouped["gap"].max()
        # Propagate qc_* flags with OR semantics over the resample window
        for col in self.df.columns:
            if isinstance(col, str) and col.startswith("qc_"):
                series = self.df[col]
                if not pd.api.types.is_bool_dtype(series) and not pd.api.types.is_numeric_dtype(series):
                    raise TypeError(
                        f"QC column '{col}' has unsupported dtype {series.dtype}; "
                        "expected bool or numeric"
                    )
                out[col] = grouped[col].apply(lambda g: g.any())
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

    def encode_wind_direction(self, drop_original: bool = False) -> "WeatherSet":
        """Encode wind direction degrees as cyclic sine/cosine features."""
        if "wdir_deg" not in self.df.columns:
            return self
        direction = pd.to_numeric(self.df["wdir_deg"], errors="coerce") % 360.0
        radians = np.deg2rad(direction)
        self.df["wdir_sin"] = np.sin(radians)
        self.df["wdir_cos"] = np.cos(radians)
        if drop_original:
            self.df = self.df.drop(columns=["wdir_deg"])
        return self

    def rolling_features(
        self,
        columns: Iterable[str],
        windows: Iterable[int],
        stats: Sequence[str] = ("mean", "std", "min", "max"),
        closed: str = "left",
    ) -> "WeatherSet":
        """Add rolling time-series features for selected columns.

        The default ``closed="left"`` computes each feature from previous rows
        only, excluding the current observation to avoid target leakage.
        """
        allowed_stats = {"mean", "std", "min", "max"}
        requested_stats = tuple(stats)
        unsupported = [stat for stat in requested_stats if stat not in allowed_stats]
        if unsupported:
            raise ValueError(f"Unsupported rolling stats: {unsupported}")

        for window in windows:
            if not isinstance(window, int) or window < 1:
                raise ValueError("Rolling windows must be positive integers")
            for column in columns:
                if column not in self.df.columns:
                    continue
                series = pd.to_numeric(self.df[column], errors="coerce")
                if closed == "left":
                    rolling = series.shift(1).rolling(window=window, min_periods=1)
                else:
                    rolling = series.rolling(window=window, min_periods=1, closed=closed)
                for stat in requested_stats:
                    out_col = f"{column}_roll{window}_{stat}"
                    self.df[out_col] = getattr(rolling, stat)()
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

    def qc_spike(
        self,
        cols: Optional[Iterable[str]] = None,
        window: int = 9,
        thresh: float = 6.0,
        causal: bool = False,
    ) -> "WeatherSet":
        from .qc import qc_spike
        self.df = qc_spike(self.df, cols=cols, window=window, thresh=thresh, causal=causal)
        return self

    def qc_flatline(
        self,
        cols: Optional[Iterable[str]] = None,
        window: int = 5,
        tol: float = 0.0,
        causal: bool = False,
    ) -> "WeatherSet":
        from .qc import qc_flatline
        self.df = qc_flatline(self.df, cols=cols, window=window, tol=tol, causal=causal)
        return self

    def qc_consistency(self) -> "WeatherSet":
        from .qc import qc_consistency, qc_any
        self.df = qc_consistency(self.df)
        self.df = qc_any(self.df)
        return self

    def to_dataframe(self) -> pd.DataFrame:
        return self.df
    
    def to_netcdf(
        self,
        path: str,
        metadata: Optional[Dict] = None,
        station_metadata: Optional[Dict] = None,
    ) -> None:
        """Export to CF-compliant NetCDF4 file."""
        from .io import to_netcdf
        to_netcdf(self.df, path, metadata, station_metadata)

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
