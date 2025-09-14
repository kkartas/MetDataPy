 # MetDataPy

 Source-agnostic toolkit for ingesting, cleaning, QC-flagging, and preparing meteorological time-series data for machine learning.

 Quickstart:

 ```bash
 pip install -e .
 mdp ingest detect --csv path/to/file.csv --save mapping.yml
 mdp ingest apply --csv path/to/file.csv --map mapping.yml --out raw.parquet
 mdp qc run --in raw.parquet --out clean.parquet --report qc_report.json
 ```

Documentation
- Build with MkDocs (optional):
  - Install: `python -m pip install mkdocs`
  - Serve: `mkdocs serve`
  - Build: `mkdocs build`

Quality Control (new)
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


