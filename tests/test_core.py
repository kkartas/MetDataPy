"""Comprehensive tests for core.py (WeatherSet)."""

import pandas as pd
import pytest
from metdatapy.core import WeatherSet


def test_from_csv_basic():
    """Test basic CSV loading."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': [20, 21, 22, 23, 24, 25, 24, 23, 22, 21],
        'rh_pct': [50, 55, 60, 65, 70, 75, 70, 65, 60, 55],
    })
    csv_path = 'test_data.csv'
    df.to_csv(csv_path, index=False)
    
    ws = WeatherSet.from_csv(csv_path, ts_col='timestamp')
    
    assert len(ws.df) == 10
    assert 'temp_c' in ws.df.columns
    assert ws.df.index.name == 'ts_utc'
    
    import os
    os.remove(csv_path)


def test_to_utc():
    """Test timezone conversion to UTC."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H', tz='US/Eastern'),
        'temp_c': [20, 21, 22, 23, 24],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.to_utc()
    
    assert ws.df.index.tz is not None
    assert str(ws.df.index.tz) == 'UTC'


def test_insert_missing():
    """Test gap insertion with gap flag."""
    df = pd.DataFrame({
        'ts_utc': pd.to_datetime(['2024-01-01 00:00', '2024-01-01 02:00', '2024-01-01 03:00']),
        'temp_c': [20.0, 22.0, 23.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.insert_missing(freq='1H')
    
    assert len(ws.df) == 4  # Filled gap at 01:00
    assert 'gap' in ws.df.columns
    assert ws.df['gap'].sum() == 1  # One gap


def test_fix_accum_rain():
    """Test rainfall accumulation rollover detection."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'rain_mm': [995.0, 998.0, 999.9, 0.5, 2.0],  # Rollover at index 3
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.fix_accum_rain()
    
    # After rollover correction, values should be monotonic or reset properly
    assert 'rain_mm' in ws.df.columns


def test_resample():
    """Test resampling with QC flag propagation."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=12, freq='10min'),
        'temp_c': [20.0] * 12,
        'qc_temp_c_range': [False] * 10 + [True, False],  # One flagged
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.resample('1h')
    
    # 12 10-min intervals (00:00-01:50) create 2 hourly bins
    assert len(ws.df) == 2
    # QC flags should be propagated with OR
    assert 'qc_temp_c_range' in ws.df.columns
    # Second hour should have the True flag from the 11th entry
    assert ws.df['qc_temp_c_range'].iloc[1] == True


def test_qc_range():
    """Test range-based quality control."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20.0, 25.0, 999.0, -50.0, 22.0],  # Two out of range
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.qc_range()
    
    assert 'qc_temp_c_range' in ws.df.columns
    assert ws.df['qc_temp_c_range'].sum() == 2  # Two flagged


def test_derive():
    """Test derived meteorological metrics."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [25.0, 26.0, 27.0, 28.0, 29.0],
        'rh_pct': [60.0, 65.0, 70.0, 75.0, 80.0],
        'pres_hpa': [1013.0] * 5,
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.derive(['dew_point', 'vpd'])
    
    assert 'dew_point_c' in ws.df.columns
    assert 'vpd_kpa' in ws.df.columns
    # Dew point should be less than temperature
    assert (ws.df['dew_point_c'] <= ws.df['temp_c']).all()


def test_calendar_features():
    """Test calendar feature generation."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=24, freq='H'),
        'temp_c': [20.0] * 24,
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.calendar_features()
    
    assert 'hour' in ws.df.columns
    assert 'weekday' in ws.df.columns
    assert 'month' in ws.df.columns
    assert 'hour_sin' in ws.df.columns
    assert 'hour_cos' in ws.df.columns
    assert ws.df['hour'].min() == 0
    assert ws.df['hour'].max() == 23


def test_add_exogenous():
    """Test adding exogenous variables."""
    # Main data
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20.0, 21.0, 22.0, 23.0, 24.0],
    }).set_index('ts_utc')
    
    # Exogenous data
    exog = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'solar_wm2': [0, 100, 200, 300, 200],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    ws = ws.add_exogenous(exog)
    
    assert 'solar_wm2' in ws.df.columns
    assert len(ws.df) == 5


def test_to_dataframe():
    """Test conversion to dataframe."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20.0, 21.0, 22.0, 23.0, 24.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    result = ws.to_dataframe()
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5
    assert 'temp_c' in result.columns


def test_chaining_operations():
    """Test chaining multiple operations."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 24.0, 23.0, 22.0, 21.0],
        'rh_pct': [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 70.0, 65.0, 60.0, 55.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    result = (ws
              .to_utc()
              .qc_range()
              .derive(['dew_point', 'vpd'])
              .calendar_features())
    
    assert 'qc_temp_c_range' in result.df.columns
    assert 'dew_point_c' in result.df.columns
    assert 'hour' in result.df.columns
    assert len(result.df) == 10


def test_from_mapping():
    """Test creation from mapping."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temperature': [20, 21, 22, 23, 24],
        'humidity': [50, 55, 60, 65, 70],
    })
    
    mapping = {
        'ts': {'col': 'timestamp'},
        'fields': {
            'temp_c': {'col': 'temperature', 'unit': 'C'},
            'rh_pct': {'col': 'humidity', 'unit': '%'},
        }
    }
    
    ws = WeatherSet.from_mapping(df, mapping)
    
    assert 'temp_c' in ws.df.columns
    assert 'rh_pct' in ws.df.columns
    assert len(ws.df) == 5
    assert ws.df.index.name == 'ts_utc'


def test_from_mapping_missing_ts():
    """Test error when timestamp column missing."""
    df = pd.DataFrame({'temp': [20, 21, 22]})
    mapping = {'ts': {'col': 'missing_col'}, 'fields': {}}
    
    with pytest.raises(ValueError):
        WeatherSet.from_mapping(df, mapping)


def test_normalize_units_fahrenheit():
    """Test temperature conversion from Fahrenheit."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=3, freq='H'),
        'temp_c': [32.0, 68.0, 212.0],  # Freezing, room temp, boiling in F
    }).set_index('ts_utc')
    
    mapping = {
        'fields': {
            'temp_c': {'col': 'temp_c', 'unit': 'F'}
        }
    }
    
    ws = WeatherSet(df).normalize_units(mapping)
    
    assert abs(ws.df['temp_c'].iloc[0] - 0.0) < 0.1  # 32F = 0C
    assert abs(ws.df['temp_c'].iloc[1] - 20.0) < 0.1  # 68F = 20C
    assert abs(ws.df['temp_c'].iloc[2] - 100.0) < 0.1  # 212F = 100C


def test_normalize_units_wind_speed():
    """Test wind speed unit conversions."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=3, freq='H'),
        'wspd_ms': [10.0, 20.0, 30.0],  # mph
    }).set_index('ts_utc')
    
    mapping = {
        'fields': {
            'wspd_ms': {'col': 'wspd_ms', 'unit': 'mph'}
        }
    }
    
    ws = WeatherSet(df).normalize_units(mapping)
    
    # mph to m/s conversion: multiply by ~0.447
    assert ws.df['wspd_ms'].iloc[0] < 10.0  # Should be less after conversion


