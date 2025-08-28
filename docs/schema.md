# Canonical Schema

- Index: `ts_utc` (UTC datetime, monotonic, no duplicates)

## Core variables (metric units)
- `temp_c` (°C)
- `rh_pct` (%)
- `pres_hpa` (hPa)
- `wspd_ms` (m/s)
- `wdir_deg` (degrees)
- `gust_ms` (m/s)
- `rain_mm` (mm, event/period totals after fix-up)

Optional:
- `solar_wm2` (W/m²)
- `uv_index` (unitless)

## Flags
- `qc_<var>_range`: boolean, out-of-plausible-bounds
- future: `qc_<var>_spike`, `qc_<var>_flatline`, `qc_consistency`
- `gap`: boolean, True when inserted row was missing in original index

## Meta (planned)
- `station_id`, `lat`, `lon`, `elev_m`, `source`, `version`, `pipeline_hash`
