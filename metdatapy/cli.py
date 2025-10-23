import json
from pathlib import Path
from typing import List, Optional

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
def ingest_detect(csv_path: str, save_path: Optional[str], yes: bool):
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


def _interactive_mapping_wizard(mapping: dict, columns: List[str]) -> dict:
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
@click.option("--config", "config_path", required=False, type=click.Path(exists=True, dir_okay=False), help="YAML/JSON thresholds for QC")
def qc_run(in_path: str, out_path: str, report_path: Optional[str], config_path: Optional[str]):
     df = pd.read_parquet(in_path)
     ws = WeatherSet(df)
     cfg = None
     if config_path:
         text = Path(config_path).read_text(encoding="utf-8")
         try:
             import yaml as _yaml
             cfg = _yaml.safe_load(text)
         except Exception:
             try:
                 cfg = json.loads(text)
             except Exception:
                 cfg = None
     ws = ws.qc_range()
     from .qc import qc_spike as _sp, qc_flatline as _fl
     sp = cfg.get("spike", {}) if isinstance(cfg, dict) else {}
     fl = cfg.get("flatline", {}) if isinstance(cfg, dict) else {}
     ws.df = _sp(ws.df, window=int(sp.get("window", 9)), thresh=float(sp.get("thresh", 6.0)))
     ws.df = _fl(ws.df, window=int(fl.get("window", 5)), tol=float(fl.get("tol", 0.0)))
     ws = ws.qc_consistency()
     out_df = ws.to_dataframe()
     out_df.to_parquet(out_path)
     click.echo(f"Wrote {out_path}")
     if report_path:
         report = {}
         for col in out_df.columns:
             if col.startswith("qc_"):
                 report[col] = int(out_df[col].fillna(False).sum())
         Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
         click.echo(f"Saved report to {report_path}")


@ingest.command("template")
@click.option("--out", "out_path", required=False, type=click.Path(dir_okay=False))
@click.option("--minimal", is_flag=True, help="Exclude optional fields from template")
def ingest_template(out_path: Optional[str], minimal: bool):
    from .mapper import Mapper
    tpl = Mapper.template(include_optional=not minimal)
    s = json.dumps(tpl, indent=2)
    if out_path:
        Path(out_path).write_text(s, encoding="utf-8")
        click.echo(f"Wrote mapping template to {out_path}")
    else:
        click.echo(s)


@main.group()
def manifest():
    """Manifest and reproducibility commands."""
    pass


