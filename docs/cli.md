# CLI Reference

## Ingest

### Detect mapping
```bash
mdp ingest detect --csv FILE.csv [--save mapping.yml] [--yes]
```
- Autodetects timestamp and fields with confidence.
- Interactive wizard (omit `--yes`) lets you confirm/edit column and unit per field.

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
