 import json
 from pathlib import Path

 import click
 import pandas as pd

 from .mapper import Detector, Mapper
 from .core import WeatherSet
 from .io import to_parquet


 @click.group()
 def main():
     """MetDataPy command-line interface."""
     pass


 @main.group()
 def ingest():
     """Ingestion helpers."""
     pass


 @ingest.command("detect")
 @click.option("--csv", "csv_path", required=True, type=click.Path(exists=True, dir_okay=False))
 @click.option("--save", "save_path", required=False, type=click.Path(dir_okay=False))
 @click.option("--yes", is_flag=True, help="Accept detected mapping without interactive editing")
 def ingest_detect(csv_path: str, save_path: str | None, yes: bool):
     det = Detector()
     # Read a sample for column choices
     df_head = pd.read_csv(csv_path, nrows=200)
     mapping = det.detect(df_head)

     if not yes:
         mapping = _interactive_mapping_wizard(mapping, list(df_head.columns))

     click.echo(json.dumps(mapping, indent=2))
     if save_path:
         Mapper.save(mapping, save_path)
         click.echo(f"Saved mapping to {save_path}")


 def _interactive_mapping_wizard(mapping: dict, columns: list[str]) -> dict:
     """Interactive confirm/edit flow for detected mapping."""
     from .mapper import CANONICAL_FIELDS

     click.echo("Interactive mapping wizard (press Enter to accept defaults). Type 'none' to unset.")

     # Timestamp column
     ts_current = (mapping.get("ts") or {}).get("col")
     col_choices = [str(c) for c in columns]
     if ts_current is None:
         ts_current = col_choices[0] if col_choices else None
     ts_selected = click.prompt(
         "Timestamp column",
         default=ts_current or "",
         show_default=True,
     ).strip()
     if ts_selected.lower() == "none" or ts_selected == "":
         mapping["ts"] = {"col": None}
     else:
         mapping["ts"] = {"col": ts_selected}

     # Ensure fields dict exists
     if "fields" not in mapping or mapping["fields"] is None:
         mapping["fields"] = {}

     # Loop over canonical fields (union with detected keys)
     canonical_all = list({*CANONICAL_FIELDS, *mapping["fields"].keys()})
     for canon in canonical_all:
         current = mapping["fields"].get(canon, {})
         cur_col = current.get("col") or ""
         cur_unit = (current.get("unit") or "")
         conf = current.get("confidence")
         if conf is not None:
             click.echo(f"\n{canon}: (confidence={conf})")
         else:
             click.echo(f"\n{canon}:")
         new_col = click.prompt(
             f"  Source column for {canon}",
             default=cur_col,
             show_default=True,
         ).strip()
         if new_col.lower() == "none":
             if canon in mapping["fields"]:
                 del mapping["fields"][canon]
             continue
         if new_col:
             # Ask for unit if applicable
             new_unit = click.prompt(
                 f"  Unit for {canon} (e.g., C, F, m/s, km/h, hpa, mm)",
                 default=cur_unit,
                 show_default=True,
             ).strip()
             entry = {"col": new_col}
             if new_unit:
                 entry["unit"] = new_unit
             # Preserve confidence if present
             if conf is not None:
                 entry["confidence"] = conf
             mapping["fields"][canon] = entry

     return mapping


 @ingest.command("apply")
 @click.option("--csv", "csv_path", required=True, type=click.Path(exists=True, dir_okay=False))
 @click.option("--map", "map_path", required=True, type=click.Path(exists=True, dir_okay=False))
 @click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False))
 def ingest_apply(csv_path: str, map_path: str, out_path: str):
     mapping = Mapper.load(map_path)
     df = pd.read_csv(csv_path)
     ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
     to_parquet(ws.to_dataframe(), out_path)
     click.echo(f"Wrote {out_path}")


 @main.group()
 def qc():
     """Quality control commands."""
     pass


 @qc.command("run")
 @click.option("--in", "in_path", required=True, type=click.Path(exists=True, dir_okay=False))
 @click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False))
 @click.option("--report", "report_path", required=False, type=click.Path(dir_okay=False))
 def qc_run(in_path: str, out_path: str, report_path: str | None):
     df = pd.read_parquet(in_path)
     ws = WeatherSet(df).qc_range()
     out_df = ws.to_dataframe()
     out_df.to_parquet(out_path)
     click.echo(f"Wrote {out_path}")
     if report_path:
         # Minimal report: counts of range flags
         report = {}
         for col in out_df.columns:
             if col.startswith("qc_"):
                 report[col] = int(out_df[col].fillna(False).sum())
         Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
         click.echo(f"Saved report to {report_path}")


 @ingest.command("template")
 @click.option("--out", "out_path", required=False, type=click.Path(dir_okay=False))
 @click.option("--minimal", is_flag=True, help="Exclude optional fields from template")
 def ingest_template(out_path: str | None, minimal: bool):
     from .mapper import Mapper
     tpl = Mapper.template(include_optional=not minimal)
     s = json.dumps(tpl, indent=2)
     if out_path:
         Path(out_path).write_text(s, encoding="utf-8")
         click.echo(f"Wrote mapping template to {out_path}")
     else:
         click.echo(s)


