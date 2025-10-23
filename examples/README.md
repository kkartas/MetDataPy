# MetDataPy Examples

This directory contains example notebooks and scripts demonstrating MetDataPy's capabilities.

## Interactive Notebooks

**View options:** GitHub (native) | nbviewer (enhanced) | Binder (interactive)

> **Note:** If nbviewer shows an error, try the GitHub link or wait a few minutes for cache refresh.

### 1. Jupyter Notebook Tutorial (`metdatapy_tutorial.ipynb`)
[[GitHub](https://github.com/kkartas/MetDataPy/blob/main/examples/metdatapy_tutorial.ipynb)] 
[[nbviewer](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/metdatapy_tutorial.ipynb)] 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/metdatapy_tutorial.ipynb)

**Publication-quality interactive tutorial** with:
- Comprehensive documentation and scientific references
- Step-by-step workflow with explanations
- Publication-ready visualizations (QC flags, derived metrics)
- Mathematical formulas (Magnus, Tetens, Rothfusz)
- Complete reproducible pipeline

**To run locally:**
```bash
pip install -e ..
pip install jupyter matplotlib seaborn
jupyter notebook metdatapy_tutorial.ipynb
```

### 2. Quickstart Tutorial (`quickstart_tutorial.ipynb`)
[[GitHub](https://github.com/kkartas/MetDataPy/blob/main/examples/quickstart_tutorial.ipynb)] 
[[nbviewer](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/quickstart_tutorial.ipynb)] 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/quickstart_tutorial.ipynb)

Quick introduction to MetDataPy core features.

### 3. Ingestion & Detection (`01_ingest_detect.ipynb`)
[[GitHub](https://github.com/kkartas/MetDataPy/blob/main/examples/01_ingest_detect.ipynb)] 
[[nbviewer](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/01_ingest_detect.ipynb)] 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/01_ingest_detect.ipynb)

Focus on data ingestion and automatic column mapping detection.

## Python Scripts

### 1. Complete Workflow (`complete_workflow.py`)

Command-line script for automated processing:

1. **Data Ingestion** - Automatic column mapping and unit normalization
2. **Quality Control** - Range checks, spike/flatline detection, consistency checks
3. **Derived Metrics** - Dew point, VPD, heat index, wind chill
4. **Data Preparation** - Gap handling, resampling, calendar features
5. **ML Preparation** - Supervised datasets with lags, time-safe splits, scaling
6. **Export** - Save to Parquet with reproducible parameters

### 2. NetCDF Export Example (`netcdf_export_example.py`)

Demonstrates CF-compliant NetCDF export:

- **CF Conventions v1.8** - Standard names, units, and metadata
- **Global Attributes** - Title, institution, source, history, references
- **Station Metadata** - Coordinates (lat/lon/elevation), station ID
- **Variable Attributes** - Standard names, long names, units, valid ranges
- **QC Flags** - Preserved with proper flag meanings
- **Compression** - zlib level 4, float32 encoding

**Output:** `../data/processed/weather_data_hourly.nc`

**Validation:**
```bash
# Install CF checker
pip install cfchecker

# Validate CF compliance
cfchecks ../data/processed/weather_data_hourly.nc

# Inspect with ncdump
ncdump -h ../data/processed/weather_data_hourly.nc
```

### Running the Example

```bash
# Install dependencies
pip install -e ..

# Generate sample data (if not already done)
cd data
python generate_sample_data.py
cd ../examples

# Run the complete workflow
python complete_workflow.py
```

## Sample Data

The tutorial uses `../data/sample_weather_2024.csv`, which contains:
- Full year of synthetic weather data (2024)
- 10-minute frequency (~52,000 records)
- Realistic patterns with seasonal and diurnal variations
- Intentional anomalies for QC demonstration:
  - Temperature spikes
  - Humidity flatlines (stuck sensor)
  - Out-of-range values
  - Random data gaps (~2%)

### Data Generation

The sample data is generated using `../data/generate_sample_data.py`, which creates:
- Temperature with seasonal + diurnal cycles
- Relative humidity (inversely correlated with temp)
- Atmospheric pressure with slow variations
- Wind speed/direction with persistence
- Rainfall events (5% probability)
- Solar radiation (time/season dependent)
- UV index (proportional to solar)

All data is synthetic and MIT licensed for use in tutorials and tests.

## CLI Examples

### Detect Mapping

```bash
mdp ingest detect --csv ../data/sample_weather_2024.csv --save ../data/mapping.yml
```

### Apply Mapping and Ingest

```bash
mdp ingest apply --csv ../data/sample_weather_2024.csv \
  --map ../data/mapping.yml \
  --out ../data/raw.parquet
```

### Run Quality Control

```bash
mdp qc run --in ../data/raw.parquet \
  --out ../data/clean.parquet \
  --report ../data/qc_report.json \
  --config ../data/qc_config.yml
```

Example `qc_config.yml`:
```yaml
spike:
  window: 5
  thresh: 6.0
flatline:
  window: 5
  tol: 1e-6
```

## Python API Example

```python
import pandas as pd
from metdatapy.mapper import Detector, Mapper
from metdatapy.core import WeatherSet
from metdatapy.mlprep import make_supervised, time_split, scale

# Load and map data
df = pd.read_csv("../data/sample_weather_2024.csv")
detector = Detector()
mapping = detector.detect(df)
Mapper.save(mapping, "../data/mapping.yml")

# Create WeatherSet and process
ws = WeatherSet.from_mapping(df, mapping)
ws = ws.to_utc().normalize_units(mapping)
ws = ws.qc_range().qc_spike().qc_flatline().qc_consistency().qc_any()
ws = ws.derive(['dew_point', 'vpd', 'heat_index', 'wind_chill'])
ws = ws.insert_missing(frequency='10min').resample('1H')
ws = ws.calendar_features(cyclical=True)

# Get clean DataFrame
df_clean = ws.to_dataframe()

# Prepare for ML
df_ml = make_supervised(
    df_clean[['temp_c', 'rh_pct', 'pres_hpa', 'wspd_ms', 'dew_point_c', 
              'hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']],
    targets=['temp_c'],
    lags=[1, 2, 3, 6, 12, 24],
    target_horizons=[1, 3, 6],
    drop_na=True
)

# Time-safe split
train, val, test = time_split(
    df_ml,
    train_end=pd.Timestamp('2024-09-30', tz='UTC'),
    val_end=pd.Timestamp('2024-10-31', tz='UTC')
)

# Scale features
train_scaled, val_scaled, test_scaled, scaler_params = scale(
    train, val, test, method='standard'
)

# Export
train_scaled.to_parquet("../data/processed/train.parquet")
val_scaled.to_parquet("../data/processed/val.parquet")
test_scaled.to_parquet("../data/processed/test.parquet")
```

## Additional Resources

- [Full Documentation](../docs/)
- [API Reference](../docs/api/)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Citation](../CITATION.cff)

