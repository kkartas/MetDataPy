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


