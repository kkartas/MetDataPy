from typing import Optional, Dict, Any
import pandas as pd
import xarray as xr
import numpy as np


def read_csv(path: str, ts_col: Optional[str] = None) -> pd.DataFrame:
    """
    Read CSV file into a DataFrame with optional timestamp parsing.
    
    Parameters
    ----------
    path : str
        Path to CSV file
    ts_col : str, optional
        Column name to parse as datetime. If provided, attempts to convert
        this column to pandas datetime format
    
    Returns
    -------
    pd.DataFrame
        DataFrame with CSV contents
    
    Examples
    --------
    >>> from metdatapy.io import read_csv
    >>> df = read_csv('weather.csv', ts_col='DateTime')
    
    See Also
    --------
    read_parquet : Read Parquet files
    WeatherSet.from_csv : Higher-level CSV loading with mapping
    """
    df = pd.read_csv(path)
    if ts_col and ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    return df


def read_parquet(path: str) -> pd.DataFrame:
    """
    Read Parquet file into a DataFrame.
    
    Parameters
    ----------
    path : str
        Path to Parquet file
    
    Returns
    -------
    pd.DataFrame
        DataFrame with Parquet contents including index
    
    Examples
    --------
    >>> from metdatapy.io import read_parquet
    >>> df = read_parquet('weather_clean.parquet')
    
    See Also
    --------
    to_parquet : Write DataFrame to Parquet format
    read_csv : Read CSV files
    """
    return pd.read_parquet(path)


def to_parquet(df: pd.DataFrame, path: str) -> None:
    """
    Write DataFrame to Parquet file format.
    
    Saves DataFrame in Apache Parquet format with index preserved.
    Parquet provides efficient columnar storage with compression.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save
    path : str
        Output file path
    
    Examples
    --------
    >>> from metdatapy.io import to_parquet
    >>> to_parquet(clean_df, 'weather_clean.parquet')
    
    See Also
    --------
    read_parquet : Read Parquet files
    to_netcdf : Export to CF-compliant NetCDF
    """
    df.to_parquet(path, index=True)


