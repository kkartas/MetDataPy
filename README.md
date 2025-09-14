# MetDataPy

Source-agnostic toolkit for ingesting, cleaning, QC-flagging, enriching, and preparing meteorological time-series data for machine learning.

Quickstart:

```bash
pip install -e .
mdp ingest detect --csv path/to/file.csv --save mapping.yml
mdp ingest apply --csv path/to/file.csv --map mapping.yml --out raw.parquet
mdp qc run --in raw.parquet --out clean.parquet --report qc_report.json \
  --config qc_config.yml
```

Statement of Need
Modern ML pipelines require clean, unit-consistent, well-flagged meteorological time series. MetDataPy provides a canonical schema, robust ingestion (with autodetection and an interactive mapping wizard), quality control, derived metrics, time-safe ML preparation, and reproducible exports.

Documentation
- Build with MkDocs (optional):
  - Install: `python -m pip install mkdocs`
  - Serve: `mkdocs serve`
  - Build: `mkdocs build`

Features
- Canonical schema with UTC index and metric units
- Ingestion from CSV with mapping autodetection and interactive mapping wizard
- Unit normalization, rain accumulation fix-up, gap insertion with `gap` flag
- WeatherSet resampling/aggregation, calendar features, exogenous joins
- Derived: dew point, VPD, heat index, wind chill
- ML prep: supervised table builder (lags, horizons), time-safe split, scaling (Standard/MinMax/Robust)

Quality Control
- Range checks with boolean flags (`qc_<var>_range`)
- Spike detection (rolling MAD z-score) and flatline detection (rolling variance)
- Cross-variable consistency checks with aggregate `qc_any`
- CLI supports a config file for thresholds:

```bash
mdp qc run --in raw.parquet --out clean.parquet \
  --config qc_config.yml --report qc_report.json
```

Example `qc_config.yml`:
```yaml
spike:
  window: 9
  thresh: 6.0
flatline:
  window: 5
  tol: 0.0
```

Python API example
```python
import pandas as pd
from metdatapy.mapper import Mapper
from metdatapy.core import WeatherSet
from metdatapy.mlprep import make_supervised, time_split, fit_scaler, apply_scaler

mapping = Mapper.load("mapping.yml")
df = pd.read_csv("path/to/file.csv")
ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
ws = ws.insert_missing().fix_accum_rain().qc_range().qc_spike().qc_flatline().qc_consistency()
ws = ws.derive(["dew_point", "vpd", "heat_index", "wind_chill"]).resample("1H").calendar_features()
clean = ws.to_dataframe()

sup = make_supervised(clean, targets=["temp_c"], horizons=[1,3], lags=[1,2,3])
splits = time_split(sup, train_end=pd.Timestamp("2025-01-15T00:00Z"))
scaler = fit_scaler(splits["train"], method="standard")
train_scaled = apply_scaler(splits["train"], scaler)
```


