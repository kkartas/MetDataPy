from typing import Dict, Iterable, Optional
import numpy as np
import pandas as pd

from .utils import PLAUSIBLE_BOUNDS


def qc_range(df: pd.DataFrame) -> pd.DataFrame:
    for var, (lo, hi) in PLAUSIBLE_BOUNDS.items():
        if var in df.columns:
            flag_col = f"qc_{var}_range"
            vals = df[var]
            df[flag_col] = (vals < lo) | (vals > hi)
    return df


def qc_spike(
    df: pd.DataFrame,
    cols: Optional[Iterable[str]] = None,
    window: int = 9,
    thresh: float = 6.0,
) -> pd.DataFrame:
    """Flag spikes using rolling MAD-based z-score.

    z = |x - median| / (1.4826*MAD + eps) > thresh => spike
    """
    eps = 1e-9
    target_cols = list(cols) if cols is not None else [c for c in df.columns if c in PLAUSIBLE_BOUNDS]
    for col in target_cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        med = s.rolling(window, center=True, min_periods=3).median()
        mad = (s - med).abs().rolling(window, center=True, min_periods=3).median()
        z = (s - med).abs() / (1.4826 * mad + eps)
        df[f"qc_{col}_spike"] = z > thresh
    return df


def qc_flatline(
    df: pd.DataFrame,
    cols: Optional[Iterable[str]] = None,
    window: int = 5,
    tol: float = 0.0,
) -> pd.DataFrame:
    """Flag flatlines where rolling variance <= tol."""
    target_cols = list(cols) if cols is not None else [c for c in df.columns if c in PLAUSIBLE_BOUNDS]
    for col in target_cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        var = s.rolling(window, center=True, min_periods=3).var()
        df[f"qc_{col}_flatline"] = var.fillna(0.0) <= tol
    return df


def qc_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Physics-based checks aggregated to qc_consistency."""
    violations = []
    # dew_point <= temp
    if {"dew_point_c", "temp_c"}.issubset(df.columns):
        v = (df["dew_point_c"] > df["temp_c"]) & df["dew_point_c"].notna() & df["temp_c"].notna()
        violations.append(v)
    # wind_chill <= temp, heat_index >= temp when present
    if {"wind_chill_c", "temp_c"}.issubset(df.columns):
        v = (df["wind_chill_c"] > df["temp_c"]) & df["wind_chill_c"].notna() & df["temp_c"].notna()
        violations.append(v)
    if {"heat_index_c", "temp_c"}.issubset(df.columns):
        v = (df["heat_index_c"] < df["temp_c"]) & df["heat_index_c"].notna() & df["temp_c"].notna()
        violations.append(v)
    # wdir should be NA when wind is calm
    if {"wspd_ms", "wdir_deg"}.issubset(df.columns):
        calm = pd.to_numeric(df["wspd_ms"], errors="coerce").fillna(0.0) <= 0.2
        bad_dir = df["wdir_deg"].notna()
        violations.append(calm & bad_dir)
    if violations:
        total = violations[0].copy()
        for v in violations[1:]:
            total = total | v
        df["qc_consistency"] = total
    else:
        df["qc_consistency"] = False
    return df


def qc_any(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate any qc_* columns to qc_any."""
    qc_cols = [c for c in df.columns if c.startswith("qc_")]
    if qc_cols:
        df["qc_any"] = df[qc_cols].fillna(False).any(axis=1)
    else:
        df["qc_any"] = False
    return df



