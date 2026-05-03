# MetDataPy

MetDataPy is a source-agnostic toolkit for ingesting, cleaning, QC-flagging, enriching, and preparing meteorological time-series data for machine learning.

## What it provides today

- Canonical schema with UTC timestamp index and metric units
- Ingestion from CSV with mapping (explicit or autodetected), including encoding/delimiter
  detection and optional `ts.timezone`
  metadata so naive local timestamps convert to UTC correctly
- Weathercloud CSV and directory ingestion helpers
- Interactive mapping wizard and robust autodetection heuristics
- Unit normalization, rain-rate schema support, and rain accumulation fix-up
- Quality control: range, spike (MAD), flatline, and cross-variable consistency checks with non-destructive flags
- Derived metrics: dew point, VPD, heat index, and wind chill
- WeatherSet operations: gap insertion, resampling/aggregation, wind-direction cyclic encoding, rolling features, calendar features, exogenous joins
- CLI commands for ingestion, QC, and templates

## Architecture

- `mapper.py`: mapping loader/saver and autodetector
- `core.py`: `WeatherSet` data container and transformations
- `weathercloud.py`: Weathercloud-specific CSV and directory ingestion
- `qc.py`: QC checks and flags
- `derive.py`: derived meteorological metrics
- `cli.py`: `mdp` command line interface

See the pages in the navigation for details.
