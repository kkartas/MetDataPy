# WeatherSet

`WeatherSet` wraps a `pandas.DataFrame` normalized to the canonical schema and indexed by `ts_utc`.

## Construction
```python
WeatherSet.from_mapping(df, mapping)
WeatherSet.from_csv(path, mapping)
```
- Sets UTC datetime index and selects mapped fields.
- Honors `ts.timezone` in the mapping (v1.1.0+). Naive source timestamps are localized to the
  declared IANA zone and then converted to UTC; tz-aware timestamps are always converted to UTC
  and the hint is ignored.
- If the source timestamps are naive and no `ts.timezone` is declared, the values are assumed to
  be UTC and a `UserWarning` is emitted. Set `ts.timezone` explicitly to silence it and to
  guarantee the intended conversion.

## Unit normalization
```python
ws.normalize_units(mapping)
```
- Converts known fields to canonical units (`F→C`, `mph/km/h→m/s`, `mbar/Pa→hPa`, `inch→mm`).

## Missing rows and gaps
```python
ws.insert_missing(frequency=None)
```
- If `frequency` is omitted, infers the cadence from the index using the **mode** of inter-observation deltas. This tolerates gapped series — e.g. `00:00, 02:00, 03:00` correctly infers an hourly cadence and inserts the missing `01:00` row.
- Only skips reindexing when no usable frequency can be derived.
- Adds/updates a boolean `gap` column: `True` for rows that were inserted.

## Rain accumulation fix-up
```python
ws.fix_accum_rain()
```
- Converts accumulated rain counters to event totals, handling rollovers and clamping negative noise to 0.

## Quality control
```python
ws.qc_range()       # plausible range flags → qc_<var>_range
ws.qc_spike()       # MAD-based spike flags → qc_<var>_spike
ws.qc_flatline()    # stuck-sensor flags   → qc_<var>_flatline
ws.qc_consistency() # cross-variable checks → qc_consistency + qc_any
```
- All checks are non-destructive; they add boolean `qc_*` columns without modifying original data.
- See [Quality Control](qc.md) for full details on each check.

## Derived metrics
```python
ws.derive(["dew_point", "vpd", "heat_index", "wind_chill"])
```
- Adds `dew_point_c`, `vpd_kpa`, `heat_index_c`, `wind_chill_c` when required source columns are present.

## Resample and aggregate
```python
ws.resample("1h", agg={...})
```
- Aggregates with sensible defaults (means for state variables, `sum` for `rain_mm`, `max` for `gust_ms`).
- `gap` is propagated as `True` if any row in the window was a gap.
- All `qc_*` columns are propagated with **OR semantics** — the output flag is `True` if any row in the window was flagged. Raises `TypeError` for `qc_*` columns with unsupported dtypes.

## Calendar features
```python
ws.calendar_features(cyclical=True)
```
- Adds `hour`, `weekday`, `month` and cyclical encodings (`hour_sin/cos`, `doy_sin/cos`).

## Exogenous joins
```python
ws.add_exogenous(exo_df)
```
- Joins additional covariates by UTC index.
