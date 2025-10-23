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
    """Test parsing temperature unit hints from column headers."""
    assert parse_unit_hint("Temperature (°F)") == "F"
    assert parse_unit_hint("Temperature (F)") == "F"
    assert parse_unit_hint("Temp degF") == "F"
    assert parse_unit_hint("Temperature (°C)") == "C"
    assert parse_unit_hint("Temp C") == "C"
    assert parse_unit_hint("temperature") is None  # No unit hint


def test_parse_unit_hint_pressure():
    """Test parsing pressure unit hints from column headers."""
    assert parse_unit_hint("Pressure (mbar)") == "mbar"
    assert parse_unit_hint("Pres mb") == "mbar"
    assert parse_unit_hint("Pressure (hPa)") == "hpa"
    assert parse_unit_hint("Pressure Pa") == "pa"
    assert parse_unit_hint("pressure") is None  # No unit hint


def test_parse_unit_hint_wind_speed():
    """Test parsing wind speed unit hints from column headers."""
    assert parse_unit_hint("Wind Speed (mph)") == "mph"
    assert parse_unit_hint("Wind km/h") == "km/h"
    assert parse_unit_hint("Wind kph") == "km/h"
    assert parse_unit_hint("Wind m/s") == "m/s"
    assert parse_unit_hint("wind_speed") is None  # No unit hint


def test_parse_unit_hint_no_hint():
    """Test parsing when no unit hint is present."""
    assert parse_unit_hint("temperature") is None
    assert parse_unit_hint("pressure") is None
    assert parse_unit_hint("wind_speed") is None
    assert parse_unit_hint("random_column") is None


def test_parse_unit_hint_case_insensitive():
    """Test that unit hint parsing is case-insensitive."""
    assert parse_unit_hint("TEMP (F)") == "F"
    assert parse_unit_hint("Pressure (MBAR)") == "mbar"
    assert parse_unit_hint("WindSpeed MPH") == "mph"


