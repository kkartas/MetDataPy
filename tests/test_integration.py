"""Integration tests for common workflows."""

import pandas as pd
import pytest
import tempfile
import os
from metdatapy import WeatherSet
from metdatapy.mapper import Mapper, Detector


def test_full_workflow():
    """Test a complete data processing workflow."""
    # Create sample CSV data
    df = pd.DataFrame({
        'datetime': pd.date_range('2024-01-01', periods=50, freq='h'),
        'temperature': [20 + i * 0.1 for i in range(50)],
        'humidity': [50 + i * 0.2 for i in range(50)],
        'pressure': [1013 + i * 0.05 for i in range(50)],
    })
    
    # Save to temp CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f.name, index=False)
        csv_path = f.name
    
    try:
        # Auto-detect column mapping
        detector = Detector()
        mapping = detector.detect(df)
        
        # Load with WeatherSet
        ws = WeatherSet.from_csv(csv_path, mapping)
        
        # Convert to UTC
        ws = ws.to_utc()
        
        # Run QC
        ws = ws.qc_range()
        
        # Add calendar features
        ws = ws.calendar_features()
        
        # Get result
        result = ws.to_dataframe()
        
        # Verify
        assert len(result) == 50
        assert 'hour' in result.columns
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.unlink(csv_path)


def test_weatherset_insert_missing():
    """Test gap filling."""
    # Create data with gaps
    dates = pd.to_datetime(['2024-01-01 00:00', '2024-01-01 02:00', '2024-01-01 03:00'])
    df = pd.DataFrame({
        'temp_c': [20.0, 22.0, 23.0]
    }, index=dates)
    df.index.name = 'ts_utc'
    
    ws = WeatherSet(df)
    ws = ws.insert_missing(frequency='1H')
    
    # Should have 4 rows after filling gap at 01:00
    assert len(ws.df) == 4
    assert 'gap' in ws.df.columns


def test_units_conversion():
    """Test various unit conversions."""
    from metdatapy.units import fahrenheit_to_c, mph_to_ms, kmh_to_ms, mbar_to_hpa, pa_to_hpa, identity
    
    # Temperature
    assert abs(fahrenheit_to_c(32.0) - 0.0) < 0.01
    assert abs(fahrenheit_to_c(212.0) - 100.0) < 0.01
    
    # Wind speed
    assert abs(mph_to_ms(0.0) - 0.0) < 0.01
    assert abs(kmh_to_ms(36.0) - 10.0) < 0.01
    
    # Pressure
    assert abs(mbar_to_hpa(1013.25) - 1013.25) < 0.01
    assert abs(pa_to_hpa(101325.0) - 1013.25) < 0.01
    
    # Identity
    assert identity(42.0) == 42.0


def test_qc_workflow():
    """Test quality control workflow."""
    df = pd.DataFrame({
        'temp_c': [20.0, 21.0, 999.0, 23.0],  # 999.0 is out of range
        'rh_pct': [50.0, 55.0, 60.0, 65.0],
        'pres_hpa': [1013.0, 1013.5, 1014.0, 1014.5],
        'wspd_ms': [5.0, 5.0, 5.0, 5.0],
        'wdir_deg': [180.0, 180.0, 180.0, 0.0],
    }, index=pd.date_range('2024-01-01', periods=4, freq='h'))
    df.index.name = 'ts_utc'
    
    ws = WeatherSet(df)
    ws = ws.to_utc().qc_range()
    
    # Should have flagged the 999.0
    assert 'qc_temp_c_range' in ws.df.columns
    assert ws.df['qc_temp_c_range'].sum() > 0


def test_mapper_template():
    """Test mapping template generation."""
    template = Mapper.template()
    
    assert 'ts' in template
    assert 'fields' in template
    assert isinstance(template['fields'], dict)


def test_derive_workflow():
    """Test deriving meteorological metrics."""
    df = pd.DataFrame({
        'temp_c': [25.0, 26.0, 27.0, 28.0, 29.0],
        'rh_pct': [60.0, 65.0, 70.0, 75.0, 80.0],
    }, index=pd.date_range('2024-01-01', periods=5, freq='h', tz='UTC'))
    df.index.name = 'ts_utc'
    
    ws = WeatherSet(df).derive(['dew_point', 'vpd'])
    
    assert 'dew_point_c' in ws.df.columns
    assert 'vpd_kpa' in ws.df.columns
    # Dew point should be less than temperature
    assert (ws.df['dew_point_c'] <= ws.df['temp_c']).all()
