 ### JOSS-readiness feature checklist

 - Documentation
   - API reference (Sphinx or MkDocs) published (e.g., GitHub Pages)
   - Expanded README: installation, quickstart, Statement of Need, citation, roadmap
   - Canonical schema reference: variables, units, flags, metadata
   - QC algorithms: definitions, parameters, examples, caveats
   - CLI reference for all commands and options
   - Tutorials/notebooks for ingestion, QC, ML prep, export
   - Changelog and versioning policy (SemVer)

 - Core functionality completeness
   - Mapper/Detector:
     - [x] interactive mapping wizard
     - [x] robust autodetection
     - [ ] user mapping templates
   - WeatherSet: insert_missing with robust gap marking; resample/aggregate; fix_accum_rain; calendar_features; add_exogenous
   - Derived: implement heat index and wind chill (alongside dew point, VPD)
   - QC: spike (MAD/z-score), flatline (rolling variance), cross-variable consistency; configurable thresholds; mask/flag propagation
   - ML prep: make_supervised (lags, rolling, horizons), leakage-safe split, scaling (Standard/MinMax/Robust) with saved params
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
   - Zenodo archival with DOI per release, linked in README
   - CITATION.cff complete and validated
   - Badges: CI, coverage, PyPI, DOI

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


