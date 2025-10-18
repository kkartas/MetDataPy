 ### JOSS-readiness feature checklist

 - Documentation
   - [x] API reference (MkDocs scaffold)
   - [x] Expanded README: installation, quickstart, docs link
   - [x] Canonical schema reference: variables, units, flags, metadata
   - [x] QC algorithms: definitions and parameters
   - [x] CLI reference for implemented commands
   - [x] Tutorials/quickstart for ingestion, QC, ML prep
   - [ ] Changelog and versioning policy (SemVer)

 - Core functionality completeness
   - Mapper/Detector:
     - [x] interactive mapping wizard
     - [x] robust autodetection
     - [x] user mapping templates
   - WeatherSet:
     - [x] insert_missing with robust gap marking
     - [x] resample/aggregate
     - [x] fix_accum_rain
     - [x] calendar_features
     - [x] add_exogenous
   - Derived:
     - [x] dew point
     - [x] VPD
     - [x] heat index
     - [x] wind chill
   - QC:
     - [x] spike (MAD/z-score)
     - [x] flatline (rolling variance)
     - [x] cross-variable consistency
     - [x] configurable thresholds (CLI --config)
     - [x] mask/flag propagation (resample qc_* any, qc_any)
   - ML prep:
     - [x] make_supervised (lags, horizons)
     - [x] leakage-safe split (time_split)
     - [x] scaling (Standard/MinMax/Robust)
     - [ ] save/attach scaler params in manifest
   - Export: Parquet manifest.json (features/targets/scalers/provenance); NetCDF (CF-compliant) with ACDD metadata

 - Reproducibility and provenance
   - Manifest schema (pydantic): variables, units, steps, parameters, split boundaries, scaling params
   - Pipeline audit log with timestamps and a pipeline_hash
   - Deterministic behavior (fixed seeds), time-safe ops

 - CLI UX and ergonomics
   - mdp derive, mdp ml build, mdp export netcdf commands
   - Interactive confirm for mapping with confidence scores; non-interactive overrides
   - Global flags: --config, --log-level, --dry-run, --quiet/--verbose
   - Helpful errors and progress/log messages

 - I/O and schema robustness
   - Ingest from common CSV/JSON formats (Weathercloud and others), compressed files, chunked reading
   - Unit/autodetection from headers and metadata; timezone handling and DST resilience
   - CF mapping and xarray integration for NetCDF export

 - Validation and testing
   - High-coverage unit tests; end-to-end pipeline tests on sample data
   - Property-based tests for QC invariants (e.g., dew point ≤ temp)
   - Golden datasets and expected manifests for regression
   - Cross-platform CI (Linux/macOS/Windows), multiple Python versions
   - Coverage reports and badge

 - Packaging and distribution
   - PyPI wheels (sdist + manylinux/macOS/Windows); dependency constraints
   - Optional conda-forge recipe
   - Release automation on tags; version bumping workflow

 - Code quality and maintenance
   - Linters (ruff/flake8), formatter (black), type-checking (mypy)
   - Pre-commit hooks; CONTRIBUTING.md; CODE_OF_CONDUCT.md
   - Issue/PR templates; governance/maintenance plan

- Archival and citation
  - [ ] Zenodo archival with DOI per release, linked in README
  - [x] CITATION.cff complete and validated
  - [ ] Badges: CI, coverage, PyPI, DOI

 - Performance and scalability
   - Vectorized operations; memory-efficient ingest (pyarrow); optional chunking
   - Benchmarks and profiling; guidance for large datasets (e.g., dask/polars optional)

 - Extensibility and stability
   - Stable public API with deprecation policy
   - Plugin/adapter pattern for new data sources and QC rules
   - Config-driven pipelines (YAML) for reproducible runs

 - Compliance and ethics
   - Clear software license (MIT/Apache-2.0) and third-party license acknowledgments
   - Sample datasets licensing and privacy notes

 - Quality gates and validation
   - CF-compliance checks for NetCDF exports
   - Static analysis and (optional) security scanning in CI

 - Project operations for JOSS
   - Authorship/affiliations list in README
   - Clear statement of need and comparison to related tools
   - Installation and usage sections verifiable via CI (doctest or smoke tests)

 - Optional niceties
   - Command completion (shell completion scripts)
   - Telemetry opt-out hook (if any usage stats considered; default off)

 - Minimal data assets
   - Include or fetch small, license-compatible sample datasets for tutorials/tests

 - Logging/observability
   - Structured logs (JSON/TSV) and rotating file option
   - Error codes for CLI for automation

 - Internationalization/timezones
   - Explicit timezone handling guidance; robust conversion to UTC

 - Robust error handling
   - Clear exceptions for schema/units/NaNs; remediation suggestions

 - Readiness checklist for submission
   - All tests passing on matrix; docs built without warnings; a tagged release with DOI
   - “How to cite” section; archived release linked; contribution guidelines visible

 - Post-acceptance
   - Add JOSS status badge and citation to README once accepted



