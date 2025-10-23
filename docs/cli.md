# CLI Reference

## Ingest

### Detect mapping
```bash
mdp ingest detect --csv FILE.csv [--save mapping.yml] [--yes]
```

Automatically detects timestamp and meteorological field columns with confidence scoring.

**Interactive mode** (default): Prompts you to review and refine each detected mapping
```bash
mdp ingest detect --csv weather_data.csv --save mapping.yml
```

**Non-interactive mode**: Accept all auto-detected mappings without prompts
```bash
mdp ingest detect --csv weather_data.csv --save mapping.yml --yes
```

The interactive wizard displays confidence scores and allows you to:
- Confirm or change the detected source column for each field
- Specify units (C/F for temperature, m/s/mph for wind speed, etc.)
- Type `none` to skip unmapped fields

### Apply mapping
```bash
mdp ingest apply --csv FILE.csv --map mapping.yml --out raw.parquet
```
- Applies explicit mapping, converts units to canonical, writes Parquet with index `ts_utc`.

### Template
```bash
mdp ingest template [--out mapping.yml] [--minimal]
```
- Prints or saves a mapping template. `--minimal` excludes optional fields.

## QC

### Run QC
```bash
mdp qc run --in raw.parquet --out clean.parquet [--report qc_report.json]
```
- Applies plausible range checks and writes flag counts to report if requested.
