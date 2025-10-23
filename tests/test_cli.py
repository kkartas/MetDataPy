"""
Comprehensive tests for CLI commands.

This test suite covers all CLI commands to achieve >80% coverage.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from metdatapy.cli import main
from metdatapy.mapper import Mapper


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "test_data.csv"
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=100, freq="10min"),
        "temperature": [20.0 + i * 0.1 for i in range(100)],
        "humidity": [60.0 + i * 0.1 for i in range(100)],
        "pressure": [1013.0 + i * 0.01 for i in range(100)],
        "wind_speed": [5.0 + i * 0.05 for i in range(100)],
        "wind_direction": [180.0 + i for i in range(100)],
        "rainfall": [0.0] * 100,
    })
    df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def sample_mapping(tmp_path):
    """Create a sample mapping file."""
    mapping_file = tmp_path / "mapping.yml"
    mapping = {
        "ts": {"col": "timestamp"},
        "fields": {
            "temp_c": {"col": "temperature", "unit": "C"},
            "rh_pct": {"col": "humidity", "unit": "%"},
            "pres_hpa": {"col": "pressure", "unit": "hpa"},
            "wspd_ms": {"col": "wind_speed", "unit": "m/s"},
            "wdir_deg": {"col": "wind_direction", "unit": "deg"},
            "rain_mm": {"col": "rainfall", "unit": "mm"},
        }
    }
    Mapper.save(mapping, str(mapping_file))
    return str(mapping_file)


@pytest.fixture
def sample_parquet(tmp_path, sample_csv, sample_mapping):
    """Create a sample parquet file with processed data."""
    parquet_file = tmp_path / "test_data.parquet"
    
    # Load and process data
    from metdatapy.core import WeatherSet
    mapping = Mapper.load(sample_mapping)
    df = pd.read_csv(sample_csv)
    ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
    ws.to_dataframe().to_parquet(parquet_file)
    
    return str(parquet_file)


class TestIngestDetect:
    """Tests for 'mdp ingest detect' command."""
    
    def test_detect_with_yes_flag(self, runner, sample_csv, tmp_path):
        """Test detection with --yes flag (non-interactive)."""
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
            "--yes"
        ])
        assert result.exit_code == 0
        assert "timestamp" in result.output
        
    def test_detect_with_save(self, runner, sample_csv, tmp_path):
        """Test detection with --save option."""
        output_file = tmp_path / "detected_mapping.yml"
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
            "--save", str(output_file),
            "--yes"
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Saved mapping to" in result.output
        
    def test_detect_interactive(self, runner, sample_csv):
        """Test interactive detection mode."""
        # Simulate user input: accept all defaults by providing empty strings
        inputs = "\n" * 20  # Press Enter multiple times for defaults
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
        ], input=inputs)
        # Should complete without error
        assert "Interactive mapping wizard" in result.output
        
    def test_detect_nonexistent_file(self, runner):
        """Test detection with non-existent file."""
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", "nonexistent.csv",
            "--yes"
        ])
        assert result.exit_code != 0


class TestIngestApply:
    """Tests for 'mdp ingest apply' command."""
    
    def test_apply_mapping(self, runner, sample_csv, sample_mapping, tmp_path):
        """Test applying mapping to CSV."""
        output_file = tmp_path / "output.parquet"
        result = runner.invoke(main, [
            "ingest", "apply",
            "--csv", sample_csv,
            "--map", sample_mapping,
            "--out", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Wrote" in result.output
        
        # Verify output
        df = pd.read_parquet(output_file)
        assert "temp_c" in df.columns
        assert len(df) == 100
        
    def test_apply_missing_csv(self, runner, sample_mapping, tmp_path):
        """Test with missing CSV file."""
        output_file = tmp_path / "output.parquet"
        result = runner.invoke(main, [
            "ingest", "apply",
            "--csv", "missing.csv",
            "--map", sample_mapping,
            "--out", str(output_file)
        ])
        assert result.exit_code != 0
        
    def test_apply_missing_mapping(self, runner, sample_csv, tmp_path):
        """Test with missing mapping file."""
        output_file = tmp_path / "output.parquet"
        result = runner.invoke(main, [
            "ingest", "apply",
            "--csv", sample_csv,
            "--map", "missing_mapping.yml",
            "--out", str(output_file)
        ])
        assert result.exit_code != 0


class TestIngestTemplate:
    """Tests for 'mdp ingest template' command."""
    
    def test_template_to_stdout(self, runner):
        """Test template output to stdout."""
        result = runner.invoke(main, ["ingest", "template"])
        assert result.exit_code == 0
        assert "ts" in result.output
        assert "fields" in result.output
        
    def test_template_to_file(self, runner, tmp_path):
        """Test template save to file."""
        output_file = tmp_path / "template.yml"
        result = runner.invoke(main, [
            "ingest", "template",
            "--out", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Wrote mapping template" in result.output
        
        # Verify it's valid JSON
        content = json.loads(output_file.read_text())
        assert "ts" in content
        assert "fields" in content
        
    def test_template_minimal(self, runner):
        """Test minimal template."""
        result = runner.invoke(main, [
            "ingest", "template",
            "--minimal"
        ])
        assert result.exit_code == 0
        assert "ts" in result.output


class TestQCRun:
    """Tests for 'mdp qc run' command."""
    
    def test_qc_basic(self, runner, sample_parquet, tmp_path):
        """Test basic QC run."""
        output_file = tmp_path / "qc_output.parquet"
        result = runner.invoke(main, [
            "qc", "run",
            "--in", sample_parquet,
            "--out", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Wrote" in result.output
        
        # Verify QC flags were added
        df = pd.read_parquet(output_file)
        qc_cols = [c for c in df.columns if str(c).startswith("qc_")]
        assert len(qc_cols) > 0
        
    def test_qc_with_report(self, runner, sample_parquet, tmp_path):
        """Test QC with report generation."""
        output_file = tmp_path / "qc_output.parquet"
        report_file = tmp_path / "qc_report.json"
        result = runner.invoke(main, [
            "qc", "run",
            "--in", sample_parquet,
            "--out", str(output_file),
            "--report", str(report_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        assert report_file.exists()
        assert "Saved report" in result.output
        
        # Verify report content
        report = json.loads(report_file.read_text())
        assert isinstance(report, dict)
        
    def test_qc_with_yaml_config(self, runner, sample_parquet, tmp_path):
        """Test QC with YAML config file."""
        config_file = tmp_path / "qc_config.yml"
        config_file.write_text("""
