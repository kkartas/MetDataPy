# Manifest & Reproducibility

MetDataPy provides a comprehensive manifest system for tracking data processing pipelines and ensuring reproducibility.

## Overview

A manifest is a JSON file that captures:
- **Dataset information**: Source, dimensions, time range, missing values
- **Pipeline steps**: All transformations with parameters and timestamps
- **Features**: Original, derived, lag, and calendar features
- **Quality control**: QC summary and flag counts
- **ML preparation**: Scaler parameters and train/val/test split boundaries
- **Pipeline hash**: Deterministic hash for reproducibility verification

## Creating Manifests

### Using ManifestBuilder

The `ManifestBuilder` class allows incremental manifest construction during pipeline execution:

```python
from metdatapy.manifest import ManifestBuilder, ScalerParamsModel, SplitBoundaries
import pandas as pd

# Initialize builder
builder = ManifestBuilder(source="weather_data.csv")

# Set dataset information
df = pd.read_parquet("processed_data.parquet")
builder.set_dataset_info(df, frequency="1H")

# Add pipeline steps
builder.add_step("load", "WeatherSet.from_csv", {"path": "weather_data.csv"})
builder.add_step("normalize", "WeatherSet.normalize_units", {"mapping": "mapping.yml"})
builder.add_step("qc", "WeatherSet.qc_range", {})
builder.add_step("resample", "WeatherSet.resample", {"rule": "1H"})

# Set QC report
builder.set_qc_report(df)

# Set derived features
builder.set_derived_features(["dew_point_c", "vpd_kpa", "heat_index_c"])

# Set scaler parameters
scaler = ScalerParamsModel(
    method="standard",
    columns=["temp_c", "rh_pct", "pres_hpa"],
    parameters={
        "temp_c": {"mean": 15.5, "scale": 8.2},
        "rh_pct": {"mean": 65.0, "scale": 15.3},
        "pres_hpa": {"mean": 1013.0, "scale": 10.5},
    }
)
builder.set_scaler(scaler)

# Set split boundaries
split = SplitBoundaries(
    train_start="2024-01-01T00:00:00Z",
    train_end="2024-09-30T23:59:59Z",
    val_start="2024-10-01T00:00:00Z",
    val_end="2024-10-31T23:59:59Z",
    test_start="2024-11-01T00:00:00Z",
    test_end="2024-12-31T23:59:59Z",
)
builder.set_split(split)

# Add custom metadata
builder.add_metadata("project", "Weather Forecasting")
builder.add_metadata("author", "Data Science Team")

# Build and save manifest
manifest = builder.build()
manifest.to_json("manifest.json")
```

## Manifest Structure

### Complete Example

```json
{
  "version": "1.0",
  "metdatapy_version": "1.0.0",
  "created_at": "2025-10-25T10:30:00Z",
  "pipeline_hash": "a1b2c3d4e5f6g7h8",
  
  "dataset": {
    "source": "weather_data.csv",
    "rows": 8761,
    "columns": ["temp_c", "rh_pct", "pres_hpa", "wspd_ms", "wdir_deg"],
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-12-31T23:00:00Z",
    "frequency": "1H",
    "missing_values": {
      "temp_c": 12,
      "wspd_ms": 5
    }
  },
  
  "pipeline_steps": [
    {
      "step": "load",
      "function": "WeatherSet.from_csv",
      "parameters": {"path": "weather_data.csv"},
      "timestamp": "2025-01-15T10:25:00Z",
      "duration_seconds": 2.5
    },
    {
      "step": "qc",
      "function": "WeatherSet.qc_range",
      "parameters": {},
      "timestamp": "2025-10-25T10:25:05Z",
      "duration_seconds": 0.8
    }
  ],
  
  "features": {
    "original_features": ["temp_c", "rh_pct", "pres_hpa"],
    "derived_features": ["dew_point_c", "vpd_kpa"],
    "lag_features": ["temp_c_lag1", "temp_c_lag2"],
    "calendar_features": ["hour", "weekday", "month"],
    "target_features": ["temp_c_t+1", "temp_c_t+3"]
  },
  
  "qc_report": {
    "total_flags": 145,
    "flagged_percentage": 1.65,
    "flags_by_type": {
      "qc_temp_c_range": 12,
      "qc_temp_c_spike": 8,
      "qc_rh_pct_flatline": 125
    }
  },
  
  "scaler": {
    "method": "standard",
    "columns": ["temp_c", "rh_pct"],
    "parameters": {
      "temp_c": {"mean": 15.5, "scale": 8.2},
      "rh_pct": {"mean": 65.0, "scale": 15.3}
    }
  },
  
  "split": {
    "train_start": "2024-01-01T00:00:00Z",
    "train_end": "2024-09-30T23:59:59Z",
    "val_start": "2024-10-01T00:00:00Z",
    "val_end": "2024-10-31T23:59:59Z",
    "test_start": "2024-11-01T00:00:00Z",
    "test_end": "2024-12-31T23:59:59Z"
  },
  
  "metadata": {
    "project": "Weather Forecasting",
    "author": "Data Science Team"
  }
}
```

