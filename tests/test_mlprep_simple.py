"""Simple tests for mlprep.py to boost coverage."""

import pandas as pd
import pytest
import json
from metdatapy.mlprep import make_supervised, time_split, fit_scaler, apply_scaler


def test_make_supervised():
    """Test make_supervised function."""
    df = pd.DataFrame({
        'temp': list(range(20)),
        'rh': list(range(20, 40)),
    }, index=pd.date_range('2024-01-01', periods=20, freq='h'))
    
    result = make_supervised(df, targets=['temp'], lags=[1, 2], horizons=[1, 3])
    
    # Should have lag columns
    assert 'temp_lag1' in result.columns
    assert 'temp_lag2' in result.columns
    # Should have target columns
    assert 'temp_t+1' in result.columns
    assert 'temp_t+3' in result.columns


def test_time_split():
    """Test time_split function."""
    df = pd.DataFrame({
        'value': range(100)
    }, index=pd.date_range('2024-01-01', periods=100, freq='h'))
    
    splits = time_split(df, 
                       train_end=pd.Timestamp('2024-01-03'),
                       val_end=pd.Timestamp('2024-01-04'))
    
    assert 'train' in splits
    assert 'val' in splits
    assert 'test' in splits
    assert len(splits['train']) > 0
    assert len(splits['val']) > 0
    assert len(splits['test']) > 0


def test_fit_and_apply_scaler_standard():
    """Test fit and apply scaler with standard method."""
    train = pd.DataFrame({'temp': [20, 25, 30]})
    test = pd.DataFrame({'temp': [22, 28]})
    
    scaler = fit_scaler(train, method='standard')
    scaled = apply_scaler(test, scaler)
    
    assert 'temp' in scaled.columns
    assert scaler.method == 'standard'
    assert 'temp' in scaler.parameters


def test_fit_and_apply_scaler_minmax():
    """Test fit and apply scaler with minmax method."""
    train = pd.DataFrame({'temp': [20, 40]})
    test = pd.DataFrame({'temp': [30]})
    
    scaler = fit_scaler(train, method='minmax')
    scaled = apply_scaler(test, scaler)
    
    # 30 should be 0.5 between 20 and 40
    assert abs(scaled['temp'].iloc[0] - 0.5) < 0.01


def test_fit_and_apply_scaler_robust():
    """Test fit and apply scaler with robust method."""
    train = pd.DataFrame({'temp': [20, 25, 30, 35, 40]})
    test = pd.DataFrame({'temp': [30]})
    
    scaler = fit_scaler(train, method='robust')
    scaled = apply_scaler(test, scaler)
    
    assert 'temp' in scaled.columns
    assert scaler.method == 'robust'


def test_scaler_serialization():
    """Test that scaler parameters are JSON serializable."""
    df = pd.DataFrame({'temp': [20, 25, 30]})
    scaler = fit_scaler(df, method='standard')
    
    # Should be serializable
    params_dict = {
        'method': scaler.method,
        'columns': scaler.columns,
        'parameters': scaler.parameters
    }
    json_str = json.dumps(params_dict)
    loaded = json.loads(json_str)
    
    assert loaded['method'] == 'standard'
    assert 'temp' in loaded['columns']


