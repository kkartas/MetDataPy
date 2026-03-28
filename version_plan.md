# Version Plan

Current version: `v1.0.1`

This document defines the implementation path from `v1.0.1` forward.
It is written to be used directly by Codex for one-task-at-a-time execution.

## Working Rules

- Treat each task below as one Codex task and one pull request.
- For every task:
  - add focused regression tests first or alongside the fix
  - run `python -m pytest -q`
  - update public docs if behavior changes
- Do not combine tasks across releases until the earlier release is green and tagged.
- Prefer backward-compatible changes within patch releases.
- If a task changes file formats, CLI behavior, or public API semantics, document the migration in `README.md` and the relevant docs page.

## v1.0.1: Ingestion Hardening

### Goal

Eliminate silent schema corruption during ingest and make public CSV-loading behavior consistent across API and CLI.

### Task 1: Stop false-positive field mappings

**Primary files**
- `metdatapy/mapper.py`
- `tests/test_mapper.py`

**Implementation**
- Update `Detector.detect()` in `metdatapy/mapper.py`.
- Only emit a canonical field when there is real evidence for it.
- Require at least one of:
  - a positive column-name pattern match
  - a positive unit hint
- Add a minimum confidence threshold before a field is accepted.
- Prevent the same source column from being assigned to multiple canonical fields by default.
- If multiple canonical fields compete for the same source column, keep the best-supported mapping and drop the weaker ones.
- If evidence is weak or absent, omit the canonical field entirely instead of guessing.

**Acceptance criteria**
- A dataset with only `timestamp`, `temperature`, `humidity`, and `pressure` does not invent mappings for:
  - `wspd_ms`
  - `wdir_deg`
  - `gust_ms`
  - `rain_mm`
  - `solar_wm2`
  - `uv_index`
- Existing obvious mappings like temperature and humidity still detect correctly.
- Confidence values remain present for accepted mappings.

**Tests**
- Add regressions to `tests/test_mapper.py` showing:
  - absent variables are not fabricated
  - one source column is not reused for multiple canonical outputs
  - normal cases still work

### Task 2: Unify CSV loading through one shared reader

**Primary files**
- `metdatapy/io.py`
- `metdatapy/core.py`
- `metdatapy/mapper.py`
- `metdatapy/cli.py`
- `tests/test_encoding.py`
- `tests/test_core.py`
- `tests/test_cli.py`

**Implementation**
- Create one shared internal CSV reader in `metdatapy/io.py` that:
  - detects encoding
  - reads CSV with `encoding_errors="replace"`
  - optionally parses a timestamp column
- Route all CSV reads through it:
  - `WeatherSet.from_csv()` in `metdatapy/core.py`
  - `Detector.detect_from_csv()` in `metdatapy/mapper.py`
  - ingest commands in `metdatapy/cli.py`
- Keep behavior consistent between Python API and CLI.

**Acceptance criteria**
- UTF-16, CP1252, and Latin-1 files behave consistently in:
  - Python API
  - detector path
  - CLI ingest commands
- Previously supported UTF-8 cases continue to work unchanged.

**Tests**
- Extend `tests/test_encoding.py` for shared-loader coverage.
- Add regressions in `tests/test_core.py` for `WeatherSet.from_csv()` with non-UTF-8 input.
- Add regressions in `tests/test_cli.py` for `mdp ingest detect` and `mdp ingest apply` on non-UTF-8 input.

### Task 3: Fix mapping-template and manifest edge behavior

**Primary files**
- `metdatapy/cli.py`
- `metdatapy/manifest.py`
- `tests/test_cli.py`
- `tests/test_manifest.py`

**Implementation**
- In `metdatapy/cli.py`, make `mdp ingest template` emit YAML mapping content when writing mapping files.
- Reuse `Mapper.save()` instead of writing JSON into `.yml` files.
- In `metdatapy/manifest.py`, fix `Manifest.validate_reproducibility()` so scaler comparison is correct:
  - if only one manifest has a scaler, `same_scaler` must be `False`
  - if both have scalers, compare method, columns, and parameters
- In `ManifestBuilder.set_dataset_info()`, validate the index type and fail with a clear error on non-datetime indexes.

**Acceptance criteria**
- Template files written via CLI are valid YAML mappings.
- Manifest comparison does not report false compatibility for scaler presence mismatches.
- Non-datetime indexed input to `ManifestBuilder.set_dataset_info()` fails cleanly with an actionable message.