@manifest.command("validate")
@click.argument("manifest_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
def manifest_validate(manifest_path: str, verbose: bool):
    """Validate a manifest.json file."""
    from .manifest import validate_manifest
    
    click.echo(f"Validating manifest: {manifest_path}")
    results = validate_manifest(manifest_path)
    
    if results["valid"]:
        click.secho("✓ Manifest is valid", fg="green", bold=True)
        
        if verbose:
            click.echo(f"\nManifest Details:")
            click.echo(f"  Version: {results['version']}")
            click.echo(f"  MetDataPy Version: {results['metdatapy_version']}")
            click.echo(f"  Pipeline Steps: {results['pipeline_steps']}")
            click.echo(f"  Pipeline Hash: {results['pipeline_hash']}")
            click.echo(f"  Has QC Report: {results['has_qc_report']}")
            click.echo(f"  Has Scaler: {results['has_scaler']}")
            click.echo(f"  Has Split: {results['has_split']}")
        
        if results.get("warnings"):
            click.echo(f"\nWarnings:")
            for warning in results["warnings"]:
                click.secho(f"  ⚠ {warning}", fg="yellow")
    else:
        click.secho("✗ Manifest is invalid", fg="red", bold=True)
        if results.get("errors"):
            click.echo(f"\nErrors:")
            for error in results["errors"]:
                click.secho(f"  ✗ {error}", fg="red")
        raise click.Abort()


@manifest.command("show")
@click.argument("manifest_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--format", "output_format", type=click.Choice(["json", "yaml", "summary"]), default="summary")
def manifest_show(manifest_path: str, output_format: str):
    """Display manifest contents."""
    from .manifest import Manifest
    
    m = Manifest.from_json(manifest_path)
    
    if output_format == "json":
        click.echo(json.dumps(m.model_dump(), indent=2))
    elif output_format == "yaml":
        import yaml
        click.echo(yaml.dump(m.model_dump(), sort_keys=False))
    else:  # summary
        click.echo(f"Manifest Summary")
        click.echo(f"{'=' * 60}")
        click.echo(f"Created: {m.created_at}")
        click.echo(f"MetDataPy Version: {m.metdatapy_version}")
        click.echo(f"Pipeline Hash: {m.pipeline_hash}")
        
        click.echo(f"\nDataset:")
        click.echo(f"  Source: {m.dataset.source}")
        click.echo(f"  Rows: {m.dataset.rows:,}")
        click.echo(f"  Columns: {len(m.dataset.columns)}")
        click.echo(f"  Time Range: {m.dataset.start_time} to {m.dataset.end_time}")
        if m.dataset.frequency:
            click.echo(f"  Frequency: {m.dataset.frequency}")
        
        click.echo(f"\nPipeline Steps ({len(m.pipeline_steps)}):")
        for i, step in enumerate(m.pipeline_steps, 1):
            duration = f" ({step.duration_seconds:.2f}s)" if step.duration_seconds else ""
            click.echo(f"  {i}. {step.function}{duration}")
        
        click.echo(f"\nFeatures:")
        click.echo(f"  Original: {len(m.features.original_features)}")
        click.echo(f"  Derived: {len(m.features.derived_features)}")
        click.echo(f"  Lag: {len(m.features.lag_features)}")
        click.echo(f"  Calendar: {len(m.features.calendar_features)}")
        click.echo(f"  Target: {len(m.features.target_features)}")
        
        if m.qc_report:
            click.echo(f"\nQuality Control:")
            click.echo(f"  Total Flags: {m.qc_report.total_flags:,}")
            click.echo(f"  Flagged: {m.qc_report.flagged_percentage:.2f}%")
            if m.qc_report.flags_by_type:
                click.echo(f"  By Type:")
                for flag_type, count in sorted(m.qc_report.flags_by_type.items()):
                    click.echo(f"    {flag_type}: {count:,}")
        
        if m.scaler:
            click.echo(f"\nScaler:")
            click.echo(f"  Method: {m.scaler.method}")
            click.echo(f"  Columns: {len(m.scaler.columns)}")
        
        if m.split:
            click.echo(f"\nSplit Boundaries:")
            click.echo(f"  Train: {m.split.train_start} to {m.split.train_end}")
            if m.split.val_start:
                click.echo(f"  Val: {m.split.val_start} to {m.split.val_end}")
            if m.split.test_start:
                click.echo(f"  Test: {m.split.test_start} to {m.split.test_end}")


@manifest.command("compare")
@click.argument("manifest1", type=click.Path(exists=True, dir_okay=False))
@click.argument("manifest2", type=click.Path(exists=True, dir_okay=False))
def manifest_compare(manifest1: str, manifest2: str):
    """Compare two manifests for reproducibility."""
    from .manifest import Manifest
    
    m1 = Manifest.from_json(manifest1)
    m2 = Manifest.from_json(manifest2)
    
    results = m1.validate_reproducibility(m2)
    
    click.echo(f"Comparing Manifests")
    click.echo(f"{'=' * 60}")
    click.echo(f"Manifest 1: {manifest1}")
    click.echo(f"Manifest 2: {manifest2}")
    click.echo()
    
    all_match = all(results.values())
    
    for check, passed in results.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "red"
        click.secho(f"{status} {check.replace('_', ' ').title()}", fg=color)
    
    click.echo()
    if all_match:
        click.secho("✓ Manifests are compatible for reproducibility", fg="green", bold=True)
    else:
        click.secho("✗ Manifests differ - results may not be reproducible", fg="yellow", bold=True)


