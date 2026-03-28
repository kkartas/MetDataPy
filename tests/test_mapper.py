import pandas as pd

from metdatapy.mapper import Detector


def test_detector_basic_columns():
    df = pd.DataFrame({
        "DateTime": ["2025-01-01 00:00", "2025-01-01 01:00"],
        "Temperature (degC)": [10, 11],
        "RH (%)": [50, 55],
        "Wind Speed (m/s)": [2.1, 3.0],
    })
    mapping = Detector().detect(df)

    assert mapping["ts"]["col"] == "DateTime"
    fields = mapping["fields"]
    assert "temp_c" in fields and fields["temp_c"]["col"] == "Temperature (degC)"
    assert "rh_pct" in fields
    assert "wspd_ms" in fields


def test_detector_does_not_invent_missing_fields():
    df = pd.DataFrame({
        "timestamp": ["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"],
        "temperature": [10.0, 11.0, 12.0],
        "humidity": [50.0, 55.0, 60.0],
        "pressure": [1012.0, 1012.5, 1013.0],
    })

    mapping = Detector().detect(df)
    fields = mapping["fields"]

    assert set(fields) == {"temp_c", "rh_pct", "pres_hpa"}
    assert len({config["col"] for config in fields.values()}) == len(fields)


def test_detector_assigns_each_source_column_once():
    df = pd.DataFrame({
        "DateTime": ["2025-01-01 00:00", "2025-01-01 01:00", "2025-01-01 02:00"],
        "Wind Speed Gust (m/s)": [2.0, 3.0, 4.0],
    })

    mapping = Detector().detect(df)
    mapped_columns = [config["col"] for config in mapping["fields"].values()]

    assert len(mapped_columns) == len(set(mapped_columns))
    assert sum(field in mapping["fields"] for field in ("wspd_ms", "gust_ms")) == 1