**Tests**
- Add CLI template-output assertions in `tests/test_cli.py`.
- Add manifest scaler mismatch and non-datetime-index regressions in `tests/test_manifest.py`.

## v1.0.2: QC and Gap-Fill Hardening

### Goal

Remove false negatives and false positives in missing-row handling and QC flagging.

### Task 4: Make `insert_missing()` work for mostly regular series with gaps

**Primary files**
- `metdatapy/core.py`
- `metdatapy/utils.py`
- `tests/test_core.py`
- `tests/test_integration.py`

**Implementation**
- Update `WeatherSet.insert_missing()` in `metdatapy/core.py`.
- Replace raw `pd.infer_freq()` usage with `metdatapy.utils.infer_frequency()`.
- Normalize deprecated frequency aliases consistently.
- Only skip reindexing when no usable frequency can be derived.
- Preserve existing `gap` semantics.

**Acceptance criteria**
- A series like `00:00, 02:00, 03:00` can infer an hourly cadence and insert the missing `01:00` row.
- Existing no-gap regular series remain unchanged.
- Existing explicit `frequency=` behavior remains supported.

**Tests**
- Add regressions in `tests/test_core.py` for a mostly regular hourly series with one missing timestamp.
- Add end-to-end coverage in `tests/test_integration.py`.

### Task 5: Remove false flatline flags on short or partially missing series

**Primary files**
- `metdatapy/qc.py`
- `tests/test_qc.py`

**Implementation**
- Update `qc_flatline()` in `metdatapy/qc.py`.
- Do not convert `NaN` rolling variance to `0.0`.
- Only flag flatlines when the rolling window has enough valid observations and variance is genuinely below tolerance.
- Preserve existing behavior for true flatline sequences.

**Acceptance criteria**
- Short series are not automatically marked as flatline.
- Windows dominated by missing values are not marked as flatline by default.
- True constant windows still flag correctly.

**Tests**
- Add regressions in `tests/test_qc.py` for:
  - short series
  - windows with NaNs
  - true flatlines

### Task 6: Remove silent exception swallowing in resample QC propagation

**Primary files**
- `metdatapy/core.py`
- `tests/test_core.py`

**Implementation**
- Replace the `try/except: pass` in `WeatherSet.resample()` around `qc_*` propagation with explicit boolean aggregation logic.
- Aggregate QC flags with OR semantics over the resample window.
- Keep `gap` propagation explicit and testable.
- Fail loudly if an unsupported QC column shape is encountered.

**Acceptance criteria**
- Multiple `qc_*` columns are propagated deterministically.
- No silent failure path remains in QC propagation.
- Existing gap propagation continues to work.

**Tests**
- Add regressions in `tests/test_core.py` covering:
  - multiple QC columns
  - gap propagation
  - mixed aggregation windows

## v1.1.0: Timezone-Safe Ingest and Export

### Goal

Make timezone semantics explicit and preserve real instants across ingest and export.

### Task 7: Add timezone metadata to mappings

**Primary files**
- `metdatapy/mapper.py`
- `metdatapy/cli.py`
- `metdatapy/core.py`
- `metdatapy/utils.py`
- `tests/test_utils.py`
- `tests/test_core.py`
- `tests/test_cli.py`

**Implementation**
- Extend the mapping schema so `ts` can carry a `timezone` field.
- Update `Mapper.template()` in `metdatapy/mapper.py` to include timezone support.
- Update the interactive mapping wizard in `metdatapy/cli.py` to prompt for timezone.
- Thread timezone into `WeatherSet.from_mapping()` via `ensure_datetime_utc()`.
- Preserve backward compatibility:
  - if timezone is omitted, keep current behavior
  - but emit a warning when naive timestamps are mapped without timezone metadata

**Acceptance criteria**
- Naive local timestamps can be correctly interpreted using mapping-provided timezone metadata.
- Existing timezone-aware timestamps continue to normalize to UTC correctly.
- Old mapping files without timezone still work.

**Tests**
- Add timezone-hint regressions in `tests/test_utils.py`.
- Add mapping-based timezone ingestion regressions in `tests/test_core.py`.
- Add CLI wizard and ingest regressions in `tests/test_cli.py`.

### Task 8: Fix NetCDF instant preservation

**Primary files**
- `metdatapy/io.py`
- `tests/test_netcdf.py`

**Implementation**
- In `to_netcdf()`, if the index is tz-aware:
  - first convert to UTC
  - then strip timezone info for xarray compatibility
