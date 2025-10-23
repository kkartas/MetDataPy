"""Comprehensive tests for mlprep.py."""

import pandas as pd
import pytest
from metdatapy.mlprep import make_supervised, time_split, fit_scaler, apply_scaler, ScalerParams


def test_make_supervised_basic():
    """Test supervised learning table creation with lags."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': list(range(10)),
        'rh_pct': list(range(10, 20)),
    }).set_index('ts_utc')
    
    result = make_supervised(df, targets=['temp_c'], lags=[1, 2], horizons=[1])
    
    assert 'temp_c_lag1' in result.columns
    assert 'temp_c_lag2' in result.columns
    assert 'temp_c_h1' in result.columns
    assert len(result) < len(df)  # Some rows dropped due to lags/horizons


def test_make_supervised_multiple_horizons():
    """Test multiple forecast horizons."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=20, freq='H'),
        'temp_c': list(range(20)),
    }).set_index('ts_utc')
    
    result = make_supervised(df, targets=['temp_c'], lags=[1], horizons=[1, 3, 6])
    
    assert 'temp_c_h1' in result.columns
    assert 'temp_c_h3' in result.columns
    assert 'temp_c_h6' in result.columns


def test_make_supervised_drop_na():
    """Test NA dropping in supervised table."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=10, freq='H'),
        'temp_c': list(range(10)),
    }).set_index('ts_utc')
    
    result_drop = make_supervised(df, targets=['temp_c'], lags=[1], horizons=[1], drop_na=True)
    result_keep = make_supervised(df, targets=['temp_c'], lags=[1], horizons=[1], drop_na=False)
    
    assert len(result_drop) <= len(result_keep)
    assert not result_drop.isna().any().any()  # No NAs when drop_na=True


def test_time_split_basic():
    """Test time-based data splitting."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=100, freq='H'),
        'temp_c': list(range(100)),
    }).set_index('ts_utc')
    
    train_end = pd.Timestamp('2024-01-03')
    val_end = pd.Timestamp('2024-01-04')
    
    splits = time_split(df, train_end=train_end, val_end=val_end)
    
    assert 'train' in splits
    assert 'val' in splits
    assert 'test' in splits
    assert len(splits['train']) + len(splits['val']) + len(splits['test']) == len(df)


def test_time_split_no_val():
    """Test time split without validation set."""
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=100, freq='H'),
        'temp_c': list(range(100)),
    }).set_index('ts_utc')
    
    train_end = pd.Timestamp('2024-01-04')
    
    splits = time_split(df, train_end=train_end, val_end=None)
    
    assert 'train' in splits
    assert 'test' in splits
    assert 'val' not in splits or len(splits['val']) == 0


def test_fit_scaler_standard():
    """Test standard scaler fitting."""
    df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0, 35.0, 40.0],
        'rh_pct': [50.0, 60.0, 70.0, 80.0, 90.0],
    })
    
    scaler = fit_scaler(df, method='standard')
    
    assert scaler.method == 'standard'
    assert 'temp_c' in scaler.columns
    assert 'rh_pct' in scaler.columns
    assert 'temp_c' in scaler.parameters
    assert 'mean' in scaler.parameters['temp_c']
    assert 'scale' in scaler.parameters['temp_c']


def test_fit_scaler_minmax():
    """Test min-max scaler fitting."""
    df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0, 35.0, 40.0],
        'rh_pct': [50.0, 60.0, 70.0, 80.0, 90.0],
    })
    
    scaler = fit_scaler(df, method='minmax')
    
    assert scaler.method == 'minmax'
    assert 'min' in scaler.parameters['temp_c']
    assert 'scale' in scaler.parameters['temp_c']


def test_fit_scaler_robust():
    """Test robust scaler fitting."""
    df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0, 35.0, 40.0, 100.0],  # Outlier
        'rh_pct': [50.0, 60.0, 70.0, 80.0, 90.0, 95.0],
    })
    
    scaler = fit_scaler(df, method='robust')
    
    assert scaler.method == 'robust'
    assert 'median' in scaler.parameters['temp_c']
    assert 'iqr' in scaler.parameters['temp_c']


