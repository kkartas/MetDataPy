import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import xarray as xr
from metdatapy.core import WeatherSet
from metdatapy.io import to_netcdf, from_netcdf


def test_netcdf_export_basic():
    """Test basic NetCDF export with CF compliance."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0, 12.0],
        "rh_pct": [50.0, 55.0, 60.0],
        "wspd_ms": [2.0, 3.0, 4.0],
    }, index=pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"], utc=True))
    df.index.name = "ts_utc"
    
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Export to NetCDF
        to_netcdf(df, tmp_path)
        
        # Verify file exists
        assert Path(tmp_path).exists()
        
        # Open and verify CF compliance
        ds = xr.open_dataset(tmp_path)
        
        # Check CF convention
        assert ds.attrs["Conventions"] == "CF-1.8"
        assert ds.attrs["featureType"] == "timeSeries"
        
        # Check time dimension
        assert "time" in ds.dims
        assert ds["time"].attrs["standard_name"] == "time"
        
        # Check variables
        assert "temp_c" in ds.data_vars
        assert ds["temp_c"].attrs["standard_name"] == "air_temperature"
        assert ds["temp_c"].attrs["units"] == "degree_Celsius"
        
        assert "rh_pct" in ds.data_vars
        assert ds["rh_pct"].attrs["standard_name"] == "relative_humidity"
        
        assert "wspd_ms" in ds.data_vars
        assert ds["wspd_ms"].attrs["standard_name"] == "wind_speed"
        
        ds.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_netcdf_with_metadata():
    """Test NetCDF export with custom metadata."""
    df = pd.DataFrame({
        "temp_c": [20.0, 21.0],
    }, index=pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"], utc=True))
    df.index.name = "ts_utc"
    
    metadata = {
        "title": "Test Weather Station",
        "institution": "Test University",
        "source": "Test AWS",
        "comment": "Test data for NetCDF export",
    }
    
    station_metadata = {
        "station_id": "TEST001",
        "station_name": "Test Station",
        "lat": 40.7128,
        "lon": -74.0060,
        "elev_m": 10.0,
    }
    
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        to_netcdf(df, tmp_path, metadata=metadata, station_metadata=station_metadata)
        
        ds = xr.open_dataset(tmp_path)
        
        # Check global metadata
        assert ds.attrs["title"] == "Test Weather Station"
        assert ds.attrs["institution"] == "Test University"
        assert ds.attrs["station_id"] == "TEST001"
        assert ds.attrs["station_name"] == "Test Station"
        
        # Check coordinates
        assert "latitude" in ds.coords
        assert ds.coords["latitude"].values == 40.7128
        assert ds["latitude"].attrs["standard_name"] == "latitude"
        assert ds["latitude"].attrs["units"] == "degrees_north"
        
        assert "longitude" in ds.coords
        assert ds.coords["longitude"].values == -74.0060
        
        assert "altitude" in ds.coords
        assert ds.coords["altitude"].values == 10.0
        
        ds.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_netcdf_with_qc_flags():
    """Test NetCDF export with QC flags."""
    df = pd.DataFrame({
        "temp_c": [10.0, 200.0, 12.0],
        "qc_temp_c_range": [False, True, False],
        "gap": [False, True, False],
    }, index=pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"], utc=True))
    df.index.name = "ts_utc"
    
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        to_netcdf(df, tmp_path)
        
        ds = xr.open_dataset(tmp_path)
        
        # Check QC flag attributes
        assert "qc_temp_c_range" in ds.data_vars
        assert "flag_values" in ds["qc_temp_c_range"].attrs
        assert "flag_meanings" in ds["qc_temp_c_range"].attrs
        
        # Check gap flag
        assert "gap" in ds.data_vars
        assert ds["gap"].attrs["flag_meanings"] == "observed_data missing_data"
        
        # Verify boolean flags are stored as int8
        assert ds["qc_temp_c_range"].dtype == np.int8
        assert ds["gap"].dtype == np.int8
        
        ds.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_netcdf_roundtrip():
    """Test NetCDF export and import roundtrip."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0, 12.0],
        "rh_pct": [50.0, 55.0, 60.0],
        "qc_temp_c_range": [False, False, True],
    }, index=pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"], utc=True))
    df.index.name = "ts_utc"
    
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Export
        to_netcdf(df, tmp_path)
        
        # Import
        df_imported = from_netcdf(tmp_path)
        
        # Verify index
        assert df_imported.index.name == "ts_utc"
        assert len(df_imported) == 3
        
        # Verify data
        assert "temp_c" in df_imported.columns
        assert "rh_pct" in df_imported.columns
        assert "qc_temp_c_range" in df_imported.columns
        
        # Verify QC flag is boolean
        assert df_imported["qc_temp_c_range"].dtype == bool
        
        # Verify values (allowing for float32 precision)
        np.testing.assert_allclose(df_imported["temp_c"].values, df["temp_c"].values, rtol=1e-5)
        np.testing.assert_array_equal(df_imported["qc_temp_c_range"].values, df["qc_temp_c_range"].values)
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_weatherset_to_netcdf():
    """Test WeatherSet.to_netcdf() method."""
    df = pd.DataFrame({
        "temp_c": [15.0, 16.0],
        "rh_pct": [60.0, 65.0],
    }, index=pd.to_datetime(["2025-01-01 00:00", "2025-01-01 01:00"], utc=True))
    df.index.name = "ts_utc"
    
    ws = WeatherSet(df)
    
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        ws.to_netcdf(
            tmp_path,
            metadata={"title": "Test WeatherSet"},
            station_metadata={"station_id": "WS001"},
        )
        
        assert Path(tmp_path).exists()
        
        ds = xr.open_dataset(tmp_path)
        assert ds.attrs["title"] == "Test WeatherSet"
        assert ds.attrs["station_id"] == "WS001"
        assert "temp_c" in ds.data_vars
        ds.close()
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)

