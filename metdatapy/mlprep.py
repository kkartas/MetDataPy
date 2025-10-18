from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


def make_supervised(
    df: pd.DataFrame,
    targets: Iterable[str],
    horizons: Iterable[int] = (1,),
    lags: Iterable[int] = (1, 2, 3),
    drop_na: bool = True,
) -> pd.DataFrame:
    """Create a supervised learning table with lagged features and target horizons.

    - Adds columns like `{col}_lag{n}` for each numeric column and lag n.
    - Adds target columns like `{tgt}_t+{h}` as future values shifted by -h.
    """
    out = df.copy()
    numeric_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    # Lags
    for n in lags:
        for col in numeric_cols:
            out[f"{col}_lag{n}"] = out[col].shift(n)
    # Targets
    for tgt in targets:
        if tgt not in out.columns:
            continue
        for h in horizons:
            out[f"{tgt}_t+{h}"] = out[tgt].shift(-h)
    if drop_na:
        out = out.dropna()
    return out


def time_split(
    df: pd.DataFrame, train_end: pd.Timestamp, val_end: Optional[pd.Timestamp] = None
) -> Dict[str, pd.DataFrame]:
    """Split by time boundaries (leakage-safe). If val_end is None, uses two-way split."""
    idx = df.index
    train = df.loc[idx <= train_end]
    if val_end is None:
        val = pd.DataFrame(index=pd.DatetimeIndex([], tz=idx.tz))
        test = df.loc[idx > train_end]
    else:
        val = df.loc[(idx > train_end) & (idx <= val_end)]
        test = df.loc[idx > val_end]
    return {"train": train, "val": val, "test": test}


@dataclass
class ScalerParams:
    method: str
    columns: List[str]
    parameters: Dict[str, Dict[str, float]]  # col -> {mean/min/median, scale/iqr, ...}


def fit_scaler(df: pd.DataFrame, method: str = "standard", columns: Optional[List[str]] = None) -> ScalerParams:
    cols = columns or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    params: Dict[str, Dict[str, float]] = {}
    if method == "standard":
        for c in cols:
            mu = float(df[c].mean())
            sigma = float(df[c].std(ddof=0)) or 1.0
            params[c] = {"mean": mu, "scale": sigma}
    elif method == "minmax":
        for c in cols:
            vmin = float(df[c].min())
            vmax = float(df[c].max())
            scale = (vmax - vmin) or 1.0
            params[c] = {"min": vmin, "scale": scale}
    elif method == "robust":
        for c in cols:
            med = float(df[c].median())
            q1 = float(df[c].quantile(0.25))
            q3 = float(df[c].quantile(0.75))
            iqr = (q3 - q1) or 1.0
            params[c] = {"median": med, "iqr": iqr}
    else:
        raise ValueError(f"Unknown scaling method: {method}")
    return ScalerParams(method=method, columns=cols, parameters=params)


def apply_scaler(df: pd.DataFrame, scaler: ScalerParams) -> pd.DataFrame:
    out = df.copy()
    if scaler.method == "standard":
        for c in scaler.columns:
            if c in out.columns and c in scaler.parameters:
                params = scaler.parameters[c]
                out[c] = (out[c] - params["mean"]) / params["scale"]
    elif scaler.method == "minmax":
        for c in scaler.columns:
            if c in out.columns and c in scaler.parameters:
                params = scaler.parameters[c]
                out[c] = (out[c] - params["min"]) / params["scale"]
    elif scaler.method == "robust":
        for c in scaler.columns:
            if c in out.columns and c in scaler.parameters:
                params = scaler.parameters[c]
                out[c] = (out[c] - params["median"]) / params["iqr"]
    else:
        raise ValueError(f"Unknown scaling method: {scaler.method}")
    return out


