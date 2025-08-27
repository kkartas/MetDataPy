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

def infer_frequency(index: pd.DatetimeIndex) -> Optional[str]:
    try:
        return pd.infer_freq(index)
    except Exception:
        pass
    if len(index) < 2:
        return None
    deltas = np.diff(index.view("int64"))
    if len(deltas) == 0:
        return None
    median_ns = np.median(deltas)
    # Fallback to a string representation of the median delta
    return str(pd.to_timedelta(int(median_ns), unit="ns"))

def now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc).isoformat()


