# Quality Control

## Plausible range checks
- `temp_c`: -40 … 55 °C
- `rh_pct`: 0 … 100 %
- `pres_hpa`: 870 … 1085 hPa
- `wspd_ms`: 0 … 75 m/s
- `wdir_deg`: 0 … 360°
- `gust_ms`: 0 … 100 m/s
- `rain_mm`: 0 … 1000 mm
- `solar_wm2`: 0 … 1500 W/m²
- `uv_index`: 0 … 20

Flags are written as boolean `qc_<var>_range`.

Planned checks: spike/MAD, flatline, cross-variable consistency (e.g., dew point ≤ temp).
