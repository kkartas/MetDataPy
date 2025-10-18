import pandas as pd
import tempfile
from pathlib import Path
from metdatapy.manifest import (
    Manifest,
    ManifestBuilder,
    DatasetInfo,
    PipelineStep,
    FeatureInfo,
    QCReport,
    ScalerParamsModel,
    SplitBoundaries,
    validate_manifest,
)


def test_manifest_builder():
    """Test building a manifest incrementally."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0, 12.0],
        "rh_pct": [50.0, 55.0, 60.0],
        "qc_temp_c_range": [False, False, True],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"], utc=True))
    
    builder = ManifestBuilder(source="test_data.csv")
    builder.set_dataset_info(df, frequency="1D")
    builder.add_step("load", "WeatherSet.from_csv", {"path": "test_data.csv"})
    builder.add_step("qc", "WeatherSet.qc_range", {})
    builder.set_qc_report(df)
    
    manifest = builder.build()
    
    assert manifest.dataset.rows == 3
    assert manifest.dataset.source == "test_data.csv"
    assert len(manifest.pipeline_steps) == 2
    assert manifest.qc_report is not None
    assert manifest.qc_report.total_flags == 1
    assert manifest.pipeline_hash != ""


def test_manifest_save_load():
    """Test saving and loading manifests."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02"], utc=True))
    
    builder = ManifestBuilder(source="test.csv")
    builder.set_dataset_info(df)
    manifest = builder.build()
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        manifest.to_json(tmp_path)
        loaded = Manifest.from_json(tmp_path)
        
        assert loaded.dataset.rows == manifest.dataset.rows
        assert loaded.pipeline_hash == manifest.pipeline_hash
        assert loaded.metdatapy_version == manifest.metdatapy_version
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_manifest_with_scaler():
    """Test manifest with scaler parameters."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0, 12.0],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"], utc=True))
    
    builder = ManifestBuilder(source="test.csv")
    builder.set_dataset_info(df)
    
    scaler = ScalerParamsModel(
        method="standard",
        columns=["temp_c"],
        parameters={"temp_c": {"mean": 11.0, "scale": 1.0}}
    )
    builder.set_scaler(scaler)
    
    manifest = builder.build()
    
    assert manifest.scaler is not None
    assert manifest.scaler.method == "standard"
    assert "temp_c" in manifest.scaler.columns


def test_manifest_with_split():
    """Test manifest with split boundaries."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0, 12.0],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"], utc=True))
    
    builder = ManifestBuilder(source="test.csv")
    builder.set_dataset_info(df)
    
    split = SplitBoundaries(
        train_start="2025-01-01T00:00:00Z",
        train_end="2025-01-02T00:00:00Z",
        test_start="2025-01-02T00:00:00Z",
        test_end="2025-01-03T00:00:00Z",
    )
    builder.set_split(split)
    
    manifest = builder.build()
    
    assert manifest.split is not None
    assert manifest.split.train_start == "2025-01-01T00:00:00Z"
    assert manifest.split.test_end == "2025-01-03T00:00:00Z"


def test_validate_manifest():
    """Test manifest validation."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02"], utc=True))
    
    builder = ManifestBuilder(source="test.csv")
    builder.set_dataset_info(df)
    builder.add_step("load", "load_data", {})
    manifest = builder.build()
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        manifest.to_json(tmp_path)
        results = validate_manifest(tmp_path)
        
        assert results["valid"] is True
        assert results["pipeline_steps"] == 1
        assert results["pipeline_hash"] == manifest.pipeline_hash
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_manifest_reproducibility():
    """Test manifest reproducibility comparison."""
    df = pd.DataFrame({
        "temp_c": [10.0, 11.0],
    }, index=pd.to_datetime(["2025-01-01", "2025-01-02"], utc=True))
    
    # Create two identical manifests
    builder1 = ManifestBuilder(source="test.csv")
    builder1.set_dataset_info(df)
    builder1.add_step("load", "load_data", {"param": 1})
    manifest1 = builder1.build()
    
    builder2 = ManifestBuilder(source="test.csv")
    builder2.set_dataset_info(df)
    builder2.add_step("load", "load_data", {"param": 1})
    manifest2 = builder2.build()
    
    results = manifest1.validate_reproducibility(manifest2)
    
    assert results["same_pipeline"] is True
    assert results["same_features"] is True

