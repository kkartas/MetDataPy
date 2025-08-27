import pandas as pd
from metdatapy.derive import dew_point_c, vpd_kpa


def test_dew_point_and_vpd_shapes():
    t = pd.Series([20.0, 25.0, 30.0])
    rh = pd.Series([50.0, 60.0, 70.0])
    td = dew_point_c(t, rh)
    vpd = vpd_kpa(t, rh)
    assert len(td) == 3 and len(vpd) == 3
    # basic sanity: dew point <= temp
    assert (td <= t + 1e-6).all()