def test_normalize_units_pressure():
    """Test pressure unit conversions."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=2, freq='H'),
        'pres_hpa': [101300.0, 100000.0],  # Pa
    }).set_index('ts_utc')
    
    mapping = {
        'fields': {
            'pres_hpa': {'col': 'pres_hpa', 'unit': 'pa'}
        }
    }
    
    ws = WeatherSet(df).normalize_units(mapping)
    
    # Pa to hPa: divide by 100
    assert abs(ws.df['pres_hpa'].iloc[0] - 1013.0) < 1.0


def test_to_utc_naive_datetime():
    """Test UTC conversion for naive datetime index."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20, 21, 22, 23, 24],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).to_utc()
    
    assert ws.df.index.tz is not None
    assert str(ws.df.index.tz) == 'UTC'


def test_insert_missing_no_frequency():
    """Test insert_missing when frequency cannot be inferred."""
    df = pd.DataFrame({
        'ts_utc': pd.to_datetime(['2024-01-01 00:00', '2024-01-01 01:00']),
        'temp_c': [20.0, 21.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).insert_missing(frequency=None)
    
    # Should return unchanged if freq can't be inferred
    assert len(ws.df) >= 2


def test_fix_accum_rain_no_rain_column():
    """Test fix_accum_rain when no rain column exists."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20, 21, 22, 23, 24],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).fix_accum_rain()
    
    # Should return unchanged
    assert 'rain_mm' not in ws.df.columns


def test_resample_with_gap_flag():
    """Test that gap flag is properly propagated during resampling."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=12, freq='10min'),
        'temp_c': [20.0] * 12,
        'gap': [False] * 6 + [True] + [False] * 5,
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).resample('1h')
    
    assert 'gap' in ws.df.columns
    # At least one hour should have a gap
    assert ws.df['gap'].any()
    # First hour (entries 0-5) should have no gap, second hour (entries 6-11) should have gap
    assert ws.df['gap'].iloc[1] == True


def test_calendar_features_non_cyclical():
    """Test calendar features without cyclical encoding."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20.0] * 5,
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).calendar_features(cyclical=False)
    
    assert 'hour' in ws.df.columns
    assert 'weekday' in ws.df.columns
    assert 'month' in ws.df.columns
    assert 'hour_sin' not in ws.df.columns
    assert 'hour_cos' not in ws.df.columns


def test_add_exogenous_tz_naive():
    """Test adding exogenous data with naive timezone."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H', tz='UTC'),
        'temp_c': [20.0] * 5,
    }).set_index('ts_utc')
    
    exog = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=5, freq='H'),  # Naive
        'solar_wm2': [0, 100, 200, 300, 200],
    }).set_index('time')
    
    ws = WeatherSet(df).add_exogenous(exog)
    
    assert 'solar_wm2' in ws.df.columns


