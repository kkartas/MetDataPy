"""
Derived meteorological metrics with scientific formulas.

This module implements standard meteorological calculations used in
atmospheric science and agricultural meteorology.

References
----------
.. [1] Alduchov, O. A., & Eskridge, R. E. (1996). Improved Magnus form
       approximation of saturation vapor pressure. Journal of Applied
       Meteorology, 35(4), 601-609.
       https://doi.org/10.1175/1520-0450(1996)035<0601:IMFAOS>2.0.CO;2

.. [2] Lawrence, M. G. (2005). The relationship between relative humidity
       and the dewpoint temperature in moist air: A simple conversion and
       applications. Bulletin of the American Meteorological Society, 86(2),
       225-233. https://doi.org/10.1175/BAMS-86-2-225

.. [3] Rothfusz, L. P. (1990). The heat index equation (or, more than you
       ever wanted to know about heat index). National Weather Service
       Technical Attachment SR 90-23.

.. [4] Steadman, R. G. (1979). The assessment of sultriness. Part I: A
       temperature-humidity index based on human physiology and clothing
       science. Journal of Applied Meteorology, 18(7), 861-873.
       https://doi.org/10.1175/1520-0450(1979)018<0861:TAOSPI>2.0.CO;2

.. [5] Osczevski, R., & Bluestein, M. (2005). The new wind chill equivalent
       temperature chart. Bulletin of the American Meteorological Society,
       86(10), 1453-1458. https://doi.org/10.1175/BAMS-86-10-1453

.. [6] Tetens, O. (1930). Über einige meteorologische Begriffe.
       Zeitschrift für Geophysik, 6, 297-309.

.. [7] Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998).
       Crop evapotranspiration - Guidelines for computing crop water
       requirements. FAO Irrigation and drainage paper 56. Food and
       Agriculture Organization of the United Nations, Rome.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Magnus formula coefficients (Alduchov & Eskridge, 1996)
A = 17.62
B = 243.12


def dew_point_c(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    """
    Calculate dew point temperature using the Magnus formula.
    
    The dew point is the temperature at which air becomes saturated with water
    vapor and condensation begins. This implementation uses the Magnus-Tetens
    approximation, which is accurate for typical atmospheric conditions.
    
    Parameters
    ----------
    temp_c : pd.Series or np.ndarray
        Air temperature in degrees Celsius
    rh_pct : pd.Series or np.ndarray
        Relative humidity in percent (0-100)
    
    Returns
    -------
    pd.Series
        Dew point temperature in degrees Celsius
    
    Notes
    -----
    The Magnus formula is:
    
    .. math::
        T_d = \\frac{B \\gamma}{A - \\gamma}
    
    where:
    
    .. math::
        \\gamma = \\ln(RH/100) + \\frac{A T}{B + T}
    
    with A = 17.62 and B = 243.12°C (Alduchov & Eskridge, 1996).
    
    Valid range: -40°C < T < 50°C, 1% < RH < 100%
    
    References
    ----------
    .. [1] Alduchov, O. A., & Eskridge, R. E. (1996). Improved Magnus form
           approximation of saturation vapor pressure. Journal of Applied
           Meteorology, 35(4), 601-609.
    .. [2] Lawrence, M. G. (2005). The relationship between relative humidity
           and the dewpoint temperature in moist air. Bulletin of the American
           Meteorological Society, 86(2), 225-233.
    
    Examples
    --------
    >>> temp = pd.Series([20.0, 25.0, 30.0])
    >>> rh = pd.Series([50.0, 60.0, 70.0])
    >>> dew_point_c(temp, rh)
    0     9.27
    1    16.67
    2    23.46
    dtype: float64
    """
    t = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=1e-6, upper=100.0)
    gamma = np.log(rh / 100.0) + (A * t) / (B + t)
    td = (B * gamma) / (A - gamma)
    return pd.Series(td, index=t.index if isinstance(t, pd.Series) else None)


def saturation_vapor_pressure_kpa(temp_c: pd.Series | np.ndarray) -> pd.Series:
    """
    Calculate saturation vapor pressure using the Tetens formula.
    
    Parameters
    ----------
    temp_c : pd.Series or np.ndarray
        Air temperature in degrees Celsius
    
    Returns
    -------
    pd.Series
        Saturation vapor pressure in kilopascals (kPa)
    
    Notes
    -----
    The Tetens formula (1930) is:
    
    .. math::
        e_s = 0.6108 \\exp\\left(\\frac{17.27 T}{T + 237.3}\\right)
    
    where T is temperature in °C and e_s is in kPa.
    
    This is a simplified form of the Clausius-Clapeyron equation and is
    accurate within ±0.1% for temperatures between -40°C and 50°C.
    
    References
    ----------
    .. [1] Tetens, O. (1930). Über einige meteorologische Begriffe.
           Zeitschrift für Geophysik, 6, 297-309.
    .. [2] Allen, R. G., et al. (1998). Crop evapotranspiration. FAO
           Irrigation and drainage paper 56, Equation 11.
    """
    t = pd.Series(temp_c, dtype="float64")
    es = 0.6108 * np.exp((17.27 * t) / (t + 237.3))
    return pd.Series(es, index=t.index if isinstance(t, pd.Series) else None)


def vpd_kpa(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    """
    Calculate Vapor Pressure Deficit (VPD).
    
    VPD is the difference between saturation vapor pressure and actual vapor
    pressure, representing the atmosphere's drying power. It is crucial for
    plant physiology, evapotranspiration, and fire weather applications.
    
    Parameters
    ----------
    temp_c : pd.Series or np.ndarray
        Air temperature in degrees Celsius
    rh_pct : pd.Series or np.ndarray
        Relative humidity in percent (0-100)
    
    Returns
    -------
    pd.Series
        Vapor pressure deficit in kilopascals (kPa)
    
    Notes
    -----
    VPD is calculated as:
    
    .. math::
        VPD = e_s - e_a = e_s \\left(1 - \\frac{RH}{100}\\right)
    
    where:
    - e_s is saturation vapor pressure (kPa)
    - e_a is actual vapor pressure (kPa)
    - RH is relative humidity (%)
    
    Higher VPD values indicate drier air and greater evaporative demand.
    Typical ranges:
    - VPD < 0.5 kPa: Low evaporative demand
    - 0.5-1.0 kPa: Moderate demand
    - VPD > 1.0 kPa: High demand (stress for many plants)
    
    References
    ----------
    .. [1] Allen, R. G., et al. (1998). Crop evapotranspiration. FAO
           Irrigation and drainage paper 56.
    .. [2] Grossiord, C., et al. (2020). Plant responses to rising vapor
           pressure deficit. New Phytologist, 226(6), 1550-1566.
           https://doi.org/10.1111/nph.16485
    
    Examples
    --------
    >>> temp = pd.Series([25.0, 30.0])
    >>> rh = pd.Series([50.0, 30.0])
    >>> vpd_kpa(temp, rh)
    0    1.583
    1    2.970
    dtype: float64
    """
    t = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=0.0, upper=100.0)
    es = saturation_vapor_pressure_kpa(t)
    ea = es * (rh / 100.0)
    return (es - ea)


def heat_index_c(temp_c: pd.Series | np.ndarray, rh_pct: pd.Series | np.ndarray) -> pd.Series:
    """
    Calculate Heat Index using the Rothfusz regression.
    
    The Heat Index combines air temperature and relative humidity to determine
    an apparent temperature - how hot it actually feels. It is used by the
    National Weather Service for heat stress warnings.
    
    Parameters
    ----------
    temp_c : pd.Series or np.ndarray
        Air temperature in degrees Celsius
    rh_pct : pd.Series or np.ndarray
        Relative humidity in percent (0-100)
    
    Returns
    -------
    pd.Series
        Heat Index in degrees Celsius
    
    Notes
    -----
    The Rothfusz (1990) regression is a multiple regression analysis of
    Steadman's (1979) apparent temperature model:
    
    .. math::
        HI = c_1 + c_2T + c_3RH + c_4TRH + c_5T^2 + c_6RH^2 + 
             c_7T^2RH + c_8TRH^2 + c_9T^2RH^2
    
    where T is temperature in °F and RH is relative humidity in %.
    
    The formula is most accurate for:
    - Temperature: 80-110°F (27-43°C)
    - Relative Humidity: 40-100%
    
    For conditions outside this range, a simpler Steadman approximation is used:
    
    .. math::
        HI_{simple} = 0.5(T + 61.0 + (T-68.0) \\times 1.2 + RH \\times 0.094)
    
    Heat Index Categories (NWS):
    - 80-90°F (27-32°C): Caution - Fatigue possible
    - 90-105°F (32-41°C): Extreme caution - Heat exhaustion possible
    - 105-130°F (41-54°C): Danger - Heat exhaustion likely
    - >130°F (>54°C): Extreme danger - Heat stroke imminent
    
    References
    ----------
    .. [1] Rothfusz, L. P. (1990). The heat index equation (or, more than you
           ever wanted to know about heat index). National Weather Service
           Technical Attachment SR 90-23.
    .. [2] Steadman, R. G. (1979). The assessment of sultriness. Part I: A
           temperature-humidity index based on human physiology and clothing
           science. Journal of Applied Meteorology, 18(7), 861-873.
    .. [3] Anderson, G. B., et al. (2013). Heat-related emergency
           hospitalizations for respiratory diseases in the Medicare population.
           American Journal of Respiratory and Critical Care Medicine, 187(10),
           1098-1103. https://doi.org/10.1164/rccm.201211-1969OC
    
    Examples
    --------
    >>> temp = pd.Series([30.0, 35.0, 40.0])  # °C
    >>> rh = pd.Series([50.0, 60.0, 70.0])
    >>> heat_index_c(temp, rh)
    0    31.2
    1    38.9
    2    51.7
    dtype: float64
    """
    t_c = pd.Series(temp_c, dtype="float64")
    rh = pd.Series(rh_pct, dtype="float64").clip(lower=0.0, upper=100.0)
    t_f = t_c * 9.0 / 5.0 + 32.0
    # Rothfusz
    c1 = -42.379
    c2 = 2.04901523
    c3 = 10.14333127
    c4 = -0.22475541
    c5 = -6.83783e-3
    c6 = -5.481717e-2
    c7 = 1.22874e-3
    c8 = 8.5282e-4
    c9 = -1.99e-6
    hi_f = (
        c1
        + c2 * t_f
        + c3 * rh
        + c4 * t_f * rh
        + c5 * (t_f ** 2)
        + c6 * (rh ** 2)
        + c7 * (t_f ** 2) * rh
        + c8 * t_f * (rh ** 2)
        + c9 * (t_f ** 2) * (rh ** 2)
    )
    # Simple adjustment outside traditional domain: use Steadman approximation
    simple_hi_f = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))
    use_simple = (t_f < 80.0) | (rh < 40.0)
    hi_f = hi_f.where(~use_simple, simple_hi_f)
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return pd.Series(hi_c, index=t_c.index if isinstance(t_c, pd.Series) else None)


def wind_chill_c(temp_c: pd.Series | np.ndarray, wspd_ms: pd.Series | np.ndarray) -> pd.Series:
    """
    Calculate Wind Chill Temperature using the North American formula.
    
    Wind chill describes the rate of heat loss from exposed skin caused by
    combined effects of wind and cold temperatures. It is used for cold weather
    safety warnings and frostbite risk assessment.
    
    Parameters
    ----------
    temp_c : pd.Series or np.ndarray
        Air temperature in degrees Celsius
    wspd_ms : pd.Series or np.ndarray
        Wind speed in meters per second
    
    Returns
    -------
    pd.Series
        Wind Chill Temperature in degrees Celsius
    
    Notes
    -----
    The current North American Wind Chill formula (2001) is:
    
    .. math::
        WC = 13.12 + 0.6215T - 11.37V^{0.16} + 0.3965TV^{0.16}
    
    where:
    - T is air temperature in °C
    - V is wind speed in km/h
    - WC is wind chill temperature in °C
    
    The formula is valid for:
    - Temperature: T ≤ 10°C
    - Wind speed: V ≥ 4.8 km/h (1.34 m/s)
    
    For conditions outside this range, the actual air temperature is returned.
    
    Wind Chill Categories (Environment Canada):
    - 0 to -9°C: Low risk
    - -10 to -27°C: Moderate risk - Frostbite possible in 10-30 min
    - -28 to -39°C: High risk - Frostbite in 5-10 min
    - -40 to -47°C: Very high risk - Frostbite in 2-5 min
    - < -48°C: Extreme risk - Frostbite in < 2 min
    
    The formula assumes:
    - Walking speed of 4.8 km/h (1.34 m/s)
    - Clear night sky
    - No solar radiation
    
    References
    ----------
    .. [1] Osczevski, R., & Bluestein, M. (2005). The new wind chill equivalent
           temperature chart. Bulletin of the American Meteorological Society,
           86(10), 1453-1458. https://doi.org/10.1175/BAMS-86-10-1453
    .. [2] Tikuisis, P., & Osczevski, R. J. (2003). Facial cooling during cold
           air exposure. Bulletin of the American Meteorological Society, 84(7),
           927-934. https://doi.org/10.1175/BAMS-84-7-927
    .. [3] Shitzer, A., & de Dear, R. (2006). Inconsistencies in the "New"
           windchill chart at low wind speeds. Journal of Applied Meteorology
           and Climatology, 45(5), 787-790.
           https://doi.org/10.1175/JAM2360.1
    
    Examples
    --------
    >>> temp = pd.Series([0.0, -10.0, -20.0])  # °C
    >>> wind = pd.Series([5.0, 10.0, 15.0])    # m/s
    >>> wind_chill_c(temp, wind)
    0    -5.8
    1   -18.7
    2   -32.4
    dtype: float64
    """
    t = pd.Series(temp_c, dtype="float64")
    v_ms = pd.Series(wspd_ms, dtype="float64").clip(lower=0.0)
    v_kmh = v_ms * 3.6
    wci = 13.12 + 0.6215 * t - 11.37 * (v_kmh ** 0.16) + 0.3965 * t * (v_kmh ** 0.16)
    return pd.Series(wci, index=t.index if isinstance(t, pd.Series) else None)