- In `from_netcdf()`, localize the returned time index to UTC so round-tripped data remains UTC-aware.

**Acceptance criteria**
- A non-UTC tz-aware input index round-trips through NetCDF without shifting instants.
- Existing UTC input still round-trips correctly.

**Tests**
- Add a round-trip regression in `tests/test_netcdf.py` using a non-UTC tz-aware index and assert identical UTC instants after reload.

## v1.2.0: Meteorological Correctness

### Goal

Fix domain-invalid derived metrics and physically incorrect aggregation behavior.

### Task 9: Make derived thermal indices domain-aware

**Primary files**
- `metdatapy/derive.py`
- `tests/test_derive.py`
- `tests/test_core.py`

**Implementation**
- Update `heat_index_c()` in `metdatapy/derive.py` so out-of-domain cases do not return values below ambient temperature.
- Update `wind_chill_c()` so out-of-domain cases return ambient temperature instead of extrapolated wind chill.
- Match the documented validity domains in the docstrings.

**Acceptance criteria**
- Heat index does not create cooling effects in inappropriate domains.
- Wind chill does not create warming/cooling artifacts outside valid conditions.
- In-domain calculations remain meteorologically reasonable.

**Tests**
- Add boundary and out-of-domain regressions in `tests/test_derive.py`.
- Add `WeatherSet.derive()` regressions in `tests/test_core.py`.

### Task 10: Fix consistency QC and wind-direction resampling semantics

**Primary files**
- `metdatapy/qc.py`
- `metdatapy/core.py`
- `tests/test_core.py`
- `tests/test_qc.py`

**Implementation**
- In `qc_consistency()` in `metdatapy/qc.py`, apply heat-index and wind-chill checks only when those metrics are within their valid domains.
- In `WeatherSet.resample()` in `metdatapy/core.py`, replace arithmetic mean aggregation for `wdir_deg` with circular mean.
- Prefer speed-weighted circular mean when `wspd_ms` is available.
- Return `NaN` for undefined calm resultant direction.

**Acceptance criteria**
- `350°` and `10°` aggregate to approximately `0°`, not `180°`.
- Library-generated heat index and wind chill no longer self-trigger false consistency failures.

**Tests**
- Add QC regressions in `tests/test_qc.py`.
- Add circular wind-direction resample regressions in `tests/test_core.py`.

## v1.3.0: Provenance-Preserving Imputation

### Goal

Add missing-data handling without losing auditability.

### Task 11: Add a dedicated imputation module

**Primary files**
- `metdatapy/impute.py` (new)
- `metdatapy/core.py`
- `tests/test_impute.py` (new)

**Implementation**
- Create `metdatapy/impute.py` with an API such as:
  - `impute(df, method, columns=None, limit=None, value=None)`
- Support at least:
  - `ffill`
  - `bfill`
  - `interpolate_time`
  - `constant`
- Add `WeatherSet.impute()` in `metdatapy/core.py` as the façade.
- Create or update:
  - `imputed`
  - `impute_method`
- Make the output compatible with existing NetCDF export support in `metdatapy/io.py`.

**Acceptance criteria**
- Imputed rows are traceable.
- Original non-imputed rows remain clearly distinguishable.
- Multiple methods behave deterministically.

**Tests**
- Add a new `tests/test_impute.py` covering:
  - each supported method
  - provenance columns
  - behavior with gaps and existing missing values

### Task 12: Integrate imputation into reproducibility and CLI

**Primary files**
- `metdatapy/manifest.py`
- `metdatapy/cli.py`
- `tests/test_manifest.py`
- `tests/test_cli.py`

**Implementation**
- Record imputation steps cleanly in `ManifestBuilder` pipeline steps and metadata.
- Add a CLI command, preferably under a new `prep` group:
  - `mdp prep impute`
- The command should:
  - read parquet
  - impute
  - write parquet
  - optionally emit a JSON summary

**Acceptance criteria**
- Imputation done via CLI is reproducible and manifest-friendly.
- Output preserves `imputed` and `impute_method`.

**Tests**
- Add CLI regressions in `tests/test_cli.py`.
- Add manifest integration regressions in `tests/test_manifest.py`.

## v1.4.0: Exogenous Feature Engineering

### Goal

Implement the most natural next-step features already implied by the package direction and optional dependencies.

### Task 13: Implement solar-position features

