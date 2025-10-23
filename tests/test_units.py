"""Tests for units.py."""

import pytest
from metdatapy.units import (
    fahrenheit_to_c,
    mph_to_ms,
    kmh_to_ms,
    mbar_to_hpa,
    pa_to_hpa,
    identity,
    parse_unit_hint,
)


def test_fahrenheit_to_c():
    """Test Fahrenheit to Celsius conversion."""
    assert abs(fahrenheit_to_c(32.0) - 0.0) < 0.01
    assert abs(fahrenheit_to_c(212.0) - 100.0) < 0.01
    assert abs(fahrenheit_to_c(98.6) - 37.0) < 0.1


def test_mph_to_ms():
    """Test miles per hour to meters per second conversion."""
    assert abs(mph_to_ms(0.0) - 0.0) < 0.01
    # 1 mph ≈ 0.44704 m/s
    assert abs(mph_to_ms(10.0) - 4.4704) < 0.01


def test_kmh_to_ms():
    """Test kilometers per hour to meters per second conversion."""
    assert abs(kmh_to_ms(0.0) - 0.0) < 0.01
    # 36 km/h = 10 m/s
    assert abs(kmh_to_ms(36.0) - 10.0) < 0.01


def test_mbar_to_hpa():
    """Test millibar to hectopascal conversion."""
    # mbar and hPa are equivalent
    assert abs(mbar_to_hpa(1013.25) - 1013.25) < 0.01


def test_pa_to_hpa():
    """Test pascal to hectopascal conversion."""
    # 101325 Pa = 1013.25 hPa
    assert abs(pa_to_hpa(101325.0) - 1013.25) < 0.01


def test_identity():
    """Test identity conversion (no conversion)."""
    assert identity(42.0) == 42.0
    assert identity(0.0) == 0.0
    assert identity(-10.5) == -10.5


def test_parse_unit_hint_temperature():
    """Test parsing temperature unit hints."""
    assert parse_unit_hint("temp_f") == "F"
    assert parse_unit_hint("temperature_fahrenheit") == "F"
    assert parse_unit_hint("temp_c") == "C"
    assert parse_unit_hint("temperature_celsius") is None  # No explicit 'c' in pattern


def test_parse_unit_hint_pressure():
    """Test parsing pressure unit hints."""
    assert parse_unit_hint("pressure_mbar") == "mbar"
    assert parse_unit_hint("pres_mb") == "mbar"
    assert parse_unit_hint("pressure_pa") == "Pa"
    assert parse_unit_hint("pres_hpa") is None  # Default


def test_parse_unit_hint_wind_speed():
    """Test parsing wind speed unit hints."""
    assert parse_unit_hint("windspeed_mph") == "mph"
    assert parse_unit_hint("wind_kmh") == "km/h"
    assert parse_unit_hint("wspd_ms") is None  # Default


def test_parse_unit_hint_no_hint():
    """Test parsing when no unit hint is present."""
    assert parse_unit_hint("temperature") is None
    assert parse_unit_hint("pressure") is None
    assert parse_unit_hint("wind_speed") is None
    assert parse_unit_hint("random_column") is None


def test_parse_unit_hint_case_insensitive():
    """Test that unit hint parsing is case-insensitive."""
    assert parse_unit_hint("TEMP_F") == "F"
    assert parse_unit_hint("Pressure_MBAR") == "mbar"
    assert parse_unit_hint("WindSpeed_MPH") == "mph"