spike:
  window: 5
  thresh: 6.0
flatline:
  window: 3
  tol: 0.0
""")
        
        output_file = tmp_path / "qc_output.parquet"
        result = runner.invoke(main, [
            "qc", "run",
            "--in", sample_parquet,
            "--out", str(output_file),
            "--config", str(config_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
    def test_qc_with_json_config(self, runner, sample_parquet, tmp_path):
        """Test QC with JSON config file."""
        config_file = tmp_path / "qc_config.json"
        config = {
            "spike": {"window": 5, "thresh": 6.0},
            "flatline": {"window": 3, "tol": 0.0}
        }
        config_file.write_text(json.dumps(config))
        
        output_file = tmp_path / "qc_output.parquet"
        result = runner.invoke(main, [
            "qc", "run",
            "--in", sample_parquet,
            "--out", str(output_file),
            "--config", str(config_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
    def test_qc_with_invalid_config(self, runner, sample_parquet, tmp_path):
        """Test QC with invalid config file."""
        config_file = tmp_path / "invalid_config.txt"
        config_file.write_text("invalid yaml: [[[")
        
        output_file = tmp_path / "qc_output.parquet"
        # Should still run with default config
        result = runner.invoke(main, [
            "qc", "run",
            "--in", sample_parquet,
            "--out", str(output_file),
            "--config", str(config_file)
        ])
        assert result.exit_code == 0
        
    def test_qc_missing_input(self, runner, tmp_path):
        """Test QC with missing input file."""
        output_file = tmp_path / "qc_output.parquet"
        result = runner.invoke(main, [
            "qc", "run",
            "--in", "missing.parquet",
            "--out", str(output_file)
        ])
        assert result.exit_code != 0


class TestManifestCommands:
    """Tests for manifest commands."""
    
    @pytest.fixture
    def sample_manifest(self, tmp_path):
        """Create a sample manifest file."""
        from metdatapy.manifest import Manifest, DatasetInfo, FeatureInfo
        
        manifest = Manifest(
            version="1.0",
            created_at="2024-01-01T00:00:00Z",
            metdatapy_version="0.0.1",
            dataset=DatasetInfo(
                source="test.csv",
                rows=100,
                columns=["temp_c", "rh_pct"],
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-01-02T00:00:00Z",
                frequency="10min",
                missing_values={}
            ),
            pipeline_steps=[],
            features=FeatureInfo(
                original_features=["temp_c", "rh_pct"],
                derived_features=[],
                lag_features=[],
                calendar_features=[],
                target_features=[]
            ),
            pipeline_hash="test_hash_123"
        )
        
        manifest_file = tmp_path / "manifest.json"
        manifest.to_json(str(manifest_file))
        return str(manifest_file)
    
    def test_manifest_validate_valid(self, runner, sample_manifest):
        """Test validating a valid manifest."""
        result = runner.invoke(main, [
            "manifest", "validate",
            sample_manifest
        ])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
        
    def test_manifest_validate_verbose(self, runner, sample_manifest):
        """Test validate with verbose flag."""
        result = runner.invoke(main, [
            "manifest", "validate",
            sample_manifest,
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Manifest Details" in result.output
        assert "Version:" in result.output
        
    def test_manifest_validate_invalid(self, runner, tmp_path):
        """Test validating invalid manifest."""
        invalid_manifest = tmp_path / "invalid_manifest.json"
        invalid_manifest.write_text('{"invalid": "structure"}')
        
        result = runner.invoke(main, [
            "manifest", "validate",
            str(invalid_manifest)
        ])
        assert result.exit_code != 0
        
    def test_manifest_show_summary(self, runner, sample_manifest):
        """Test showing manifest summary."""
        result = runner.invoke(main, [
            "manifest", "show",
            sample_manifest
        ])
        assert result.exit_code == 0
        assert "Manifest Summary" in result.output
        assert "Dataset:" in result.output
        
    def test_manifest_show_json(self, runner, sample_manifest):
        """Test showing manifest as JSON."""
        result = runner.invoke(main, [
            "manifest", "show",
            sample_manifest,
            "--format", "json"
        ])
        assert result.exit_code == 0
        # Should be valid JSON
        output_data = json.loads(result.output)
        assert "version" in output_data
        
    def test_manifest_show_yaml(self, runner, sample_manifest):
        """Test showing manifest as YAML."""
        result = runner.invoke(main, [
            "manifest", "show",
            sample_manifest,
            "--format", "yaml"
        ])
        assert result.exit_code == 0
        assert "version:" in result.output
        
    def test_manifest_compare_same(self, runner, sample_manifest):
        """Test comparing identical manifests."""
        result = runner.invoke(main, [
            "manifest", "compare",
            sample_manifest,
            sample_manifest
        ])
        assert result.exit_code == 0
        assert "compatible" in result.output.lower() or "✓" in result.output
        
    def test_manifest_compare_different(self, runner, sample_manifest, tmp_path):
        """Test comparing different manifests."""
        from metdatapy.manifest import Manifest, DatasetInfo, FeatureInfo
        
        # Create a different manifest
        manifest2 = Manifest(
            version="1.0",
            created_at="2024-01-02T00:00:00Z",
            metdatapy_version="0.0.2",
            dataset=DatasetInfo(
                source="test2.csv",
                rows=200,
                columns=["temp_c"],
                start_time="2024-01-01T00:00:00Z",
                end_time="2024-01-03T00:00:00Z",
                frequency="1H",
                missing_values={"temp_c": 5}
            ),
            pipeline_steps=[],
            features=FeatureInfo(
                original_features=["temp_c"],
                derived_features=[],
                lag_features=[],
                calendar_features=[],
                target_features=[]
            ),
            pipeline_hash="different_hash"
        )
        
        manifest_file2 = tmp_path / "manifest2.json"
        manifest2.to_json(str(manifest_file2))
        
        result = runner.invoke(main, [
            "manifest", "compare",
            sample_manifest,
            str(manifest_file2)
        ])
        assert result.exit_code == 0
        assert "Comparing Manifests" in result.output


class TestCLIHelp:
    """Test CLI help messages."""
    
    def test_main_help(self, runner):
        """Test main help message."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "MetDataPy command-line interface" in result.output
        
    def test_ingest_help(self, runner):
        """Test ingest help message."""
        result = runner.invoke(main, ["ingest", "--help"])
        assert result.exit_code == 0
        assert "Ingestion helpers" in result.output
        
    def test_qc_help(self, runner):
        """Test qc help message."""
        result = runner.invoke(main, ["qc", "--help"])
        assert result.exit_code == 0
        assert "Quality control" in result.output
        
    def test_manifest_help(self, runner):
        """Test manifest help message."""
        result = runner.invoke(main, ["manifest", "--help"])
        assert result.exit_code == 0
        assert "Manifest and reproducibility" in result.output


class TestInteractiveMappingWizard:
    """Test the interactive mapping wizard."""
    
    def test_wizard_accept_defaults(self, runner, sample_csv):
        """Test wizard accepting all defaults."""
        inputs = "\n" * 25  # Accept all defaults
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
        ], input=inputs)
        assert "Interactive mapping wizard" in result.output
        
    def test_wizard_set_to_none(self, runner, sample_csv):
        """Test wizard setting field to none."""
        inputs = "timestamp\nnone\n" + "\n" * 20
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
        ], input=inputs)
        assert "Interactive mapping wizard" in result.output
        
    def test_wizard_custom_values(self, runner, sample_csv):
        """Test wizard with custom column and unit values."""
        inputs = "timestamp\ntemperature\nC\n" + "\n" * 20
        result = runner.invoke(main, [
            "ingest", "detect",
            "--csv", sample_csv,
        ], input=inputs)
        assert "Interactive mapping wizard" in result.output

