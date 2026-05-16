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

CSV ingestion detects common delimiters and encodings, including semicolon-delimited Weathercloud exports encoded as UTF-16LE/BE without a BOM. For multiple Weathercloud files, use the Python helper:

```python
from metdatapy import read_weathercloud_directory

df, report = read_weathercloud_directory(
    "path/to/weathercloud_exports",
    "mapping.yml",
    duplicate_policy="keep_first",
    return_report=True,
)
```

Weathercloud ingestion localizes naive station timestamps with `nonexistent="shift_forward"` and `ambiguous="infer"` by default for DST transitions. If an isolated ambiguous fall-back row cannot be inferred from context, MetDataPy falls back to standard time deterministically.

## Python API

```python
from metdatapy.mapper import Mapper
from metdatapy.core import WeatherSet
from metdatapy.io import read_csv

mapping = Mapper.load("mapping.yml")
df = read_csv("path/to/file.csv")
ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
ws = ws.insert_missing().fix_accum_rain().qc_range()
ws = ws.derive(["dew_point", "vpd"]).resample("1h")
ws = ws.encode_wind_direction().rolling_features(["temp_c", "wdir_sin", "wdir_cos"], [3, 6])
ws = ws.calendar_features()
clean = ws.to_dataframe()
```
