# Export Formats

MetDataPy supports multiple export formats for interoperability and archival.

## Parquet Export

Parquet is a columnar storage format optimized for analytics and ML workflows.

```python
from metdatapy.io import to_parquet

# Export to Parquet
to_parquet(ws.to_dataframe(), "weather_data.parquet")

# Or directly from WeatherSet
ws.to_dataframe().to_parquet("weather_data.parquet")
```

**Advantages:**
- Fast read/write performance
- Efficient compression
- Preserves data types
- Wide tool support (pandas, Spark, DuckDB, etc.)

## NetCDF Export (CF-Compliant)

NetCDF (Network Common Data Form) is the standard format for climate and meteorological data, following CF (Climate and Forecast) Conventions v1.8.

### Basic Export

```python
# Export to NetCDF
ws.to_netcdf("weather_data.nc")

# Or using the io module
from metdatapy.io import to_netcdf
to_netcdf(ws.to_dataframe(), "weather_data.nc")
```

### With Metadata

```python
metadata = {
    "title": "Hourly Weather Observations - Station XYZ",
    "institution": "University Weather Network",
    "source": "Automatic Weather Station",
    "history": "Quality controlled and processed with MetDataPy",
    "references": "https://doi.org/10.xxxx/xxxxx",
    "comment": "Data collected for agricultural research",
}

station_metadata = {
    "station_id": "AWS_001",
    "station_name": "Central Campus Weather Station",
    "lat": 40.7128,
    "lon": -74.0060,
    "elev_m": 10.0,
}

ws.to_netcdf(
    "weather_data.nc",
    metadata=metadata,
    station_metadata=station_metadata,
)
```

### CF-Compliant Features

The NetCDF export includes:

**Global Attributes (CF-1.8):**
- `Conventions`: "CF-1.8"
- `featureType`: "timeSeries"
- `title`, `institution`, `source`, `history`, `references`, `comment`

**Time Dimension:**
- Standard name: `time`
- Axis: `T`
- UTC-aware datetime encoding

**Variable Attributes:**
- `standard_name`: CF standard names (e.g., `air_temperature`, `wind_speed`)
- `long_name`: Human-readable descriptions
- `units`: CF-compliant units (e.g., `degree_Celsius`, `m s-1`)
- `valid_min`, `valid_max`: Physical plausibility ranges

**Spatial Coordinates:**
- `latitude` (degrees_north, axis Y)
- `longitude` (degrees_east, axis X)
- `altitude` (m, axis Z, positive up)

**QC Flags:**
- `flag_values`: "0, 1"
- `flag_meanings`: "good_data bad_data"
- Stored as int8 for NetCDF compatibility

**Compression:**
- zlib compression (level 4)
- float64 → float32 conversion for efficiency

### Supported Variables

All canonical MetDataPy variables are mapped to CF standard names:

| MetDataPy Variable | CF Standard Name | Units |
|-------------------|------------------|-------|
| `temp_c` | `air_temperature` | degree_Celsius |
| `rh_pct` | `relative_humidity` | percent |
| `pres_hpa` | `air_pressure` | hPa |
| `wspd_ms` | `wind_speed` | m s-1 |
| `wdir_deg` | `wind_from_direction` | degree |
| `gust_ms` | `wind_speed_of_gust` | m s-1 |
| `rain_mm` | `precipitation_amount` | mm |
| `solar_wm2` | `surface_downwelling_shortwave_flux_in_air` | W m-2 |
| `uv_index` | (no CF standard name) | 1 |
| `dewpoint_c` | `dew_point_temperature` | degree_Celsius |
| `vpd_kpa` | (no CF standard name) | kPa |
| `heat_index_c` | (no CF standard name) | degree_Celsius |
| `wind_chill_c` | (no CF standard name) | degree_Celsius |

### Reading NetCDF Files

```python
from metdatapy.io import from_netcdf

# Import NetCDF back to DataFrame
df = from_netcdf("weather_data.nc")

# Create WeatherSet from imported data
ws = WeatherSet(df)
```

**Automatic Conversions:**
- `time` dimension → `ts_utc` index
- int8 QC flags → boolean
- Coordinate variables (lat/lon/alt) dropped from time series

### Validation

Verify CF compliance using standard tools:

```bash
# Install CF checker
pip install cfchecker

# Validate NetCDF file
cfchecks weather_data.nc
```

Or use `ncdump` to inspect metadata:

```bash
ncdump -h weather_data.nc
```

## Manifest (Planned)

Future releases will include `manifest.json` export with:
- Variable inventory
- Feature engineering provenance
- Scaler parameters
- QC summary statistics
- Pipeline hash for reproducibility

## Comparison

| Format | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Parquet** | ML workflows, analytics | Fast, efficient, wide support | Not self-describing |
| **NetCDF** | Scientific archival, sharing | CF-compliant, self-describing, metadata-rich | Larger file size, slower I/O |
| **CSV** | Human inspection, legacy systems | Universal compatibility | Large, no metadata, type ambiguity |

## Best Practices

1. **For ML/AI projects**: Use Parquet for speed and efficiency
2. **For scientific publication**: Use NetCDF for CF compliance and metadata
3. **For data sharing**: Provide both formats when possible
4. **For archival**: Use NetCDF with comprehensive metadata
5. **For version control**: Use manifest.json (when available) to track provenance
