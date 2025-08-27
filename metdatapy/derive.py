from __future__ import annotations

import numpy as np
import pandas as pd

A = 17.62
B = 243.12


def dew_point_c(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    t = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=1e-6, upper=100.0)
    gamma = np.log(rh / 100.0) + (A * t) / (B + t)
    td = (B * gamma) / (A - gamma)
    return pd.Series(td, index=t.index if isinstance(t, pd.Series) else None)


def saturation_vapor_pressure_kpa(temp_c: pd.Series | np.ndarray) -> pd.Series:
    t = pd.Series(temp_c, dtype="float64")
    es = 0.6108 * np.exp((17.27 * t) / (t + 237.3))
    return pd.Series(es, index=t.index if isinstance(t, pd.Series) else None)


def vpd_kpa(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    t = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=0.0, upper=100.0)
    es = saturation_vapor_pressure_kpa(t)
    ea = es * (rh / 100.0)
    return (es - ea)


