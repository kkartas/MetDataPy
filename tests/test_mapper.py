import pandas as pd
from metdatapy.mapper import Detector


def test_detector_basic_columns():
    df = pd.DataFrame({
        "DateTime": ["2025-01-01 00:00", "2025-01-01 01:00"],
        "Temperature (°C)": [10, 11],
        "RH (%)": [50, 55],
        "Wind Speed (m/s)": [2.1, 3.0],
    })
    det = Detector()
    mapping = det.detect(df)
    assert mapping["ts"]["col"] == "DateTime"
    fields = mapping["fields"]
    assert "temp_c" in fields and fields["temp_c"]["col"] == "Temperature (°C)"
    assert "rh_pct" in fields
    assert "wspd_ms" in fields
