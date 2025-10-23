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

## Requirements and Compatibility

**Python:** 3.9+

**Core dependencies:** pandas ≥2.0, numpy ≥1.23, pyarrow ≥13.0, click ≥8.1, pydantic ≥2.4, PyYAML ≥6.0

**NumPy Compatibility:** MetDataPy is compatible with both NumPy 1.x and 2.x. If you encounter compatibility issues with optional visualization dependencies (matplotlib, seaborn), you may need to either:
- Downgrade NumPy: `pip install 'numpy<2.0'`
- Or upgrade visualization libraries to versions compatible with NumPy 2.x

The core MetDataPy functionality works with both NumPy versions.

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
- **Performance:** Processes 1 year of 10-min data in <0.5s (see `benchmarks/`)

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

**Jupyter Notebook:**
- **`metdatapy_tutorial.ipynb`** - Publication-quality interactive tutorial  
  [![GitHub](https://img.shields.io/badge/view-GitHub-181717?logo=github)](https://github.com/kkartas/MetDataPy/blob/main/examples/metdatapy_tutorial.ipynb)
  [![nbviewer](https://img.shields.io/badge/render-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/kkartas/MetDataPy/blob/main/examples/metdatapy_tutorial.ipynb)
  [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kkartas/MetDataPy/main?filepath=examples/metdatapy_tutorial.ipynb)
  
  Comprehensive tutorial with:
  - Step-by-step workflow with scientific references
  - Publication-ready visualizations (QC flags, derived metrics)
  - Mathematical formulas and physical validation
  - Complete reproducible pipeline

**Python Scripts:**
- **`complete_workflow.py`** - Automated batch processing script
- **`netcdf_export_example.py`** - CF-compliant NetCDF export demonstration

**Additional Resources:**
- **`README.md`** - Detailed usage guide
- Sample weather data in `data/sample_weather_2024.csv`

**Try the notebooks:**
- 📁 **View on GitHub** - Click GitHub links above for native rendering (works immediately)
- 🔍 **View on nbviewer** - Better rendering with MathJax support
  - *Note: nbviewer may show 400 errors for new/recently updated files due to caching. If this happens, use GitHub view or try again in a few minutes.*
- 🚀 **Run interactively** - Click Binder badge for live Jupyter environment (takes ~2 min to launch)

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

