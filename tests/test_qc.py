import pandas as pd
from metdatapy.qc import qc_range, qc_spike, qc_flatline, qc_consistency, qc_any


def test_qc_range_flags_out_of_bounds():
    df = pd.DataFrame({
        "temp_c": [-50, 20, 60],
        "rh_pct": [10, 200, -1],
    })
    out = qc_range(df.copy())
    assert out["qc_temp_c_range"].tolist() == [True, False, True]
    assert out["qc_rh_pct_range"].tolist() == [False, True, True]


def test_qc_spike_and_flatline():
    df = pd.DataFrame({
        "temp_c": [10, 10, 10, 50, 10, 10, 10],
    })
    out = qc_spike(df.copy(), window=5, thresh=4.0)
    assert out["qc_temp_c_spike"].any()
    out2 = qc_flatline(df.copy(), window=3, tol=0.0)
    assert out2["qc_temp_c_flatline"].iloc[1]


## --- v1.0.2 regressions: Task 5 (flatline false positives) ---


def test_qc_flatline_short_series_not_flagged():
    """A short series (< window) should not be automatically flagged as flatline."""
    df = pd.DataFrame({"temp_c": [20.0, 21.0, 22.0]})
    out = qc_flatline(df.copy(), window=5, tol=0.0)
    # With only 3 values and window=5, there aren't enough observations
    assert not out["qc_temp_c_flatline"].any()


def test_qc_flatline_nan_window_not_flagged():
    """Windows dominated by NaN should not be flagged as flatline."""
    import numpy as np
    df = pd.DataFrame({
        "temp_c": [np.nan, np.nan, 20.0, np.nan, np.nan, np.nan, np.nan]
    })
    out = qc_flatline(df.copy(), window=5, tol=0.0)
    # Not enough valid observations in any window
    assert not out["qc_temp_c_flatline"].any()


def test_qc_flatline_true_constant_still_flags():
    """A genuine flatline of constant values should still be flagged."""
    df = pd.DataFrame({"temp_c": [20.0] * 10})
    out = qc_flatline(df.copy(), window=5, tol=0.0)
    # Centre of the series should be flagged
    assert out["qc_temp_c_flatline"].any()


def test_qc_consistency_and_any():
    df = pd.DataFrame({
        "temp_c": [20, 20],
        "dew_point_c": [25, 15],
        "wspd_ms": [0.0, 5.0],
        "wdir_deg": [90.0, 270.0],
    })
    out = qc_consistency(df.copy())
    out = qc_any(out)
    assert bool(out["qc_consistency"].iloc[0]) is True
    assert out["qc_any"].any()
