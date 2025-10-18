#!/usr/bin/env python3
"""
Example: Exporting Weather Data to CF-Compliant NetCDF

This script demonstrates how to export processed meteorological data
to NetCDF format following CF (Climate and Forecast) Conventions v1.8.

NetCDF is the standard format for climate and weather data archival,
ensuring interoperability with tools like xarray, nco, cdo, and Panoply.
"""

import pandas as pd
from metdatapy.core import WeatherSet
from metdatapy.mapper import Mapper

# Load and process data
print("Loading sample weather data...")
mapping = Mapper.load("../data/mapping.yml")
df = pd.read_csv("../data/sample_weather_2024.csv")

# Create WeatherSet and process
ws = (
    WeatherSet.from_mapping(df, mapping)
    .to_utc()
    .normalize_units(mapping)
    .insert_missing(frequency="10min")
    .fix_accum_rain()
    .qc_range()
    .qc_spike()
    .qc_flatline()
    .qc_consistency()
)

# Add derived metrics
ws = ws.derive(["dew_point", "vpd", "heat_index", "wind_chill"])

# Resample to hourly
ws = ws.resample("1H")

print(f"Processed {len(ws.to_dataframe())} hourly records")

# Define metadata following CF and ACDD conventions
metadata = {
    "title": "Sample Weather Station Data - 2024",
    "institution": "MetDataPy Example",
    "source": "Synthetic Automatic Weather Station",
    "history": f"Created with MetDataPy on {pd.Timestamp.now().isoformat()}. "
               "Quality controlled with range, spike, flatline, and consistency checks. "
               "Resampled to hourly averages.",
    "references": "https://github.com/kkartas/MetDataPy",
    "comment": "Synthetic weather data for demonstration purposes. "
               "Contains intentional anomalies for QC testing.",
}

# Station metadata (coordinates, elevation, identifiers)
station_metadata = {
    "station_id": "SAMPLE_AWS_001",
    "station_name": "Sample Weather Station",
    "lat": 40.7128,  # Example: New York City
    "lon": -74.0060,
    "elev_m": 10.0,
}

# Export to NetCDF
output_path = "../data/processed/weather_data_hourly.nc"
print(f"\nExporting to CF-compliant NetCDF: {output_path}")

ws.to_netcdf(
    output_path,
    metadata=metadata,
    station_metadata=station_metadata,
)

print("[OK] NetCDF export complete!")

# Verify the export
print("\n" + "="*60)
print("NetCDF File Information:")
print("="*60)

import xarray as xr
ds = xr.open_dataset(output_path)

print(f"\nGlobal Attributes:")
print(f"  Conventions: {ds.attrs['Conventions']}")
print(f"  Title: {ds.attrs['title']}")
print(f"  Station ID: {ds.attrs.get('station_id', 'N/A')}")

print(f"\nDimensions:")
print(f"  time: {ds.dims['time']} records")

print(f"\nCoordinates:")
if 'latitude' in ds.coords:
    print(f"  Latitude: {ds.coords['latitude'].values}°N")
if 'longitude' in ds.coords:
    print(f"  Longitude: {ds.coords['longitude'].values}°E")
if 'altitude' in ds.coords:
    print(f"  Altitude: {ds.coords['altitude'].values} m")

print(f"\nData Variables ({len(ds.data_vars)}):")
for var in list(ds.data_vars)[:10]:  # Show first 10
    attrs = ds[var].attrs
    std_name = attrs.get('standard_name', 'N/A')
    units = attrs.get('units', 'N/A')
    print(f"  {var:20s} | {std_name:40s} | {units}")

if len(ds.data_vars) > 10:
    print(f"  ... and {len(ds.data_vars) - 10} more variables")

print(f"\nQC Flags:")
qc_vars = [v for v in ds.data_vars if v.startswith('qc_')]
print(f"  {len(qc_vars)} quality control flags included")

ds.close()

print("\n" + "="*60)
print("Validation:")
print("="*60)
print("\nTo validate CF compliance, run:")
print("  pip install cfchecker")
print(f"  cfchecks {output_path}")
print("\nTo inspect with command-line tools:")
print(f"  ncdump -h {output_path}")
print(f"  ncdump -v temp_c {output_path} | head -20")
print("\nTo visualize:")
print("  - Panoply: https://www.giss.nasa.gov/tools/panoply/")
print("  - ncview: http://meteora.ucsd.edu/~pierce/ncview_home_page.html")

print("\n[OK] Example complete!")