## CLI Commands

### Validate Manifest

Check if a manifest file is valid:

```bash
mdp manifest validate manifest.json

# With verbose output
mdp manifest validate manifest.json --verbose
```

**Output:**
```
Validating manifest: manifest.json
✓ Manifest is valid

Manifest Details:
  Version: 1.0
  MetDataPy Version: 1.0.0
  Pipeline Steps: 4
  Pipeline Hash: a1b2c3d4e5f6g7h8
  Has QC Report: True
  Has Scaler: True
  Has Split: True
```

### Show Manifest

Display manifest contents in different formats:

```bash
# Summary view (default)
mdp manifest show manifest.json

# JSON format
mdp manifest show manifest.json --format json

# YAML format
mdp manifest show manifest.json --format yaml
```

**Summary Output:**
```
Manifest Summary
============================================================
Created: 2025-01-15T10:30:00Z
MetDataPy Version: 1.0.0
Pipeline Hash: a1b2c3d4e5f6g7h8

Dataset:
  Source: weather_data.csv
  Rows: 8,761
  Columns: 5
  Time Range: 2024-01-01T00:00:00Z to 2024-12-31T23:00:00Z
  Frequency: 1H

Pipeline Steps (4):
  1. WeatherSet.from_csv (2.50s)
  2. WeatherSet.normalize_units (0.15s)
  3. WeatherSet.qc_range (0.80s)
  4. WeatherSet.resample (1.20s)

Features:
  Original: 5
  Derived: 2
  Lag: 2
  Calendar: 3
  Target: 2

Quality Control:
  Total Flags: 145
  Flagged: 1.65%
  By Type:
    qc_rh_pct_flatline: 125
    qc_temp_c_range: 12
    qc_temp_c_spike: 8

Scaler:
  Method: standard
  Columns: 2

Split Boundaries:
  Train: 2024-01-01T00:00:00Z to 2024-09-30T23:59:59Z
  Val: 2024-10-01T00:00:00Z to 2024-10-31T23:59:59Z
  Test: 2024-11-01T00:00:00Z to 2024-12-31T23:59:59Z
```

### Compare Manifests

Compare two manifests for reproducibility:

```bash
mdp manifest compare manifest1.json manifest2.json
```

**Output:**
```
Comparing Manifests
============================================================
Manifest 1: manifest1.json
Manifest 2: manifest2.json

✓ Same Pipeline
✓ Same Version
✓ Same Features
✓ Same Scaler

✓ Manifests are compatible for reproducibility
```

## Pipeline Hash

The pipeline hash is a deterministic SHA-256 hash of:
- All pipeline steps (function names and parameters)
- Feature engineering configuration

**Purpose:**
- Verify that two datasets were processed identically
- Detect pipeline drift over time
- Ensure reproducibility in production

**Example:**
```python
manifest1 = Manifest.from_json("run1/manifest.json")
manifest2 = Manifest.from_json("run2/manifest.json")

if manifest1.pipeline_hash == manifest2.pipeline_hash:
    print("Identical processing pipelines")
else:
    print("Different pipelines - results may not be comparable")
```

## Reproducibility Validation

