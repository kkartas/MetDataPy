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


def test_read_weathercloud_csv_maps_utf16le_without_bom(tmp_path):
    csv_path = tmp_path / "weathercloud_utf16le_no_bom.csv"
    content = (
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;12.5;70;1.2\n"
    )
    csv_path.write_bytes(content.encode("utf-16le"))

    df = read_weathercloud_csv(csv_path, _weathercloud_mapping())

    assert list(df.columns) == ["temp_c", "rh_pct", "rain_rate_mmh"]
    assert df.index[0] == pd.Timestamp("2023-12-31 22:00", tz="UTC")
    assert df.iloc[0]["temp_c"] == 12.5


def test_read_weathercloud_csv_shifts_dst_nonexistent_rows_by_default(tmp_path):
    csv_path = tmp_path / "weathercloud_dst.csv"
    csv_path.write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-03-31 03:00;12.5;70;1.2\n",
        encoding="utf-8",
    )

    df = read_weathercloud_csv(csv_path, _weathercloud_mapping())

    assert df.index[0] == pd.Timestamp("2024-03-31 01:00", tz="UTC")
    assert df.iloc[0]["temp_c"] == 12.5


def test_read_weathercloud_csv_handles_isolated_dst_ambiguous_row_by_default(tmp_path):
    csv_path = tmp_path / "weathercloud_dst_fallback.csv"
    csv_path.write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-10-27 03:30;12.5;70;1.2\n",
        encoding="utf-8",
    )

    df = read_weathercloud_csv(csv_path, _weathercloud_mapping())

    assert df.index[0] == pd.Timestamp("2024-10-27 01:30", tz="UTC")
    assert df.iloc[0]["temp_c"] == 12.5


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


def test_read_weathercloud_directory_keeps_first_duplicate_by_default(tmp_path):
    mapping = _weathercloud_mapping()
    (tmp_path / "a.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;12.5;70;1.2\n"
        "2024-01-01 01:00;13.0;71;0.0\n",
        encoding="utf-8",
    )
    (tmp_path / "b.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 01:00;99.0;80;0.0\n"
        "2024-01-01 02:00;14.0;72;0.0\n",
        encoding="utf-8",
    )

    with pytest.warns(UserWarning, match="duplicate Weathercloud timestamps"):
        df = read_weathercloud_directory(tmp_path, mapping)

    assert len(df) == 3
    assert df.loc[pd.Timestamp("2023-12-31 23:00", tz="UTC"), "temp_c"] == 13.0


def test_read_weathercloud_directory_can_raise_on_duplicates(tmp_path):
    mapping = _weathercloud_mapping()
    for name in ["a.csv", "b.csv"]:
        (tmp_path / name).write_text(
            "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
            "2024-01-01 00:00;12.5;70;1.2\n",
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="duplicate Weathercloud timestamps"):
        read_weathercloud_directory(tmp_path, mapping, duplicate_policy="raise")


def test_read_weathercloud_directory_returns_duplicate_report(tmp_path):
    mapping = _weathercloud_mapping()
    (tmp_path / "a.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;12.5;70;1.2\n",
        encoding="utf-8",
    )
    (tmp_path / "b.csv").write_text(
        "Date (Europe/Athens);Temperature (C);Humidity (%);Rain Rate (mm/h)\n"
        "2024-01-01 00:00;99.0;80;0.0\n",
        encoding="utf-8",
    )

    with pytest.warns(UserWarning, match="duplicate Weathercloud timestamps"):
        df, report = read_weathercloud_directory(tmp_path, mapping, return_report=True)

    assert len(df) == 1
    assert report["files_read"] == ["a.csv", "b.csv"]
    assert report["rows_before_duplicate_handling"] == 2
    assert report["rows_after_duplicate_handling"] == 1
    assert report["duplicate_rows"] == 1
    assert report["duplicate_timestamp_count"] == 1
    assert report["duplicate_policy"] == "keep_first"


def test_read_weathercloud_directory_requires_csvs(tmp_path):
    with pytest.raises(ValueError, match="No Weathercloud CSV files"):
        read_weathercloud_directory(tmp_path, _weathercloud_mapping())
