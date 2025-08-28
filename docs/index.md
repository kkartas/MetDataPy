# MetDataPy

MetDataPy is a source-agnostic toolkit for ingesting, cleaning, QC-flagging, enriching, and preparing meteorological time-series data for machine learning.

## What it provides today

- Canonical schema with UTC timestamp index and metric units
- Ingestion from CSV with mapping (explicit or autodetected)
- Interactive mapping wizard and robust autodetection heuristics
- Unit normalization and rain accumulation fix-up
- Quality control: plausible range checks with flags
- Derived metrics: dew point and VPD
- WeatherSet operations: gap insertion, resampling/aggregation, calendar features, exogenous joins
- CLI commands for ingestion, QC, and templates

## Architecture

- `mapper.py`: mapping loader/saver and autodetector
- `core.py`: `WeatherSet` data container and transformations
- `qc.py`: QC checks and flags
- `derive.py`: derived meteorological metrics
- `cli.py`: `mdp` command line interface

See the pages in the navigation for details.
