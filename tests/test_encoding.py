"""Tests for encoding detection in CSV files."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from metdatapy.mapper import Detector
from metdatapy.io import read_csv, _detect_encoding


def test_detect_encoding_utf8(tmp_path):
    """Test UTF-8 encoding detection."""
    csv_file = tmp_path / "test_utf8.csv"
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    df.to_csv(csv_file, index=False, encoding="utf-8")
    
    encoding = _detect_encoding(str(csv_file))
    assert encoding == "utf-8"


def test_detect_encoding_utf16(tmp_path):
    """Test UTF-16 encoding detection."""
    csv_file = tmp_path / "test_utf16.csv"
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
    df.to_csv(csv_file, index=False, encoding="utf-16")
    
    encoding = _detect_encoding(str(csv_file))
    assert encoding == "utf-16"


def test_detect_encoding_latin1(tmp_path):
    """Test Latin-1 encoding detection."""
    csv_file = tmp_path / "test_latin1.csv"
    # Create content with Latin-1 specific characters
    content = "temp,city\n25,São Paulo\n30,Zürich\n"
    csv_file.write_text(content, encoding="latin-1")
    
    encoding = _detect_encoding(str(csv_file))
    assert encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]


def test_read_csv_with_utf8(tmp_path):
    """Test reading UTF-8 encoded CSV."""
    csv_file = tmp_path / "test_utf8.csv"
    df = pd.DataFrame({
        "DateTime": ["2024-01-01 00:00", "2024-01-01 01:00"],
        "temp_c": [20.5, 21.0]
    })
    df.to_csv(csv_file, index=False, encoding="utf-8")
    
    result = read_csv(str(csv_file), ts_col="DateTime")
    assert len(result) == 2
    assert "DateTime" in result.columns
    assert "temp_c" in result.columns


def test_read_csv_with_utf16(tmp_path):
    """Test reading UTF-16 encoded CSV."""
    csv_file = tmp_path / "test_utf16.csv"
    df = pd.DataFrame({
        "DateTime": ["2024-01-01 00:00", "2024-01-01 01:00"],
        "temp_c": [20.5, 21.0]
    })
    df.to_csv(csv_file, index=False, encoding="utf-16")
    
    result = read_csv(str(csv_file), ts_col="DateTime")
    assert len(result) == 2
    assert "DateTime" in result.columns
    assert "temp_c" in result.columns


def test_detect_encoding_utf16le_without_bom(tmp_path):
    """Detect UTF-16LE CSV files that omit a byte-order mark."""
    csv_file = tmp_path / "weathercloud_utf16le_no_bom.csv"
    content = (
        "Date (Europe/Athens);Temperature (C);Humidity (%)\n"
        "2024-01-01 00:00;12.5;70\n"
    )
    csv_file.write_bytes(content.encode("utf-16le"))

    encoding = _detect_encoding(str(csv_file))
    result = read_csv(str(csv_file))

    assert encoding == "utf-16le"
    assert list(result.columns) == ["Date (Europe/Athens)", "Temperature (C)", "Humidity (%)"]
    assert result.iloc[0]["Temperature (C)"] == 12.5


def test_detect_encoding_utf16be_without_bom(tmp_path):
    """Detect UTF-16BE CSV files that omit a byte-order mark."""
    csv_file = tmp_path / "weathercloud_utf16be_no_bom.csv"
    content = (
        "Date (Europe/Athens);Temperature (C);Humidity (%)\n"
        "2024-01-01 00:00;12.5;70\n"
    )
    csv_file.write_bytes(content.encode("utf-16be"))

    encoding = _detect_encoding(str(csv_file))
    result = read_csv(str(csv_file))

    assert encoding == "utf-16be"
    assert list(result.columns) == ["Date (Europe/Athens)", "Temperature (C)", "Humidity (%)"]
    assert result.iloc[0]["Humidity (%)"] == 70


def test_read_csv_detects_semicolon_delimiter(tmp_path):
    """Test semicolon-delimited CSV detection."""
    csv_file = tmp_path / "weather_semicolon.csv"
    csv_file.write_text(
        "DateTime;temp_c;rh_pct\n"
        "2024-01-01 00:00;20.5;60\n"
        "2024-01-01 01:00;21.0;61\n",
        encoding="utf-8",
    )

    result = read_csv(str(csv_file), ts_col="DateTime")

    assert list(result.columns) == ["DateTime", "temp_c", "rh_pct"]
    assert len(result) == 2


def test_read_csv_honors_explicit_delimiter(tmp_path):
    """Test explicit delimiter configuration."""
    csv_file = tmp_path / "weather_pipe.csv"
    csv_file.write_text("DateTime|temp_c\n2024-01-01 00:00|20.5\n", encoding="utf-8")

    result = read_csv(str(csv_file), delimiter="|")

    assert list(result.columns) == ["DateTime", "temp_c"]


def test_detector_detect_from_csv_with_utf16(tmp_path):
    """Test detector CSV loading path with UTF-16 input."""
    csv_file = tmp_path / "detector_utf16.csv"
    df = pd.DataFrame({
        "DateTime": ["2024-01-01 00:00", "2024-01-01 01:00"],
        "Temperature (degC)": [20.5, 21.0],
        "RH (%)": [60.0, 61.0],
    })
    df.to_csv(csv_file, index=False, encoding="utf-16")

    mapping = Detector().detect_from_csv(str(csv_file))

    assert mapping["ts"]["col"] == "DateTime"
    assert mapping["fields"]["temp_c"]["col"] == "Temperature (degC)"
    assert mapping["fields"]["rh_pct"]["col"] == "RH (%)"


def test_read_csv_with_special_characters_latin1(tmp_path):
    """Test reading CSV with special Latin-1 characters."""
    csv_file = tmp_path / "test_special.csv"
    content = "city,temp\nSão Paulo,25\nZürich,18\nMünchen,15\n"
    csv_file.write_text(content, encoding="latin-1")
    
    # Should not raise UnicodeDecodeError
    result = read_csv(str(csv_file))
    assert len(result) == 3
    assert "city" in result.columns
    assert "temp" in result.columns


def test_read_csv_with_cp1252(tmp_path):
    """Test reading CSV with Windows-1252 encoding."""
    csv_file = tmp_path / "test_cp1252.csv"
    # Windows-1252 has special characters in range 0x80-0x9F
    content = "name,value\ntest–data,123\ncafé,456\n"  # en-dash (–) is cp1252 specific
    csv_file.write_text(content, encoding="cp1252")
    
    # Should not raise UnicodeDecodeError
    result = read_csv(str(csv_file))
    assert len(result) == 2


def test_encoding_fallback_for_corrupted_file(tmp_path):
    """Test that encoding detection falls back gracefully for corrupted files."""
    csv_file = tmp_path / "test_corrupted.csv"
    # Write some binary content that's not valid in any encoding
    csv_file.write_bytes(b"DateTime,temp\n2024-01-01,\xff\xfe\x00invalid")
    
    # Should detect some encoding (latin-1 accepts all bytes, so it might be detected)
    encoding = _detect_encoding(str(csv_file))
    assert encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    # read_csv should handle this without crashing due to encoding_errors='replace'
    result = read_csv(str(csv_file))
    assert "DateTime" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

