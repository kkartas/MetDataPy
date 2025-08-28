# WeatherSet

`WeatherSet` wraps a `pandas.DataFrame` normalized to the canonical schema and indexed by `ts_utc`.

## Construction
```python
WeatherSet.from_mapping(df, mapping)
WeatherSet.from_csv(path, mapping)
```
- Sets UTC datetime index and selects mapped fields.

## Unit normalization
```python
ws.normalize_units(mapping)
```
- Converts known fields to canonical units (`F→C`, `mph/km/h→m/s`, `mbar/Pa→hPa`, `inch→mm`).

## Missing rows and gaps
```python
ws.insert_missing(frequency=None)
```
- Infers frequency (or use `frequency`) and reindexes.
- Adds/updates `gap` where rows were inserted.

## Rain accumulation fix-up
```python
ws.fix_accum_rain()
```
- Converts accumulated rain counters to event totals, handling rollovers and clamping negative noise to 0.

## QC
```python
ws.qc_range()
```
- Adds `qc_<var>_range` flags per plausible bounds.

## Derived metrics
```python
ws.derive(["dew_point", "vpd"])
```
- Adds `dew_point_c`, `vpd_kpa` when `temp_c` and `rh_pct` are present.

## Resample and aggregate
```python
ws.resample("1H", agg={...})
```
- Aggregates with sensible defaults (means for state variables, `sum` for `rain_mm`, `max` for `gust_ms`).
- Propagates `gap` as `any` across the window.

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