def to_netcdf(
    df: pd.DataFrame,
    path: str,
    metadata: Optional[Dict[str, Any]] = None,
    station_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Export WeatherSet DataFrame to CF-compliant NetCDF4 file.
    
    Parameters
    ----------
    df : pd.DataFrame
        WeatherSet DataFrame with time index and meteorological variables
    path : str
        Output NetCDF file path
    metadata : dict, optional
        Global metadata (title, institution, source, history, references, comment)
    station_metadata : dict, optional
        Station-specific metadata (station_id, lat, lon, elev_m, station_name)
    
    Notes
    -----
    Follows CF Conventions v1.8 for climate and forecast metadata:
    http://cfconventions.org/
    """
    metadata = metadata or {}
    station_metadata = station_metadata or {}
    
    # CF-compliant variable metadata
    CF_ATTRS = {
        "temp_c": {
            "standard_name": "air_temperature",
            "long_name": "Air Temperature",
            "units": "degree_Celsius",
            "valid_min": -40.0,
            "valid_max": 55.0,
        },
        "rh_pct": {
            "standard_name": "relative_humidity",
            "long_name": "Relative Humidity",
            "units": "percent",
            "valid_min": 0.0,
            "valid_max": 100.0,
        },
        "pres_hpa": {
            "standard_name": "air_pressure",
            "long_name": "Atmospheric Pressure",
            "units": "hPa",
            "valid_min": 870.0,
            "valid_max": 1085.0,
        },
        "wspd_ms": {
            "standard_name": "wind_speed",
            "long_name": "Wind Speed",
            "units": "m s-1",
            "valid_min": 0.0,
            "valid_max": 70.0,
        },
        "wdir_deg": {
            "standard_name": "wind_from_direction",
            "long_name": "Wind Direction",
            "units": "degree",
            "valid_min": 0.0,
            "valid_max": 360.0,
        },
        "gust_ms": {
            "standard_name": "wind_speed_of_gust",
            "long_name": "Wind Gust Speed",
            "units": "m s-1",
            "valid_min": 0.0,
            "valid_max": 90.0,
        },
        "rain_mm": {
            "standard_name": "precipitation_amount",
            "long_name": "Rainfall",
            "units": "mm",
            "valid_min": 0.0,
            "valid_max": 500.0,
        },
        "solar_wm2": {
            "standard_name": "surface_downwelling_shortwave_flux_in_air",
            "long_name": "Solar Radiation",
            "units": "W m-2",
            "valid_min": 0.0,
            "valid_max": 1500.0,
        },
        "uv_index": {
            "long_name": "UV Index",
            "units": "1",
            "valid_min": 0.0,
            "valid_max": 15.0,
        },
        "dew_point_c": {
            "standard_name": "dew_point_temperature",
            "long_name": "Dew Point Temperature",
            "units": "degree_Celsius",
        },
        "vpd_kpa": {
            "long_name": "Vapor Pressure Deficit",
            "units": "kPa",
            "valid_min": 0.0,
        },
        "heat_index_c": {
            "long_name": "Heat Index",
            "units": "degree_Celsius",
        },
        "wind_chill_c": {
            "long_name": "Wind Chill Temperature",
            "units": "degree_Celsius",
        },
    }
    
    # Convert DataFrame to xarray Dataset
    # Note: xarray/numpy compatibility issue with tz-aware datetimes
    # Convert to tz-naive UTC before creating Dataset
    df_for_xr = df.copy()
    if df_for_xr.index.tz is not None:
        df_for_xr.index = df_for_xr.index.tz_localize(None)
    
    ds = xr.Dataset.from_dataframe(df_for_xr)
    
    # Rename time dimension to match CF conventions
    if "ts_utc" in ds.dims:
        ds = ds.rename({"ts_utc": "time"})
    
    # Add CF-compliant time attributes
    ds["time"].attrs = {
        "standard_name": "time",
        "long_name": "Time",
        "axis": "T",
    }
    
    # Add variable attributes
    for var in ds.data_vars:
        if var in CF_ATTRS:
            ds[var].attrs.update(CF_ATTRS[var])
        elif var.startswith("qc_"):
            # QC flags
            ds[var].attrs = {
                "long_name": f"Quality Control Flag: {var.replace('qc_', '').replace('_', ' ').title()}",
                "flag_values": "0, 1",
                "flag_meanings": "good_data bad_data",
                "comment": "True (1) indicates data failed quality control check",
            }
        elif var == "gap":
            ds[var].attrs = {
                "long_name": "Gap Flag",
                "flag_values": "0, 1",
                "flag_meanings": "observed_data missing_data",
                "comment": "True (1) indicates missing data filled by reindexing",
            }
        elif var == "imputed":
            ds[var].attrs = {
                "long_name": "Imputation Flag",
                "flag_values": "0, 1",
                "flag_meanings": "original_data imputed_data",
            }
        elif var == "impute_method":
            ds[var].attrs = {
                "long_name": "Imputation Method",
            }
    
    # Add station metadata as coordinates if provided
    if station_metadata:
        if "lat" in station_metadata:
            ds.coords["latitude"] = station_metadata["lat"]
            ds["latitude"].attrs = {
                "standard_name": "latitude",
                "long_name": "Latitude",
                "units": "degrees_north",
                "axis": "Y",
            }
        if "lon" in station_metadata:
            ds.coords["longitude"] = station_metadata["lon"]
            ds["longitude"].attrs = {
                "standard_name": "longitude",
                "long_name": "Longitude",
                "units": "degrees_east",
                "axis": "X",
            }
        if "elev_m" in station_metadata:
            ds.coords["altitude"] = station_metadata["elev_m"]
            ds["altitude"].attrs = {
                "standard_name": "altitude",
                "long_name": "Altitude",
                "units": "m",
                "positive": "up",
                "axis": "Z",
            }
        if "station_id" in station_metadata:
            ds.attrs["station_id"] = station_metadata["station_id"]
        if "station_name" in station_metadata:
            ds.attrs["station_name"] = station_metadata["station_name"]
    
    # Add global attributes (CF-compliant)
    ds.attrs.update({
        "Conventions": "CF-1.8",
        "title": metadata.get("title", "Meteorological Time Series Data"),
        "institution": metadata.get("institution", ""),
        "source": metadata.get("source", "MetDataPy"),
        "history": metadata.get("history", f"Created with MetDataPy on {pd.Timestamp.now().isoformat()}"),
        "references": metadata.get("references", "https://github.com/kkartas/MetDataPy"),
        "comment": metadata.get("comment", "Processed with MetDataPy - A source-agnostic toolkit for meteorological time-series data"),
        "featureType": "timeSeries",
    })
    
    # Write to NetCDF4 with compression
    encoding = {}
    for var in ds.data_vars:
        if ds[var].dtype == bool:
            # Convert boolean to int8 for NetCDF compatibility
            ds[var] = ds[var].astype(np.int8)
        encoding[var] = {
            "zlib": True,
            "complevel": 4,
            "dtype": "float32" if ds[var].dtype == np.float64 else ds[var].dtype,
        }
    
    ds.to_netcdf(path, format="NETCDF4", encoding=encoding)


def from_netcdf(path: str) -> pd.DataFrame:
    """
    Read a CF-compliant NetCDF file into a WeatherSet-compatible DataFrame.
    
    Parameters
    ----------
    path : str
        Path to NetCDF file
    
    Returns
    -------
    pd.DataFrame
        DataFrame with time index and meteorological variables
    """
    ds = xr.open_dataset(path)
    
    # Convert to DataFrame
    df = ds.to_dataframe()
    
    # Rename time dimension back to ts_utc if needed
    if "time" in df.index.names:
        df.index.names = ["ts_utc" if name == "time" else name for name in df.index.names]
    
    # Drop coordinate variables that are not time-series data
    coords_to_drop = ["latitude", "longitude", "altitude"]
    df = df.drop(columns=[c for c in coords_to_drop if c in df.columns], errors="ignore")
    
    # Convert int8 flags back to bool
    for col in df.columns:
        if col.startswith("qc_") or col == "gap" or col == "imputed":
            if df[col].dtype == np.int8:
                df[col] = df[col].astype(bool)
    
    return df


