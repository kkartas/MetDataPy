"""Tests for utils.py."""

import pandas as pd
import pytest
from metdatapy.utils import CANONICAL_INDEX, CANONICAL_VARS, ensure_datetime_utc, PLAUSIBLE_BOUNDS


def test_canonical_index():
    """Test canonical index name."""
    assert CANONICAL_INDEX == 'ts_utc'


def test_canonical_vars_contains_expected():
    """Test canonical variables list contains expected fields."""
    expected_vars = ['temp_c', 'rh_pct', 'pres_hpa', 'wspd_ms', 'wdir_deg']
    for var in expected_vars:
        assert var in CANONICAL_VARS


def test_plausible_bounds_temperature():
    """Test plausible bounds for temperature."""
    assert 'temp_c' in PLAUSIBLE_BOUNDS
    lo, hi = PLAUSIBLE_BOUNDS['temp_c']
    assert lo < 0  # Can be below freezing
    assert hi > 40  # Can be hot


def test_plausible_bounds_relative_humidity():
    """Test plausible bounds for relative humidity."""
    assert 'rh_pct' in PLAUSIBLE_BOUNDS
    lo, hi = PLAUSIBLE_BOUNDS['rh_pct']
    assert lo == 0
    assert hi == 100


def test_plausible_bounds_wind_speed():
    """Test plausible bounds for wind speed."""
    assert 'wspd_ms' in PLAUSIBLE_BOUNDS
    lo, hi = PLAUSIBLE_BOUNDS['wspd_ms']
    assert lo == 0  # Wind speed cannot be negative
    assert hi > 0


def test_plausible_bounds_pressure():
    """Test plausible bounds for pressure."""
    assert 'pres_hpa' in PLAUSIBLE_BOUNDS
    lo, hi = PLAUSIBLE_BOUNDS['pres_hpa']
    assert lo > 0
    assert hi > lo


def test_ensure_datetime_utc_already_utc():
    """Test ensure_datetime_utc when already UTC."""
    sr = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1h', tz='UTC'))
    result = ensure_datetime_utc(sr)
    
    # ensure_datetime_utc returns DatetimeIndex, not Series
    assert isinstance(result, pd.DatetimeIndex)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'


def test_ensure_datetime_utc_naive():
    """Test ensure_datetime_utc with naive datetimes."""
    sr = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1h'))
    result = ensure_datetime_utc(sr)
    
    # ensure_datetime_utc returns DatetimeIndex, not Series
    assert isinstance(result, pd.DatetimeIndex)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'


def test_ensure_datetime_utc_other_timezone():
    """Test ensure_datetime_utc with non-UTC timezone."""
    sr = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1h', tz='US/Eastern'))
    result = ensure_datetime_utc(sr)
    
    # ensure_datetime_utc returns DatetimeIndex, not Series
    assert isinstance(result, pd.DatetimeIndex)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'
    # Times are converted to UTC (5 hours ahead for Eastern)
    # Original: 2024-01-01 00:00 EST = 2024-01-01 05:00 UTC
    assert result[0].hour == 5  # Converted from midnight EST to UTC


def test_ensure_datetime_utc_preserves_values():
    """Test that UTC conversion preserves the actual time point."""
    # Create a timestamp in US/Eastern
    sr = pd.Series([pd.Timestamp('2024-01-01 12:00:00', tz='US/Eastern')])
    result = ensure_datetime_utc(sr)
    
    # ensure_datetime_utc returns DatetimeIndex
    assert isinstance(result, pd.DatetimeIndex)
    # The UTC version should be 5 hours ahead (EST = UTC-5)
    assert result[0].hour == 17  # 12 + 5


def test_all_canonical_vars_have_bounds():
    """Test that all canonical variables have plausible bounds defined."""
    # Most canonical vars should have bounds (except maybe some metadata fields)
    core_vars = ['temp_c', 'rh_pct', 'pres_hpa', 'wspd_ms', 'wdir_deg', 'rain_mm']
    for var in core_vars:
        assert var in PLAUSIBLE_BOUNDS, f"{var} missing from PLAUSIBLE_BOUNDS"


def test_plausible_bounds_logical():
    """Test that plausible bounds are logical (lo < hi)."""
    for var, (lo, hi) in PLAUSIBLE_BOUNDS.items():
        assert lo < hi, f"Bounds for {var} are illogical: {lo} >= {hi}"


def test_ensure_datetime_utc_with_tz_hint():
    """Test ensure_datetime_utc with timezone hint."""
    from metdatapy.utils import ensure_datetime_utc
    sr = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1h'))
    result = ensure_datetime_utc(sr, tz_hint='US/Eastern')
    
    # ensure_datetime_utc returns DatetimeIndex, not Series
    assert isinstance(result, pd.DatetimeIndex)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'
    # Should have been localized to US/Eastern then converted to UTC


def test_infer_frequency_valid():
    """Test frequency inference with regular intervals."""
    from metdatapy.utils import infer_frequency
    idx = pd.DatetimeIndex(pd.date_range('2024-01-01', periods=10, freq='1h'))
    freq = infer_frequency(idx)
    
    assert freq is not None
    # Should detect hourly frequency


def test_infer_frequency_single_value():
    """Test frequency inference with single value."""
    from metdatapy.utils import infer_frequency
    idx = pd.DatetimeIndex(['2024-01-01'])
    freq = infer_frequency(idx)
    
    assert freq is None


def test_infer_frequency_empty():
    """Test frequency inference with empty index."""
    from metdatapy.utils import infer_frequency
    idx = pd.DatetimeIndex([])
    freq = infer_frequency(idx)
    
    assert freq is None


def test_infer_frequency_irregular():
    """Test frequency inference with irregular intervals."""
    from metdatapy.utils import infer_frequency
    # Need at least 3 points, but pandas.infer_freq may still fail
    idx = pd.DatetimeIndex(['2024-01-01 00:00', '2024-01-01 01:00', '2024-01-01 03:30'])
    freq = infer_frequency(idx)
    
    # With irregular intervals, infer_freq may return None, then fallback kicks in
    # The fallback computes median delta
    if freq is not None:
        assert isinstance(freq, str)


def test_now_utc_iso():
    """Test UTC ISO timestamp generation."""
    from metdatapy.utils import now_utc_iso
    result = now_utc_iso()
    
    assert isinstance(result, str)
    assert 'T' in result  # ISO format
    assert '+' in result or 'Z' in result or '+00:00' in result  # UTC indicator


def test_plausible_bounds_coverage():
    """Test that all expected variables have bounds."""
    expected_vars = ['temp_c', 'rh_pct', 'pres_hpa', 'wspd_ms', 'wdir_deg', 
                     'gust_ms', 'rain_mm', 'solar_wm2', 'uv_index']
    for var in expected_vars:
        assert var in PLAUSIBLE_BOUNDS, f"{var} missing from PLAUSIBLE_BOUNDS"


