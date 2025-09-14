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


def heat_index_c(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    """Heat index (Rothfusz regression) returning °C.

    Formula expects T in °F and RH in percent. We convert to/from °C.
    Valid mainly for T_f >= 80 and RH >= 40; outside, use Steadman simple approximation.
    """
    t_c = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=0.0, upper=100.0)
    t_f = t_c * 9.0 / 5.0 + 32.0
    # Rothfusz
    c1 = -42.379
    c2 = 2.04901523
    c3 = 10.14333127
    c4 = -0.22475541
    c5 = -6.83783e-3
    c6 = -5.481717e-2
    c7 = 1.22874e-3
    c8 = 8.5282e-4
    c9 = -1.99e-6
    hi_f = (
        c1
        + c2 * t_f
        + c3 * rh
        + c4 * t_f * rh
        + c5 * (t_f ** 2)
        + c6 * (rh ** 2)
        + c7 * (t_f ** 2) * rh
        + c8 * t_f * (rh ** 2)
        + c9 * (t_f ** 2) * (rh ** 2)
    )
    # Simple adjustment outside traditional domain: use Steadman approximation
    simple_hi_f = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))
    use_simple = (t_f < 80.0) | (rh < 40.0)
    hi_f = hi_f.where(~use_simple, simple_hi_f)
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return pd.Series(hi_c, index=t_c.index if isinstance(t_c, pd.Series) else None)


def wind_chill_c(temp_c: pd.Series | np.ndarray, wspd_ms: pd.Series | np.ndarray) -> pd.Series:
    """Wind chill in °C using Canadian/Australian formula.

    WCI = 13.12 + 0.6215 T - 11.37 v^0.16 + 0.3965 T v^0.16, with T in °C, v in km/h.
    """
    t = pd.Series(temp_c, dtype="float64")
    v_ms = pd.Series(wspd_ms, dtype="float64").clip(lower=0.0)
    v_kmh = v_ms * 3.6
    wci = 13.12 + 0.6215 * t - 11.37 * (v_kmh ** 0.16) + 0.3965 * t * (v_kmh ** 0.16)
    return pd.Series(wci, index=t.index if isinstance(t, pd.Series) else None)


