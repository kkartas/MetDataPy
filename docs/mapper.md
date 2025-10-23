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

The interactive mapping wizard allows you to review and refine automatically detected column mappings. To use it, run the detect command without the `--yes` flag:

```bash
mdp ingest detect --csv weather_data.csv --save mapping.yml
```

The wizard will:
1. Display the detected timestamp column and prompt for confirmation
2. For each canonical meteorological field (temp_c, rh_pct, etc.):
   - Show the auto-detected source column with confidence score
   - Prompt you to accept (press Enter) or specify a different column
   - Ask for the unit if applicable (e.g., C, F, m/s, mph)
3. Allow you to type `none` to skip/unmap any field

**Example wizard session:**
```
Interactive mapping wizard (press Enter to accept defaults). Type 'none' to unset.
Timestamp column [DateTime]: ⏎
temp_c: (confidence=0.85)
  Source column for temp_c [Temperature]: ⏎
  Unit for temp_c (e.g., C, F, m/s, km/h, hpa, mm) [C]: ⏎
rh_pct: (confidence=0.92)
  Source column for rh_pct [Humidity]: RelativeHumidity
  Unit for rh_pct (e.g., C, F, m/s, km/h, hpa, mm) [%]: ⏎
```

To skip the wizard and accept auto-detected mappings:
```bash
mdp ingest detect --csv weather_data.csv --save mapping.yml --yes
```