**Primary files**
- `metdatapy/features.py` or `metdatapy/exogenous.py` (new)
- `metdatapy/core.py`
- `tests/test_features.py` (new)
- `docs/weatherset.md`
- `README.md`

**Implementation**
- Use the existing optional `astral` dependency.
- Add a function like `solar_features(index, lat, lon, elev_m=None)` or equivalent.
- Add a `WeatherSet.solar_features(lat, lon, elev_m=None)` façade.
- Produce useful columns such as:
  - solar elevation
  - solar azimuth
  - possibly daylight/night flag

**Acceptance criteria**
- Features are deterministic for known coordinates and timestamps.
- The API fits naturally into the `WeatherSet` pipeline style.

**Tests**
- Add deterministic tests for known dates/times and expected ranges.

### Task 14: Implement holiday features

**Primary files**
- `metdatapy/features.py` or `metdatapy/exogenous.py`
- `metdatapy/core.py`
- `tests/test_features.py`
- `docs/weatherset.md`
- `README.md`

**Implementation**
- Use the existing optional `holidays` dependency.
- Add a function like `holiday_features(index, country, subdiv=None)`.
- Add a `WeatherSet.holiday_features(country, subdiv=None)` façade or a compatible helper.
- Produce at least:
  - `is_holiday`
  - `holiday_name`

**Acceptance criteria**
- Known fixed holidays are detected correctly.
- The feature output aligns cleanly to the UTC index.

**Tests**
- Add tests for known holiday dates.

## v1.5.0: Pipeline Runner and Backtesting

### Goal

Turn the corrected primitives into a declarative, reproducible end-to-end workflow surface.

### Task 15: Build a declarative pipeline runner

**Primary files**
- `metdatapy/pipeline.py` (new)
- `metdatapy/cli.py`
- `metdatapy/manifest.py`
- `tests/test_integration.py`
- `docs/`

**Implementation**
- Create a Pydantic `PipelineConfig` in `metdatapy/pipeline.py`.
- The pipeline runner should orchestrate existing library steps without reimplementing them:
  - ingest
  - mapping
  - unit normalization
  - QC
  - derivation
  - gap insertion
  - resampling
  - calendar features
  - exogenous features
  - imputation
  - supervised-table creation
  - split
  - scaling
  - export
  - manifest generation
- Add CLI support:
  - `mdp pipeline run --config pipeline.yml`

**Acceptance criteria**
- A single config can drive an end-to-end processing run.
- Pipeline output is reproducible and manifest-backed.
- The runner composes existing APIs rather than duplicating logic.

**Tests**
- Add end-to-end config-driven integration tests in `tests/test_integration.py`.

### Task 16: Add rolling-origin backtesting to ML prep

**Primary files**
- `metdatapy/mlprep.py`
- `tests/test_backtesting.py` (new)
- `docs/mlprep.md`

**Implementation**
- Add a function such as:
  - `rolling_time_split()`
  - or `walk_forward_split()`
- It should yield chronological train/validation/test windows with zero overlap and no leakage.
- Make it optionally usable from the pipeline runner config.

**Acceptance criteria**
- Windows are ordered and non-overlapping.
- Boundary behavior is deterministic and well documented.
- The API integrates naturally with `make_supervised()` and `fit_scaler()`.

**Tests**
- Add a new `tests/test_backtesting.py` covering:
  - split boundaries
  - counts
  - leakage prevention

## Release Order

1. Ship `v1.0.1` and `v1.0.2` before feature work.
2. Ship `v1.1.0` next because timezone correctness affects every downstream artifact.
3. Ship `v1.2.0` before model-facing feature work so derived metrics and resampling are physically correct.
4. Ship `v1.3.0` and `v1.4.0` next as the most natural product extensions.
5. Ship `v1.5.0` last after the primitives are corrected and stable.

## Summary by Release

- `v1.0.1`
  - ingest mapping correctness
  - shared CSV loading
  - template and manifest edge-case cleanup
- `v1.0.2`
  - gap insertion correctness
  - flatline QC correctness
  - explicit QC propagation during resample
- `v1.1.0`
  - timezone-aware mapping
  - NetCDF instant preservation
- `v1.2.0`
  - thermal-index correctness
  - circular wind-direction aggregation
  - domain-aware consistency QC
- `v1.3.0`
  - imputation with provenance
  - CLI and manifest integration
- `v1.4.0`
  - solar-position features
  - holiday features
- `v1.5.0`
  - declarative pipeline runner
  - rolling-origin backtesting
