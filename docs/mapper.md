# Mapper & Detector

## Mapping format (YAML)
```yaml
version: 1
ts:
  col: DateTime
  timezone: US/Eastern   # optional; IANA tz name for naive source timestamps
fields:
  temp_c: { col: "Temperature (°C)", unit: C }
  rh_pct:  { col: "RH (%)" }
  wspd_ms: { col: "Wind Speed (m/s)", unit: m/s }
  rain_rate_mmh: { col: "Rain Rate (mm/h)", unit: mm/h }
```

- `ts.col` is required; fields map to source column names and optional `unit` hints.
- `ts.timezone` is optional. When set, naive source timestamps are first localized
  to that timezone and then converted to UTC. Tz-aware source timestamps are always converted
  to UTC and the hint is ignored. If the source timestamps are naive and no `timezone` is
  set, the value is assumed to already be UTC and a `UserWarning` is emitted.

## Autodetection heuristics
- Timestamp scored by name hints, parse success rate, and monotonicity.
- Field score combines:
  - Name match on regex patterns (e.g., `temp|temperature`, `rh|humid`, `press|baro`)
  - Unit hints from header text (e.g., `°F`, `mph`, `mbar`)
  - Range plausibility against canonical bounds; unit is inferred by maximizing in-bounds fraction
- Confidence = name (0–0.4) + unit hint bonus (0.1) + 0.6 × plausibility, with a small bump when both name and plausibility are strong.

**Detection rules (v1.0.1):**
- A canonical field is only emitted when there is real evidence for it — at least one of a name pattern match or a unit hint. Weak or absent evidence means the field is omitted rather than guessed.
- A minimum confidence threshold must be met before a mapping is accepted.
- Each source column is assigned to at most one canonical field. If two canonical fields compete for the same column, the better-supported one wins.

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
Timestamp timezone (e.g. UTC, US/Eastern; blank = naive/UTC) []: US/Eastern
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
