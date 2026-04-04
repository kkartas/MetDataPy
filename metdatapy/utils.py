import datetime as _dt
from typing import Dict, Optional

import numpy as np
import pandas as pd

CANONICAL_VARS = [
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

CANONICAL_INDEX = "ts_utc"

PLAUSIBLE_BOUNDS = {
    "temp_c": (-40.0, 55.0),
    "rh_pct": (0.0, 100.0),
    "pres_hpa": (870.0, 1085.0),
    "wspd_ms": (0.0, 75.0),
    "wdir_deg": (0.0, 360.0),
    "gust_ms": (0.0, 100.0),
    "rain_mm": (0.0, 1000.0),
    "solar_wm2": (0.0, 1500.0),
    "uv_index": (0.0, 20.0),
}

def ensure_datetime_utc(series: pd.Series, tz_hint: Optional[str] = None) -> pd.DatetimeIndex:
    di = pd.to_datetime(series, errors="coerce", utc=False)
    if di.dt.tz is None:
        if tz_hint:
            di = di.dt.tz_localize(tz_hint).dt.tz_convert("UTC")
        else:
            di = di.dt.tz_localize("UTC")
    else:
        di = di.dt.tz_convert("UTC")
    return pd.DatetimeIndex(di)

def _normalize_freq_alias(freq: Optional[str]) -> Optional[str]:
    """Normalize deprecated pandas frequency aliases."""
    if freq is None:
        return None
    # H -> h, T -> min, S -> s, etc. (pandas 2.2+)
    if freq == "H":
        return "h"
    if freq == "T":
        return "min"
    if freq == "S":
        return "s"
    # e.g. "2H" -> "2h"
    if freq.endswith("H") and freq[:-1].isdigit():
        return freq[:-1] + "h"
    if freq.endswith("T") and freq[:-1].isdigit():
        return freq[:-1] + "min"
    if freq.endswith("S") and freq[:-1].isdigit():
        return freq[:-1] + "s"
    return freq


def infer_frequency(index: pd.DatetimeIndex) -> Optional[str]:
    """Infer frequency from a DatetimeIndex, tolerating gaps.

    First tries ``pd.infer_freq`` (strict). If that fails, falls back to the
    median inter-observation delta and maps it to the closest standard pandas
    offset alias.
    """
    try:
        freq = pd.infer_freq(index)
        if freq is not None:
            return _normalize_freq_alias(freq)
    except Exception:
        pass
    if len(index) < 2:
        return None
    deltas = np.diff(index.view("int64"))
    if len(deltas) == 0:
        return None
    # Use the mode (most common delta) — best for mostly-regular series with
    # occasional gaps.  Fall back to the minimum delta when no clear mode.
    unique, counts = np.unique(deltas, return_counts=True)
    max_count = counts.max()
    if max_count > 1:
        best_ns = int(unique[counts.argmax()])
    else:
        best_ns = int(unique.min())
    td = pd.to_timedelta(best_ns, unit="ns")
    # Map common timedeltas to standard offset aliases
    total_seconds = td.total_seconds()
    if total_seconds <= 0:
        return None
    _SECOND_MAP = {
        60: "min",
        300: "5min",
        600: "10min",
        900: "15min",
        1800: "30min",
        3600: "h",
        7200: "2h",
        10800: "3h",
        21600: "6h",
        43200: "12h",
        86400: "D",
    }
    rounded = round(total_seconds)
    if rounded in _SECOND_MAP:
        return _SECOND_MAP[rounded]
    # For non-standard intervals, return a seconds-based offset
    return f"{rounded}s"

def now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc).isoformat()


