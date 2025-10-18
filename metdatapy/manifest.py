"""
Manifest generation and validation for reproducibility.

A manifest captures the complete provenance of a data processing pipeline,
including steps, parameters, versions, and transformations applied.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field, field_validator

# Import ScalerParams from mlprep to avoid duplication
# We'll create a Pydantic version for validation
class ScalerParamsModel(BaseModel):
    """Scaler parameters for reproducibility (Pydantic model for validation)."""
    method: str = Field(description="Scaling method: standard, minmax, or robust")
    columns: List[str] = Field(description="Columns that were scaled")
    parameters: Dict[str, Dict[str, float]] = Field(
        description="Per-column scaling parameters (mean, scale, etc.)"
    )


class SplitBoundaries(BaseModel):
    """Time-based split boundaries."""
    train_start: str = Field(description="Training set start timestamp (ISO 8601)")
    train_end: str = Field(description="Training set end timestamp (ISO 8601)")
    val_start: Optional[str] = Field(None, description="Validation set start timestamp")
    val_end: Optional[str] = Field(None, description="Validation set end timestamp")
    test_start: Optional[str] = Field(None, description="Test set start timestamp")
    test_end: Optional[str] = Field(None, description="Test set end timestamp")


class PipelineStep(BaseModel):
    """A single step in the data processing pipeline."""
    step: str = Field(description="Step name/identifier")
    function: str = Field(description="Function or method called")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used")
    timestamp: str = Field(description="When this step was executed (ISO 8601)")
    duration_seconds: Optional[float] = Field(None, description="Execution time")


class DatasetInfo(BaseModel):
    """Information about the dataset."""
    source: str = Field(description="Data source (file path, URL, etc.)")
    rows: int = Field(description="Number of rows")
    columns: List[str] = Field(description="Column names")
    start_time: str = Field(description="First timestamp in dataset")
    end_time: str = Field(description="Last timestamp in dataset")
    frequency: Optional[str] = Field(None, description="Temporal frequency (e.g., '10min', '1H')")
    missing_values: Dict[str, int] = Field(
        default_factory=dict, 
        description="Count of missing values per column"
    )


class QCReport(BaseModel):
    """Quality control summary."""
    total_flags: int = Field(description="Total number of flagged records")
    flags_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of flags by QC check type"
    )
    flagged_percentage: float = Field(description="Percentage of records flagged")


class FeatureInfo(BaseModel):
    """Information about features in the dataset."""
    original_features: List[str] = Field(description="Original input features")
    derived_features: List[str] = Field(default_factory=list, description="Derived features")
    lag_features: List[str] = Field(default_factory=list, description="Lagged features")
    calendar_features: List[str] = Field(default_factory=list, description="Calendar features")
    target_features: List[str] = Field(default_factory=list, description="Target variables")


class Manifest(BaseModel):
    """Complete pipeline manifest for reproducibility."""
    
    version: str = Field(default="1.0", description="Manifest schema version")
    metdatapy_version: str = Field(description="MetDataPy package version")
    created_at: str = Field(description="Manifest creation timestamp (ISO 8601)")
    
    # Dataset information
    dataset: DatasetInfo = Field(description="Input dataset information")
    
    # Pipeline steps
    pipeline_steps: List[PipelineStep] = Field(
        default_factory=list,
        description="Ordered list of processing steps"
    )
    pipeline_hash: str = Field(description="Hash of pipeline configuration for reproducibility")
    
    # Features
    features: FeatureInfo = Field(description="Feature engineering information")
    
    # Quality control
    qc_report: Optional[QCReport] = Field(None, description="Quality control summary")
    
    # ML preparation
    scaler: Optional[ScalerParamsModel] = Field(None, description="Scaler parameters")
    split: Optional[SplitBoundaries] = Field(None, description="Train/val/test split boundaries")
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional user-defined metadata"
    )
    
    @field_validator('created_at', 'dataset', mode='before')
    @classmethod
    def validate_timestamps(cls, v):
        """Ensure timestamps are in ISO 8601 format."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    def to_json(self, path: Union[str, Path], indent: int = 2) -> None:
        """Save manifest to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "Manifest":
        """Load manifest from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    def compute_pipeline_hash(self) -> str:
        """Compute deterministic hash of pipeline configuration."""
        # Create a canonical representation of the pipeline
        pipeline_repr = json.dumps(
            {
                "steps": [
                    {"function": step.function, "parameters": step.parameters}
                    for step in self.pipeline_steps
                ],
                "features": self.features.model_dump(),
            },
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(pipeline_repr.encode()).hexdigest()[:16]
    
    def validate_reproducibility(self, other: "Manifest") -> Dict[str, bool]:
        """Compare two manifests for reproducibility."""
        return {
            "same_pipeline": self.pipeline_hash == other.pipeline_hash,
            "same_version": self.metdatapy_version == other.metdatapy_version,
            "same_features": (
                self.features.original_features == other.features.original_features
            ),
            "same_scaler": (
                self.scaler.method == other.scaler.method if self.scaler and other.scaler else True
            ),
        }


class ManifestBuilder:
    """Helper class to build manifests incrementally during pipeline execution."""
    
    def __init__(self, source: str):
        """Initialize manifest builder."""
        self.source = source
        self.steps: List[PipelineStep] = []
        self.start_time = datetime.utcnow()
        self.dataset_info: Optional[DatasetInfo] = None
        self.features_info = FeatureInfo(original_features=[])
        self.qc_report: Optional[QCReport] = None
        self.scaler_params: Optional[ScalerParamsModel] = None
        self.split_boundaries: Optional[SplitBoundaries] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_step(
        self,
        step_name: str,
        function: str,
        parameters: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None,
    ) -> "ManifestBuilder":
        """Add a pipeline step."""
        self.steps.append(
            PipelineStep(
                step=step_name,
                function=function,
                parameters=parameters or {},
                timestamp=datetime.utcnow().isoformat(),
                duration_seconds=duration,
            )
        )
        return self
    
    def set_dataset_info(
        self,
        df: pd.DataFrame,
        frequency: Optional[str] = None,
    ) -> "ManifestBuilder":
        """Set dataset information from DataFrame."""
        missing = {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().any()}
        
        self.dataset_info = DatasetInfo(
            source=self.source,
            rows=len(df),
            columns=list(df.columns),
            start_time=df.index.min().isoformat() if hasattr(df.index, 'min') else "unknown",
            end_time=df.index.max().isoformat() if hasattr(df.index, 'max') else "unknown",
            frequency=frequency,
            missing_values=missing,
        )
        
        # Set original features
        self.features_info.original_features = [
            col for col in df.columns 
            if not col.startswith('qc_') and col not in ['gap', 'imputed', 'impute_method']
        ]
        
        return self
    
    def set_qc_report(self, df: pd.DataFrame) -> "ManifestBuilder":
        """Generate QC report from DataFrame with QC flags."""
        qc_cols = [col for col in df.columns if col.startswith('qc_')]
        if not qc_cols:
            return self
        
        flags_by_type = {col: int(df[col].sum()) for col in qc_cols if df[col].any()}
        total_flags = int(df[qc_cols].any(axis=1).sum())
        
        self.qc_report = QCReport(
            total_flags=total_flags,
            flags_by_type=flags_by_type,
            flagged_percentage=round(100 * total_flags / len(df), 2) if len(df) > 0 else 0.0,
        )
        return self
    
    def set_derived_features(self, features: List[str]) -> "ManifestBuilder":
        """Set derived features."""
        self.features_info.derived_features = features
        return self
    
    def set_lag_features(self, features: List[str]) -> "ManifestBuilder":
        """Set lag features."""
        self.features_info.lag_features = features
        return self
    
    def set_calendar_features(self, features: List[str]) -> "ManifestBuilder":
        """Set calendar features."""
        self.features_info.calendar_features = features
        return self
    
    def set_target_features(self, features: List[str]) -> "ManifestBuilder":
        """Set target features."""
        self.features_info.target_features = features
        return self
    
    def set_scaler(self, scaler_params: ScalerParamsModel) -> "ManifestBuilder":
        """Set scaler parameters."""
        self.scaler_params = scaler_params
        return self
    
    def set_split(self, split_boundaries: SplitBoundaries) -> "ManifestBuilder":
        """Set split boundaries."""
        self.split_boundaries = split_boundaries
        return self
    
    def add_metadata(self, key: str, value: Any) -> "ManifestBuilder":
        """Add custom metadata."""
        self.metadata[key] = value
        return self
    
    def build(self) -> Manifest:
        """Build the final manifest."""
        from . import __version__
        
        if self.dataset_info is None:
            raise ValueError("Dataset info must be set before building manifest")
        
        manifest = Manifest(
            metdatapy_version=__version__,
            created_at=datetime.utcnow().isoformat(),
            dataset=self.dataset_info,
            pipeline_steps=self.steps,
            pipeline_hash="",  # Will be computed below
            features=self.features_info,
            qc_report=self.qc_report,
            scaler=self.scaler_params,
            split=self.split_boundaries,
            metadata=self.metadata,
        )
        
        # Compute pipeline hash
        manifest.pipeline_hash = manifest.compute_pipeline_hash()
        
        return manifest


def validate_manifest(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate a manifest file.
    
    Returns a dictionary with validation results.
    """
    try:
        manifest = Manifest.from_json(path)
        
        results = {
            "valid": True,
            "version": manifest.version,
            "metdatapy_version": manifest.metdatapy_version,
            "pipeline_steps": len(manifest.pipeline_steps),
            "pipeline_hash": manifest.pipeline_hash,
            "has_qc_report": manifest.qc_report is not None,
            "has_scaler": manifest.scaler is not None,
            "has_split": manifest.split is not None,
            "warnings": [],
            "errors": [],
        }
        
        # Check for common issues
        if not manifest.pipeline_steps:
            results["warnings"].append("No pipeline steps recorded")
        
        if manifest.qc_report and manifest.qc_report.flagged_percentage > 50:
            results["warnings"].append(
                f"High percentage of flagged data: {manifest.qc_report.flagged_percentage}%"
            )
        
        if manifest.scaler and not manifest.split:
            results["warnings"].append("Scaler defined but no train/test split boundaries")
        
        return results
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
        }