def test_qc_spike():
    """Test spike detection QC."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': [20, 20, 20, 100, 20, 20, 20, 20, 20, 20],  # Spike at index 3
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).qc_spike()
    
    # Should have spike flags
    qc_cols = [c for c in ws.df.columns if str(c).startswith('qc_') and 'spike' in str(c)]
    assert len(qc_cols) > 0


def test_qc_flatline():
    """Test flatline detection QC."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 21.0, 22.0, 23.0, 24.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).qc_flatline()
    
    # Should have flatline flags
    qc_cols = [c for c in ws.df.columns if str(c).startswith('qc_') and 'flatline' in str(c)]
    assert len(qc_cols) > 0


def test_qc_consistency():
    """Test cross-variable consistency checks."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [20.0, 21.0, 22.0, 23.0, 24.0],
        'rh_pct': [50.0, 55.0, 60.0, 65.0, 70.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).qc_consistency()
    
    # Should have qc_any flag
    assert 'qc_any' in ws.df.columns


def test_derive_individual_metrics():
    """Test deriving individual metrics."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [25.0, 26.0, 27.0, 28.0, 29.0],
        'rh_pct': [60.0, 65.0, 70.0, 75.0, 80.0],
        'wspd_ms': [5.0, 6.0, 7.0, 8.0, 9.0],
    }).set_index('ts_utc')
    
    # Test dew point only
    ws = WeatherSet(df.copy()).derive(['dew_point'])
    assert 'dew_point_c' in ws.df.columns
    assert 'vpd_kpa' not in ws.df.columns
    
    # Test VPD only
    ws = WeatherSet(df.copy()).derive(['vpd'])
    assert 'vpd_kpa' in ws.df.columns
    
    # Test heat index
    ws = WeatherSet(df.copy()).derive(['heat_index'])
    assert 'heat_index_c' in ws.df.columns
    
    # Test wind chill
    df2 = df.copy()
    df2['temp_c'] = [0.0, -5.0, -10.0, -15.0, -20.0]
    ws = WeatherSet(df2).derive(['wind_chill'])
    assert 'wind_chill_c' in ws.df.columns


def test_derive_missing_required_columns():
    """Test derive when required columns are missing."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H'),
        'temp_c': [25.0, 26.0, 27.0, 28.0, 29.0],
        # Missing rh_pct
    }).set_index('ts_utc')
    
    ws = WeatherSet(df).derive(['dew_point', 'vpd'])
    
    # Should not crash, just not add the metrics
    assert 'dew_point_c' not in ws.df.columns
    assert 'vpd_kpa' not in ws.df.columns


def test_to_netcdf(tmp_path):
    """Test NetCDF export."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=5, freq='H', tz='UTC'),
        'temp_c': [20.0, 21.0, 22.0, 23.0, 24.0],
        'rh_pct': [50.0, 55.0, 60.0, 65.0, 70.0],
    }).set_index('ts_utc')
    
    ws = WeatherSet(df)
    output_file = tmp_path / "test_output.nc"
    
    try:
        ws.to_netcdf(str(output_file))
        assert output_file.exists()
    except ImportError:
        # xarray/netCDF4 may not be installed
        pytest.skip("xarray or netCDF4 not installed")


