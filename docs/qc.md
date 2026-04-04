# Quality Control

All QC functions add boolean flag columns to the DataFrame without modifying original values. `True` means the check failed for that row.

## Range checks — `qc_range`

Flags values outside climatologically plausible bounds.

| Variable | Min | Max |
|---|---|---|
| `temp_c` | -40 °C | 55 °C |
| `rh_pct` | 0 % | 100 % |
| `pres_hpa` | 870 hPa | 1085 hPa |
| `wspd_ms` | 0 m/s | 75 m/s |
| `wdir_deg` | 0° | 360° |
| `gust_ms` | 0 m/s | 100 m/s |
| `rain_mm` | 0 mm | 1000 mm |
| `solar_wm2` | 0 W/m² | 1500 W/m² |
| `uv_index` | 0 | 20 |

Output columns: `qc_<var>_range` (one per variable present).

```python
from metdatapy.qc import qc_range
df = qc_range(df)
# or via WeatherSet
ws.qc_range()
```

## Spike detection — `qc_spike`

Flags sudden spikes using a rolling Median Absolute Deviation (MAD) z-score. More robust to outliers than standard-deviation methods.

**Algorithm:**
1. Rolling median over `window` (default 9), `min_periods=3`
2. Rolling MAD over the same window
3. `z = |x − median| / (1.4826 × MAD + ε)`
4. Flag where `z > thresh` (default 6.0)

Output columns: `qc_<var>_spike`.

```python
from metdatapy.qc import qc_spike
df = qc_spike(df, window=9, thresh=6.0)
# or
ws.qc_spike()
```

## Flatline detection — `qc_flatline`

Flags stuck or frozen sensor readings — periods with suspiciously low rolling variance.

**Behaviour (v1.0.2):**
- Uses `min_periods = max(3, window // 2 + 1)` so short series and NaN-dominated windows are not flagged.
- Only flags when variance is genuinely at or below `tol` **and** is not NaN. A window with insufficient valid observations produces NaN variance, which is not treated as zero.

Output columns: `qc_<var>_flatline`.

```python
from metdatapy.qc import qc_flatline
df = qc_flatline(df, window=5, tol=0.0)   # tol=0 flags perfect flatlines only
df = qc_flatline(df, window=5, tol=1e-6)  # flag near-constant values
# or
ws.qc_flatline()
```

## Consistency checks — `qc_consistency`

Flags violations of physical relationships between variables.

| Check | Condition flagged |
|---|---|
| Dew point vs temperature | `dew_point_c > temp_c` |
| Wind chill vs temperature | `wind_chill_c > temp_c` |
| Heat index vs temperature | `heat_index_c < temp_c` |
| Wind direction when calm | `wdir_deg` is not NaN when `wspd_ms ≤ 0.2 m/s` |

Only checks for variables present in the DataFrame are applied. Output column: `qc_consistency`.

```python
from metdatapy.qc import qc_consistency
df = qc_consistency(df)
# or
ws.qc_consistency()  # also adds qc_any
```

## Aggregate flag — `qc_any`

Combines all `qc_*` columns into a single `qc_any` flag (`True` if any check failed).

```python
from metdatapy.qc import qc_any
df = qc_any(df)

# Filter to clean rows only
clean = df[df["qc_any"] == False]
```

`WeatherSet.qc_consistency()` calls `qc_any` automatically. To aggregate after running checks individually:

```python
ws.qc_range().qc_spike().qc_flatline()
df = qc_any(ws.to_dataframe())
```
