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
    """
    Create a supervised learning table with lagged features and target horizons.
    
    Transforms a time-series DataFrame into a supervised learning format by adding
    lagged features (past observations) and target variables (future values). This
    is essential for training forecasting models while maintaining temporal order.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with time-series data (must have datetime index)
    targets : Iterable[str]
        Column names to use as forecast targets (will create future shifted versions)
    horizons : Iterable[int], default (1,)
        Forecast horizons in time steps. For each horizon h, creates `{target}_t+{h}`
        columns containing future values
    lags : Iterable[int], default (1, 2, 3)
        Number of time steps to lag. For each lag n and numeric column c, creates
        `{c}_lag{n}` columns containing past values
    drop_na : bool, default True
        If True, drops rows with NaN values introduced by shifting
    
    Returns
    -------
    pd.DataFrame
        Supervised learning table with original columns, lag features, and targets
    
    Notes
    -----
    - All numeric columns receive lag features, not just the target columns
    - Target columns are shifted backward (negative shift) to create future values
    - The resulting DataFrame has fewer rows than input if drop_na=True
    - Time-safe splitting should be applied AFTER creating supervised table
    
    Examples
    --------
    >>> import pandas as pd
    >>> from metdatapy.mlprep import make_supervised
    >>> 
    >>> df = pd.DataFrame({
    ...     'temp_c': [20, 21, 22, 23, 24],
    ...     'rh_pct': [50, 55, 60, 65, 70]
    ... }, index=pd.date_range('2024-01-01', periods=5, freq='1h'))
    >>> 
    >>> # Create supervised table with 1-step ahead forecast
    >>> sup = make_supervised(df, targets=['temp_c'], lags=[1, 2], horizons=[1])
    >>> # Result has columns: temp_c, rh_pct, temp_c_lag1, rh_pct_lag1, 
    >>> #                      temp_c_lag2, rh_pct_lag2, temp_c_t+1
    
    See Also
    --------
    time_split : Time-safe train/val/test splitting
    fit_scaler : Fit scaling parameters for normalization
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
    """
    Split time-series data into train/val/test sets using temporal boundaries.
    
    Performs time-safe data splitting that prevents temporal leakage by ensuring
    strict chronological ordering: all training data comes before validation data,
    which comes before test data. This is critical for realistic evaluation of
    forecasting models.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with datetime index (must be sorted chronologically)
    train_end : pd.Timestamp
        Last timestamp to include in training set (inclusive)
    val_end : pd.Timestamp, optional
        Last timestamp to include in validation set (inclusive).
        If None, performs two-way split (train/test only)
    
    Returns
    -------
    dict of str to pd.DataFrame
        Dictionary with keys 'train', 'val', 'test' containing the split DataFrames.
        If val_end is None, 'val' will be an empty DataFrame
    
    Notes
    -----
    - Input DataFrame MUST have a sorted datetime index
    - All splits are mutually exclusive (no overlap)
    - Train set: index <= train_end
    - Val set: train_end < index <= val_end (empty if val_end is None)
    - Test set: index > val_end (or index > train_end if val_end is None)
    
    Examples
    --------
    >>> import pandas as pd
    >>> from metdatapy.mlprep import time_split
    >>> 
    >>> df = pd.DataFrame({
    ...     'value': range(100)
    ... }, index=pd.date_range('2024-01-01', periods=100, freq='1h'))
    >>> 
    >>> # Three-way split
    >>> splits = time_split(df, 
    ...                     train_end=pd.Timestamp('2024-01-03'),
    ...                     val_end=pd.Timestamp('2024-01-04'))
    >>> print(len(splits['train']), len(splits['val']), len(splits['test']))
    48 24 28
    >>> 
    >>> # Two-way split (no validation set)
    >>> splits = time_split(df, train_end=pd.Timestamp('2024-01-03'))
    >>> print(len(splits['train']), len(splits['test']))
    48 52
    
    See Also
    --------
    make_supervised : Create supervised learning tables with lags
    fit_scaler : Fit scaling on training data
    """
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
    """
    Fit scaling parameters on training data for normalization.
    
    Computes scaling parameters (mean/std, min/max, or median/IQR) from the input
    DataFrame for later use in normalizing features. This is the 'fit' step in the
    fit-transform pattern.
    
    Parameters
    ----------
    df : pd.DataFrame
        Training data to compute scaling parameters from
    method : {'standard', 'minmax', 'robust'}, default 'standard'
        Scaling method:
        - 'standard': z-score normalization using mean and standard deviation
        - 'minmax': scales to [0, 1] range using min and max
        - 'robust': uses median and IQR, less sensitive to outliers
    columns : List[str], optional
        Columns to scale. If None, scales all numeric columns
    
    Returns
    -------
    ScalerParams
        Dataclass containing method, columns, and parameters dictionary
        with computed statistics for each column
    
    Notes
    -----
    Standard scaling formula: (x - mean) / std
    MinMax scaling formula: (x - min) / (max - min)
    Robust scaling formula: (x - median) / IQR
    
    The scaler should be fit on TRAINING data only, then applied to
    validation and test sets to prevent data leakage.
    
    Examples
    --------
    >>> from metdatapy.mlprep import fit_scaler, apply_scaler
    >>> 
    >>> # Fit scaler on training data
    >>> scaler = fit_scaler(train_df, method='standard')
    >>> 
    >>> # Apply to all splits
    >>> train_scaled = apply_scaler(train_df, scaler)
    >>> val_scaled = apply_scaler(val_df, scaler)
    >>> test_scaled = apply_scaler(test_df, scaler)
    
    See Also
    --------
    apply_scaler : Apply fitted scaler to transform data
    ScalerParams : Dataclass storing scaler parameters
    """
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
    """
    Apply fitted scaler parameters to transform data.
    
    Normalizes DataFrame columns using previously fitted scaling parameters.
    This is the 'transform' step in the fit-transform pattern.
    
    Parameters
    ----------
    df : pd.DataFrame
        Data to transform
    scaler : ScalerParams
        Fitted scaler parameters from fit_scaler()
    
    Returns
    -------
    pd.DataFrame
        Transformed DataFrame with scaled numeric columns
    
    Notes
    -----
    - Only columns present in both df and scaler.columns are transformed
    - Non-numeric columns and columns not in scaler are left unchanged
    - The scaler must be fit on training data and applied to all splits
    
    Examples
    --------
    >>> from metdatapy.mlprep import fit_scaler, apply_scaler
    >>> 
    >>> # Fit scaler on training data
    >>> scaler = fit_scaler(train_df, method='standard')
    >>> 
    >>> # Apply to transform data
    >>> train_scaled = apply_scaler(train_df, scaler)
    >>> val_scaled = apply_scaler(val_df, scaler)
    >>> test_scaled = apply_scaler(test_df, scaler)
    
    See Also
    --------
    fit_scaler : Fit scaling parameters on training data
    ScalerParams : Dataclass storing scaler parameters
    """
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


