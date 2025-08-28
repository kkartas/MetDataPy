# Mapper & Detector

## Mapping format (YAML)
```yaml
version: 1
ts:
  col: DateTime
fields:
  temp_c: { col: "Temperature (°C)", unit: C }
  rh_pct:  { col: "RH (%)" }
  wspd_ms: { col: "Wind Speed (m/s)", unit: m/s }
```

- `ts.col` is required; fields map to source column names and optional `unit` hints.

## Autodetection heuristics
- Timestamp scored by name hints, parse success rate, and monotonicity.
- Field score combines:
  - Name match on regex patterns (e.g., `temp|temperature`, `rh|humid`, `press|baro`)
  - Unit hints from header text (e.g., `°F`, `mph`, `mbar`)
  - Range plausibility against canonical bounds; unit is inferred by maximizing in-bounds fraction
- Confidence = name (0–0.4) + unit hint bonus (0.1) + 0.6 × plausibility, with a small bump when both name and plausibility are strong.

## Interactive wizard
- For each canonical field, select a source column and unit. Type `none` to unset.
- Confidences (when available) are displayed to guide adjustments.