## Additional JOSS-ready enhancements (detailed checklist)

- Documentation and scientific rigor
  - [ ] Add literature references for formulas (Magnus, Tetens, Rothfusz, wind chill)
  - [ ] Statement of Need and comparison to related tools (MetPy, xarray, tsfresh)
  - [ ] Reproducibility guide: seeds, pinned deps, env export, deterministic ops

- Data sources and adapters
  - [ ] NOAA ISD/ASOS reader (CSV/API)
  - [ ] ERA5/ERA5-Land reanalysis adapter
  - [ ] Weathercloud/Weather Underground CSV variants
  - [ ] Metadata capture: station coords/elevation/source version

- QC advancements
  - [ ] Spike detection (rolling MAD/z-score)
  - [ ] Step-change/stuck sensor detection
  - [ ] Flatline via rolling variance
  - [ ] Cross-variable consistency (Td ≤ T; wspd≈0 ⇒ wdir NA; UV↔Solar bounds)
  - [ ] Configurable thresholds and rule toggles
  - [ ] Consolidated QC score and HTML report with plots

- Gap handling and imputation
  - [ ] Forward-fill with window; linear/spline; KNN
  - [ ] Seasonal naïve and STL-based residual imputation
  - [ ] Imputation flags and method provenance
  - [ ] Time-safe (train-only) imputation pipelines

- Derived metrics expansion
  - [ ] Wet-bulb temperature (Stull)
  - [ ] Saturation deficit / enthalpy
  - [ ] u/v wind components
  - [ ] Growing Degree Days; solar zenith/extraterrestrial radiation

- ML/AI readiness
  - [ ] Time-safe splitters (expanding/rolling window CV, blocked CV)
  - [ ] Robust lag/rolling builder with alignment checks
  - [ ] Holiday and astral feature generators
  - [ ] sklearn-compatible transformers for mapping/QC/derive/lag
  - [ ] Supervised window dataset generator (PyTorch/TF ready)

- Evaluation and benchmarks
  - [ ] Baselines (persistence, seasonal naïve)
  - [ ] Metrics (MAE/RMSE/SMAPE/CRPS)
  - [ ] Backtesting harness and example notebooks

- Export and standards
  - [ ] CF-compliant NetCDF variable attrs (units, standard_name)
  - [ ] ACDD global metadata; cf-checker validation
  - [ ] Manifest schema versioning and mdp manifest validate

- Performance and scale
  - [ ] Optional dask/polars backend
  - [ ] Chunked ingest; Parquet partitioning guidance
  - [ ] Benchmarks and memory profiling docs

- Extensibility and governance
  - [ ] Plugin API for QC rules/derivations/ingest adapters
  - [ ] Config-driven pipelines (YAML) runnable via mdp run
  - [ ] CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR templates

- CI and quality gates
  - [ ] Build docs warning-free in CI; publish to Pages
  - [ ] Coverage badge; mypy/ruff/bandit checks

- Archival and citation
  - [x] CITATION.cff complete and validated
  - [ ] Zenodo DOI per release, linked in README
  - [ ] License-compatible sample datasets for tests/tutorials

- Reliability and ops
  - [ ] Structured JSON logs and error codes
  - [ ] Robust timezone/DST tests and guidance

