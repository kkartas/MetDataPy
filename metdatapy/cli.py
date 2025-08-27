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
 def ingest_detect(csv_path: str, save_path: str | None):
     det = Detector()
     mapping = det.detect_from_csv(csv_path)
     click.echo(json.dumps(mapping, indent=2))
     if save_path:
         Mapper.save(mapping, save_path)
         click.echo(f"Saved mapping to {save_path}")


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


