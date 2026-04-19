# Quickstart

## Install (editable)

```bash
python -m pip install -e .
```

## Detect and save a mapping

**Option 1: Interactive wizard** (recommended for first-time use)
```bash
mdp ingest detect --csv path/to/file.csv --save mapping.yml
```
This launches an interactive wizard that lets you review and refine auto-detected column mappings. You can press Enter to accept defaults or type custom values. The wizard also prompts for the timestamp's source timezone — set this to the zone of your naive timestamps (e.g. `US/Eastern`) so they are converted to UTC correctly.

**Option 2: Non-interactive** (auto-accept detected mappings)
```bash
mdp ingest detect --csv path/to/file.csv --save mapping.yml --yes
```
After saving, open `mapping.yml` and set `ts.timezone` manually if your source timestamps are naive but not UTC. See [Mapper & Detector](mapper.md) for the full schema.

## Apply mapping and run QC

```bash
mdp ingest apply --csv path/to/file.csv --map mapping.yml --out raw.parquet
mdp qc run --in raw.parquet --out clean.parquet --report qc_report.json
```

## Python API

```python
from metdatapy.mapper import Mapper
from metdatapy.core import WeatherSet
import pandas as pd

mapping = Mapper.load("mapping.yml")
df = pd.read_csv("path/to/file.csv")
ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
ws = ws.insert_missing().fix_accum_rain().qc_range()
ws = ws.derive(["dew_point", "vpd"]).resample("1h")
ws = ws.calendar_features()
clean = ws.to_dataframe()
```
