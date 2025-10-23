# MetDataPy

[![CI](https://github.com/kkartas/MetDataPy/actions/workflows/ci.yml/badge.svg)](https://github.com/kkartas/MetDataPy/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/metdatapy/badge/?version=latest)](https://metdatapy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/kkartas/MetDataPy/branch/main/graph/badge.svg)](https://codecov.io/gh/kkartas/MetDataPy)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## Documentation

Full documentation is available on **[Read the Docs](https://metdatapy.readthedocs.io/)**.

To build documentation locally:
```bash
pip install -r docs/requirements.txt
mkdocs serve
# Then open http://localhost:8000
```

Features
- Canonical schema with UTC index and metric units
- Ingestion from CSV with mapping autodetection and interactive mapping wizard
- Unit normalization, rain accumulation fix-up, gap insertion with `gap` flag
- WeatherSet resampling/aggregation, calendar features, exogenous joins
- Derived: dew point, VPD, heat index, wind chill
- ML prep: supervised table builder (lags, horizons), time-safe split, scaling (Standard/MinMax/Robust)
- Export: Parquet and CF-compliant NetCDF with metadata

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

# Export to CF-compliant NetCDF
ws.to_netcdf("weather_data.nc", metadata={"title": "Weather Station Data"}, 
             station_metadata={"station_id": "AWS001", "lat": 40.7, "lon": -74.0})

sup = make_supervised(clean, targets=["temp_c"], horizons=[1,3], lags=[1,2,3])
splits = time_split(sup, train_end=pd.Timestamp("2025-01-15T00:00Z"))
scaler = fit_scaler(splits["train"], method="standard")
train_scaled = apply_scaler(splits["train"], scaler)
```

## Examples

See the `examples/` directory for:

**Jupyter Notebooks:**
- **`metdatapy_tutorial.ipynb`** - Publication-quality tutorial with visualizations and scientific references  
  [![nbviewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/metdatapy_tutorial.ipynb)
  [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/metdatapy_tutorial.ipynb)
  
- **`quickstart_tutorial.ipynb`** - Quick start guide for new users  
  [![nbviewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/quickstart_tutorial.ipynb)
  [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/quickstart_tutorial.ipynb)
  
- **`01_ingest_detect.ipynb`** - Data ingestion and mapping detection  
  [![nbviewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/01_ingest_detect.ipynb)
  [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/01_ingest_detect.ipynb)

**Python Scripts:**
- **`complete_workflow.py`** - Automated batch processing script
- **`netcdf_export_example.py`** - CF-compliant NetCDF export demonstration

**Additional Resources:**
- **`README.md`** - Detailed usage guide
- Sample weather data in `data/sample_weather_2024.csv`

**Try the notebooks online:**
- 🔍 **View** notebooks with [nbviewer](https://nbviewer.org/) (static rendering with proper formatting)
- 🚀 **Run** notebooks interactively with [Binder](https://mybinder.org/) (no installation required)

**Or run locally:**
```bash
cd examples
jupyter notebook metdatapy_tutorial.ipynb
```

**Automated workflow:**
```bash
cd examples
python complete_workflow.py
```

## Citation

If you use MetDataPy in your research, please cite it:

```bibtex
@software{metdatapy,
  title = {MetDataPy: A Source-Agnostic Toolkit for Meteorological Time-Series Data},
  author = {Kyriakos Kartas},
  year = {2025},
  url = {https://github.com/kkartas/MetDataPy},
  version = {0.0.1}
}
```

See `CITATION.cff` for machine-readable citation metadata.

## License

MIT License. See `LICENSE` for details.

