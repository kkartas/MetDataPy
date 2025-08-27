import pandas as pd
from metdatapy.qc import qc_range


def test_qc_range_flags_out_of_bounds():
    df = pd.DataFrame({
        "temp_c": [-50, 20, 60],
        "rh_pct": [10, 200, -1],
    })
    out = qc_range(df.copy())
    assert out["qc_temp_c_range"].tolist() == [True, False, True]
    assert out["qc_rh_pct_range"].tolist() == [False, True, True]