Compare two manifests to verify reproducibility:

```python
from metdatapy.manifest import Manifest

m1 = Manifest.from_json("experiment1/manifest.json")
m2 = Manifest.from_json("experiment2/manifest.json")

results = m1.validate_reproducibility(m2)

print(f"Same pipeline: {results['same_pipeline']}")
print(f"Same version: {results['same_version']}")
print(f"Same features: {results['same_features']}")
print(f"Same scaler: {results['same_scaler']}")
```

## Best Practices

### 1. Always Create Manifests

Generate a manifest for every processed dataset:

```python
# At the end of your pipeline
manifest = builder.build()
manifest.to_json(f"output/manifest_{timestamp}.json")
```

### 2. Version Control Manifests

Store manifests alongside processed data:

```
project/
├── data/
│   ├── processed/
│   │   ├── train.parquet
│   │   ├── val.parquet
│   │   ├── test.parquet
│   │   └── manifest.json  # ← Store here
```

### 3. Validate Before Training

Check manifest validity before ML training:

```python
from metdatapy.manifest import validate_manifest

results = validate_manifest("data/manifest.json")
if not results["valid"]:
    raise ValueError(f"Invalid manifest: {results['errors']}")
```

### 4. Compare Across Runs

Track pipeline changes over time:

```python
# Compare production vs. development
prod_manifest = Manifest.from_json("prod/manifest.json")
dev_manifest = Manifest.from_json("dev/manifest.json")

if prod_manifest.pipeline_hash != dev_manifest.pipeline_hash:
    print("⚠️ Pipeline has changed - review differences")
    results = prod_manifest.validate_reproducibility(dev_manifest)
    print(results)
```

### 5. Include Metadata

Add context-specific information:

```python
builder.add_metadata("experiment_id", "exp_2024_01")
builder.add_metadata("git_commit", "a1b2c3d")
builder.add_metadata("environment", "production")
builder.add_metadata("notes", "Added new QC thresholds")
```

## Integration with ML Workflows

### Scikit-learn Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor

# Build manifest during data preparation
builder = ManifestBuilder(source="weather.csv")
# ... add steps ...
manifest = builder.build()
manifest.to_json("models/manifest.json")

# Train model
model = Pipeline([
    ('scaler', StandardScaler()),
    ('rf', RandomForestRegressor())
])
model.fit(X_train, y_train)

# Save model with manifest reference
joblib.dump(model, "models/model.pkl")
# Manifest is already saved alongside
```

### MLflow Integration

```python
import mlflow

with mlflow.start_run():
    # Log manifest as artifact
    manifest.to_json("manifest.json")
    mlflow.log_artifact("manifest.json")
    
    # Log key metrics from manifest
    mlflow.log_param("pipeline_hash", manifest.pipeline_hash)
    mlflow.log_param("dataset_rows", manifest.dataset.rows)
    if manifest.qc_report:
        mlflow.log_metric("qc_flagged_pct", manifest.qc_report.flagged_percentage)
```

## Troubleshooting

### Manifest Validation Fails

**Issue:** `validate_manifest()` returns errors

**Solutions:**
1. Check JSON syntax: `python -m json.tool manifest.json`
2. Verify required fields are present
3. Ensure timestamps are ISO 8601 format
4. Check that pipeline_hash is computed

### Pipeline Hash Mismatch

**Issue:** Two manifests with same steps have different hashes

**Cause:** Parameter values differ (even slightly)

**Solution:** Compare pipeline steps:
```python
m1 = Manifest.from_json("manifest1.json")
m2 = Manifest.from_json("manifest2.json")

for s1, s2 in zip(m1.pipeline_steps, m2.pipeline_steps):
    if s1.parameters != s2.parameters:
        print(f"Difference in {s1.function}:")
        print(f"  M1: {s1.parameters}")
        print(f"  M2: {s2.parameters}")
```

### Large Manifest Files

**Issue:** Manifest JSON files are very large

**Solutions:**
1. Limit parameter detail in pipeline steps
2. Don't store full dataframes in metadata
3. Use gzip compression: `gzip manifest.json`

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [DVC for Data Versioning](https://dvc.org/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
