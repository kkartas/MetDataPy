"""
Complete MetDataPy Workflow Example
====================================

This script demonstrates the full MetDataPy pipeline:
1. Data ingestion with automatic mapping
2. Quality control
3. Derived metrics
4. Data preparation
5. ML-ready dataset creation
6. Export

Usage:
    python complete_workflow.py

Requirements:
    pip install -e ..
    pip install matplotlib

License: MIT
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metdatapy.core import WeatherSet
from metdatapy.mapper import Detector, Mapper
from metdatapy.mlprep import make_supervised, time_split, fit_scaler, apply_scaler

# Configuration
DATA_PATH = Path("../data/sample_weather_2024.csv")
OUTPUT_DIR = Path("../data/processed")
MAPPING_PATH = Path("../data/mapping.yml")

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def main():
    print("=" * 70)
    print("MetDataPy Complete Workflow Example")
    print("=" * 70)

    # Step 1: Load raw data
    print("\n[1/7] Loading raw data...")
    df_raw = pd.read_csv(DATA_PATH)
    print(f"  [OK] Loaded {len(df_raw):,} records")
    print(f"  [OK] Columns: {list(df_raw.columns)}")

    # Step 2: Automatic column mapping
    print("\n[2/7] Detecting column mapping...")
    detector = Detector()
    mapping = detector.detect(df_raw)
    print(f"  [OK] Timestamp: {mapping['ts']['col']}")
    print(f"  [OK] Detected {len(mapping['fields'])} fields:")
    for canonical, info in mapping['fields'].items():
        print(f"      {canonical:15s} <- {info['col']:30s} (conf: {info['confidence']:.2f})")
    
    # Save mapping
    Mapper.save(mapping, MAPPING_PATH)
    print(f"  [OK] Saved mapping to {MAPPING_PATH}")

    # Step 3: Create WeatherSet and normalize
    print("\n[3/7] Creating WeatherSet and normalizing units...")
    ws = WeatherSet.from_mapping(df_raw, mapping)
    ws = ws.to_utc().normalize_units(mapping)
    print(f"  [OK] Converted to UTC and normalized units (F->C, mph->m/s)")

    # Step 4: Quality Control
    print("\n[4/7] Running quality control checks...")
    ws = ws.qc_range()
    ws = ws.qc_spike()  # Uses default window=5, threshold=6.0
    ws = ws.qc_flatline()  # Uses default window=5, tolerance=1e-6
    ws = ws.qc_consistency()
    
    df_qc = ws.to_dataframe()
    qc_cols = [col for col in df_qc.columns if col.startswith('qc_')]
    print(f"  [OK] QC Summary:")
    for col in qc_cols:
        count = df_qc[col].sum()
        pct = 100 * count / len(df_qc)
        if count > 0:
            print(f"      {col:30s}: {count:5d} flags ({pct:5.2f}%)")

    # Step 5: Derive metrics
    print("\n[5/7] Calculating derived metrics...")
    ws = ws.derive(['dew_point', 'vpd', 'heat_index', 'wind_chill'])
    print(f"  [OK] Added: dew_point_c, vpd_kpa, heat_index_c, wind_chill_c")

    # Step 6: Data preparation
    print("\n[6/7] Preparing data...")
    ws = ws.insert_missing(frequency='10min')
    df_gaps = ws.to_dataframe()
    n_gaps = df_gaps['gap'].sum() if 'gap' in df_gaps.columns else 0
    print(f"  [OK] Marked {n_gaps} gaps ({100*n_gaps/len(df_gaps):.2f}%)")
    
    ws = ws.resample('1H')
    print(f"  [OK] Resampled to hourly: {len(ws.to_dataframe())} records")
    
    ws = ws.calendar_features(cyclical=True)
    print(f"  [OK] Added calendar features (hour, weekday, month, cyclical encodings)")

    # Get clean DataFrame
    df_clean = ws.to_dataframe()
    
    # Save clean data
    clean_path = OUTPUT_DIR / "weather_clean_hourly.parquet"
    df_clean.to_parquet(clean_path)
    print(f"  [OK] Saved clean data to {clean_path}")

    # Step 7: ML Preparation
    print("\n[7/7] Preparing ML-ready datasets...")
    
    # Select features (check what's available)
    available_cols = df_clean.columns.tolist()
    feature_cols = []
    for col in ['temp_c', 'rh_pct', 'pres_hpa', 'wspd_ms', 'solar_wm2',
                'dew_point_c', 'vpd_kpa', 'hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']:
        if col in available_cols:
            feature_cols.append(col)
    df_ml = df_clean[feature_cols].copy()
    
    # Create supervised dataset
    df_supervised = make_supervised(
        df_ml,
        targets=['temp_c'],
        lags=[1, 2, 3, 6, 12, 24],
        horizons=[1, 3, 6],
        drop_na=True
    )
    print(f"  [OK] Created supervised dataset: {df_supervised.shape}")
    
    # Time-safe split
    train_end = pd.Timestamp('2024-09-30', tz='UTC')
    val_end = pd.Timestamp('2024-10-31', tz='UTC')
    splits = time_split(df_supervised, train_end, val_end)
    train_df, val_df, test_df = splits['train'], splits['val'], splits['test']
    print(f"  [OK] Train: {len(train_df):5d} | Val: {len(val_df):5d} | Test: {len(test_df):5d}")
    
    # Scale features
    scaler_params = fit_scaler(train_df, method='standard')
    train_scaled = apply_scaler(train_df, scaler_params)
    val_scaled = apply_scaler(val_df, scaler_params)
    test_scaled = apply_scaler(test_df, scaler_params)
    print(f"  [OK] Applied StandardScaler (fitted on train only)")
    
    # Save ML datasets
    train_scaled.to_parquet(OUTPUT_DIR / "train_scaled.parquet")
    val_scaled.to_parquet(OUTPUT_DIR / "val_scaled.parquet")
    test_scaled.to_parquet(OUTPUT_DIR / "test_scaled.parquet")
    
    # Save scaler parameters
    with open(OUTPUT_DIR / "scaler_params.json", 'w') as f:
        json.dump(scaler_params.__dict__, f, indent=2)
    
    print(f"  [OK] Saved ML datasets to {OUTPUT_DIR}")
    print(f"  [OK] Saved scaler parameters to {OUTPUT_DIR / 'scaler_params.json'}")

    # Summary
    print("\n" + "=" * 70)
    print("Workflow Complete!")
    print("=" * 70)
    print(f"\nOutputs:")
    print(f"  - Mapping:       {MAPPING_PATH}")
    print(f"  - Clean data:    {OUTPUT_DIR / 'weather_clean_hourly.parquet'}")
    print(f"  - Train set:     {OUTPUT_DIR / 'train_scaled.parquet'}")
    print(f"  - Val set:       {OUTPUT_DIR / 'val_scaled.parquet'}")
    print(f"  - Test set:      {OUTPUT_DIR / 'test_scaled.parquet'}")
    print(f"  - Scaler params: {OUTPUT_DIR / 'scaler_params.json'}")
    print(f"\nNext steps:")
    print(f"  - Train ML models on the prepared datasets")
    print(f"  - Explore QC flags and adjust thresholds")
    print(f"  - Add exogenous variables (holidays, solar position)")
    print(f"  - Export to NetCDF for climate applications")


if __name__ == "__main__":
    main()

