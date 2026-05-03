import pandas as pd
import pytest

from metdatapy import read_weathercloud_csv, read_weathercloud_directory


def _weathercloud_mapping():
    return {
        "ts": {"col": "Date (Europe/Athens)"},
        "fields": {
            "temp_c": {"col": "Temperature (C)", "unit": "C"},
            "rh_pct": {"col": "Humidity (%)", "unit": "%"},
            "rain_rate_mmh": {"col": "Rain Rate (mm/h)", "unit": "mm/h"},
        },
    }


def test_read_weathercloud_csv_returns_raw_without_mapping(tmp_path):
    csv_path = tmp_path / "weathercloud.csv"
    csv_path.write_text(
        "Date (Europe/Athens);Temperature (C)\n"
        "2024-01-01 00:00;12.5\n",
        encoding="utf-8",
    )

    df = read_weathercloud_csv(csv_path)

    assert list(df.columns) == ["Date (Europe/Athens)", "Temperature (C)"]
    assert df.iloc[0]["Temperature (C)"] == 12.5


def test_read_weathercloud_csv_maps_semicolon_export_to_canonical(tmp_path):
    csv_path = tmp_path / "weathercloud.csv"
    csv_path.write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;12.5;70;1.2\n",
        encoding="utf-8",
    )

    df = read_weathercloud_csv(csv_path, _weathercloud_mapping())

    assert list(df.columns) == ["temp_c", "rh_pct", "rain_rate_mmh"]
    assert df.index.name == "ts_utc"
    assert str(df.index.tz) == "UTC"
    assert df.index[0] == pd.Timestamp("2023-12-31 22:00", tz="UTC")
    assert df.iloc[0]["rain_rate_mmh"] == 1.2


def test_read_weathercloud_directory_concatenates_sorted_csvs(tmp_path):
    mapping = _weathercloud_mapping()
    (tmp_path / "b.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 01:00;13.0;71;0.0\n",
        encoding="utf-8",
    )
    (tmp_path / "a.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;12.5;70;1.2\n",
        encoding="utf-8",
    )

    df = read_weathercloud_directory(tmp_path, mapping)

    assert len(df) == 2
    assert df.index.is_monotonic_increasing
    assert list(df["temp_c"]) == [12.5, 13.0]


def test_read_weathercloud_directory_requires_csvs(tmp_path):
    with pytest.raises(ValueError, match="No Weathercloud CSV files"):
        read_weathercloud_directory(tmp_path, _weathercloud_mapping())
