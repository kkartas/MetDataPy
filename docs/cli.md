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
- Declare the timestamp's source timezone (e.g. `UTC`, `US/Eastern`, `Europe/Athens`). Leave
  blank only if the source timestamps are already UTC — otherwise times will be interpreted
  as UTC and shifted silently.
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
- The template includes a `ts.timezone` field; fill it in with an IANA timezone name
  (e.g. `US/Eastern`) when your source timestamps are naive but not UTC.

## QC

### Run QC
```bash
mdp qc run --in raw.parquet --out clean.parquet [--report qc_report.json]
```
- Applies the full QC suite: range checks, spike detection (MAD), flatline detection, and cross-variable consistency checks.
- Writes boolean `qc_*` flag columns into the output Parquet file.
- If `--report` is given, writes a JSON summary of flag counts per check.
