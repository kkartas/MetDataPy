from typing import Dict, Iterable, Optional
import numpy as np
import pandas as pd

from .utils import PLAUSIBLE_BOUNDS


def qc_range(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag values outside climatologically plausible ranges.
    
    Performs range checking against meteorologically reasonable bounds for each
    canonical variable. Values outside these bounds are flagged as suspicious.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with meteorological variables
    
    Returns
    -------
    pd.DataFrame
        Input DataFrame with added `qc_{var}_range` boolean columns where
        True indicates values outside plausible bounds
    
    Notes
    -----
    Plausible bounds are defined in utils.PLAUSIBLE_BOUNDS:
    - temp_c: -40°C to 55°C
    - rh_pct: 0% to 100%
    - pres_hpa: 870 hPa to 1085 hPa
    - wspd_ms: 0 m/s to 75 m/s
    - wdir_deg: 0° to 360°
    - And others...
    
    Flags are non-destructive; original data is preserved.
    
    Examples
    --------
    >>> from metdatapy.qc import qc_range
    >>> df = WeatherSet(df).qc_range().to_dataframe()
    >>> flagged = df[df['qc_temp_c_range'] == True]  # Out-of-range temps
    
    See Also
    --------
    qc_spike : Detect sudden spikes using MAD
    qc_flatline : Detect stuck sensors
    qc_consistency : Physical consistency checks
    """
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
    """
    Flag sudden spikes using rolling Median Absolute Deviation (MAD).
    
    Detects anomalous spikes by comparing each value to the local median within
    a rolling window. Uses MAD-based z-scores which are more robust to outliers
    than standard deviation-based methods.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with meteorological variables
    cols : Iterable[str], optional
        Columns to check for spikes. If None, checks all canonical variables
    window : int, default 9
        Size of rolling window for computing local median and MAD
    thresh : float, default 6.0
        MAD-based z-score threshold. Values exceeding this are flagged as spikes
    
    Returns
    -------
    pd.DataFrame
        Input DataFrame with added `qc_{var}_spike` boolean columns where
        True indicates detected spikes
    
    Notes
    -----
    The spike detection algorithm:
    
    1. Computes rolling median over window
    2. Computes Median Absolute Deviation (MAD)
    3. Calculates robust z-score: z = |x - median| / (1.4826 × MAD + ε)
    4. Flags values where z > thresh
    
    The factor 1.4826 makes MAD comparable to standard deviation for normal
    distributions, while being much more robust to outliers [1]_.
    
    References
    ----------
    .. [1] Leys, C., et al. (2013). Detecting outliers: Do not use standard
           deviation around the mean, use absolute deviation around the median.
           Journal of Experimental Social Psychology, 49(4), 764-766.
    
    Examples
    --------
    >>> from metdatapy.qc import qc_spike
    >>> df = qc_spike(df, window=9, thresh=6.0)
    >>> spikes = df[df['qc_temp_c_spike'] == True]
    
    See Also
    --------
    qc_range : Range-based quality control
    qc_flatline : Detect stuck sensors
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
    """
    Flag flatlines indicating stuck or frozen sensors.
    
    Detects periods where sensor readings show suspiciously low variability,
    suggesting sensor malfunction. Uses rolling variance to identify periods
    of constant or near-constant values.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with meteorological variables
    cols : Iterable[str], optional
        Columns to check for flatlines. If None, checks all canonical variables
    window : int, default 5
        Size of rolling window for computing local variance
    tol : float, default 0.0
        Variance tolerance. Values with variance ≤ tol are flagged as flatlines
    
    Returns
    -------
    pd.DataFrame
        Input DataFrame with added `qc_{var}_flatline` boolean columns where
        True indicates detected flatlines (stuck sensors)
    
    Notes
    -----
    - A value of tol=0.0 flags only perfectly constant sequences
    - Increase tol (e.g., 1e-6) to catch near-constant values
    - Useful for detecting sensor failures, communication errors, or frozen readings
    
    Examples
    --------
    >>> from metdatapy.qc import qc_flatline
    >>> # Flag perfect flatlines
    >>> df = qc_flatline(df, window=5, tol=0.0)
    >>> 
    >>> # Flag near-constant values
    >>> df = qc_flatline(df, window=5, tol=1e-6)
    >>> stuck_sensors = df[df['qc_temp_c_flatline'] == True]
    
    See Also
    --------
    qc_range : Range-based quality control
    qc_spike : Detect sudden spikes
    """
    target_cols = list(cols) if cols is not None else [c for c in df.columns if c in PLAUSIBLE_BOUNDS]
    for col in target_cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        var = s.rolling(window, center=True, min_periods=3).var()
        df[f"qc_{col}_flatline"] = var.fillna(0.0) <= tol
    return df


def qc_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag violations of physical consistency relationships between variables.
    
    Performs cross-variable checks based on physical laws and meteorological
    relationships. Violations indicate sensor errors, calibration issues, or
    data corruption.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with meteorological variables (may include derived metrics)
    
    Returns
    -------
    pd.DataFrame
        Input DataFrame with added `qc_consistency` boolean column where
        True indicates violation of physical constraints
    
    Notes
    -----
    Physical consistency checks performed:
    
    1. **Dew point vs temperature**: dew_point_c ≤ temp_c
       (air cannot be supersaturated under normal conditions)
    
    2. **Wind chill vs temperature**: wind_chill_c ≤ temp_c
       (wind chill cannot make it feel warmer)
    
    3. **Heat index vs temperature**: heat_index_c ≥ temp_c
       (humidity cannot make it feel cooler)
    
    4. **Wind direction when calm**: wdir_deg should be undefined (NA) when
       wspd_ms ≤ 0.2 m/s (calm conditions)
    
    Only checks are applied for variables present in the DataFrame.
    
    Examples
    --------
    >>> from metdatapy.qc import qc_consistency
    >>> df = qc_consistency(df)
    >>> inconsistent = df[df['qc_consistency'] == True]
    
    See Also
    --------
    qc_range : Range-based quality control
    qc_any : Aggregate all QC flags
    """
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
    """
    Create aggregate QC flag indicating if ANY quality check failed.
    
    Combines all individual `qc_*` flags into a single `qc_any` column for
    easy filtering of data with any quality issues.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with one or more `qc_*` flag columns
    
    Returns
    -------
    pd.DataFrame
        Input DataFrame with added `qc_any` boolean column where
        True indicates at least one QC check failed for that row
    
    Notes
    -----
    - Combines ALL columns starting with 'qc_' using logical OR
    - Useful for quickly identifying problematic rows
    - If no qc_* columns exist, qc_any is set to False for all rows
    
    Examples
    --------
    >>> from metdatapy.qc import qc_range, qc_spike, qc_any
    >>> df = qc_range(df)
    >>> df = qc_spike(df)
    >>> df = qc_any(df)
    >>> 
    >>> # Filter to only good data
    >>> clean_data = df[df['qc_any'] == False]
    >>> 
    >>> # Count total flagged rows
    >>> n_flagged = df['qc_any'].sum()
    
    See Also
    --------
    qc_range : Range-based quality control
    qc_spike : Spike detection
    qc_flatline : Flatline detection
    qc_consistency : Physical consistency checks
    """
    qc_cols = [c for c in df.columns if c.startswith("qc_")]
    if qc_cols:
        df["qc_any"] = df[qc_cols].fillna(False).any(axis=1)
    else:
        df["qc_any"] = False
    return df