def test_fit_scaler_selected_columns():
    """Test scaler with selected columns only."""
    df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0],
        'rh_pct': [50.0, 60.0, 70.0],
        'station_id': ['A', 'B', 'C'],  # Non-numeric
    })
    
    scaler = fit_scaler(df, method='standard', columns=['temp_c'])
    
    assert 'temp_c' in scaler.columns
    assert 'rh_pct' not in scaler.columns
    assert len(scaler.columns) == 1


def test_apply_scaler_standard():
    """Test applying standard scaler."""
    train_df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0, 35.0, 40.0],
    })
    
    test_df = pd.DataFrame({
        'temp_c': [22.0, 28.0, 33.0],
    })
    
    scaler = fit_scaler(train_df, method='standard')
    scaled = apply_scaler(test_df, scaler)
    
    assert 'temp_c' in scaled.columns
    assert scaled['temp_c'].mean() != test_df['temp_c'].mean()  # Scaled


def test_apply_scaler_minmax():
    """Test applying min-max scaler."""
    train_df = pd.DataFrame({
        'temp_c': [20.0, 40.0],  # Min=20, Max=40, Range=20
    })
    
    test_df = pd.DataFrame({
        'temp_c': [30.0],  # Should be (30-20)/20 = 0.5
    })
    
    scaler = fit_scaler(train_df, method='minmax')
    scaled = apply_scaler(test_df, scaler)
    
    assert abs(scaled['temp_c'].iloc[0] - 0.5) < 0.01


def test_apply_scaler_robust():
    """Test applying robust scaler."""
    train_df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0, 35.0, 40.0],
    })
    
    test_df = pd.DataFrame({
        'temp_c': [30.0],
    })
    
    scaler = fit_scaler(train_df, method='robust')
    scaled = apply_scaler(test_df, scaler)
    
    assert 'temp_c' in scaled.columns


def test_scaler_params_serialization():
    """Test that ScalerParams can be serialized."""
    df = pd.DataFrame({
        'temp_c': [20.0, 25.0, 30.0],
        'rh_pct': [50.0, 60.0, 70.0],
    })
    
    scaler = fit_scaler(df, method='standard')
    
    # Should be JSON serializable
    import json
    params_dict = {
        'method': scaler.method,
        'columns': scaler.columns,
        'parameters': scaler.parameters,
    }
    
    json_str = json.dumps(params_dict)
    assert isinstance(json_str, str)
    
    # Should be able to reconstruct
    loaded = json.loads(json_str)
    assert loaded['method'] == 'standard'
    assert 'temp_c' in loaded['columns']


def test_end_to_end_ml_pipeline():
    """Test complete ML preparation pipeline."""
    # Create sample data
    df = pd.DataFrame({
        'ts_utc': pd.date_range('2024-01-01', periods=100, freq='H'),
        'temp_c': [20 + i * 0.1 for i in range(100)],
        'rh_pct': [50 + i * 0.2 for i in range(100)],
    }).set_index('ts_utc')
    
    # Create supervised learning table
    supervised = make_supervised(df, targets=['temp_c'], lags=[1, 2, 3], horizons=[1])
    
    # Split data
    train_end = pd.Timestamp('2024-01-03')
    val_end = pd.Timestamp('2024-01-04')
    splits = time_split(supervised, train_end=train_end, val_end=val_end)
    
    # Fit scaler on train
    scaler = fit_scaler(splits['train'], method='standard')
    
    # Apply to all splits
    train_scaled = apply_scaler(splits['train'], scaler)
    val_scaled = apply_scaler(splits['val'], scaler)
    test_scaled = apply_scaler(splits['test'], scaler)
    
    assert len(train_scaled) > 0
    assert len(val_scaled) > 0
    assert len(test_scaled) > 0
    assert 'temp_c_lag1' in train_scaled.columns
    assert 'temp_c_h1' in train_scaled.columns


