import pandas as pd
from metdatapy.core import WeatherSet


def test_from_mapping_and_units():
    df = pd.DataFrame({
        "dt": ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z"],
        "TempF": [32.0, 50.0],
        "RH": [60, 65],
    })
    mapping = {
        "ts": {"col": "dt"},
        "fields": {
            "temp_c": {"col": "TempF", "unit": "F"},
            "rh_pct": {"col": "RH"},
        },
    }
    ws = WeatherSet.from_mapping(df, mapping).to_utc().normalize_units(mapping)
    out = ws.to_dataframe()
    assert "temp_c" in out.columns
    assert abs(out["temp_c"].iloc[0] - 0.0) < 1e-6
    assert out.index.tz is not None
