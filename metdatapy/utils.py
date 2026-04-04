import datetime as _dt
from typing import Dict, Optional

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


def infer_frequency(index: pd.DatetimeIndex) -> Optional[str]:
    """Infer frequency from a DatetimeIndex, tolerating gaps.

    First tries ``pd.infer_freq`` (strict). If that fails, falls back to the
    mode of inter-observation timedeltas and maps it to the closest standard
    pandas offset alias. Uses ``TimedeltaIndex`` arithmetic rather than
    ``view("int64")`` so the result is correct regardless of the index
    resolution (ns, us, s) or pandas version.
    """
    try:
        freq = pd.infer_freq(index)
        if freq is not None:
            return _normalize_freq_alias(freq)
    except Exception:
        pass
    if len(index) < 2:
        return None
    # Compute timedeltas without assuming a specific internal resolution.
    # index[1:] - index[:-1] always returns a TimedeltaIndex.
    deltas = index[1:] - index[:-1]
    if len(deltas) == 0:
        return None
    # Use the mode (most common delta) — best for mostly-regular series with
    # occasional gaps.  Fall back to the minimum when all deltas are unique.
    counts = pd.Series(deltas).value_counts()
    if counts.iloc[0] > 1:
        best_td = counts.index[0]
    else:
        best_td = deltas.min()
    total_seconds = best_td.total_seconds()
    if total_seconds <= 0:
        return None
    rounded = round(total_seconds)
    if rounded in _SECOND_MAP:
        return _SECOND_MAP[rounded]
    return f"{rounded}s"

def now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc).isoformat()


