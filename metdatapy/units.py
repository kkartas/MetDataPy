import re
from typing import Optional


def fahrenheit_to_c(value):
    return (value - 32.0) * 5.0 / 9.0


def identity(x):
    return x


def mph_to_ms(value):
    return value * 0.44704


def kmh_to_ms(value):
    return value * (1000.0 / 3600.0)


def mbar_to_hpa(value):
    return value


def pa_to_hpa(value):
    return value / 100.0


def parse_unit_hint(text: str) -> Optional[str]:
    t = (text or "").lower()
    if re.search(r"\b(°f|degf|f)\b", t):
        return "F"
    if re.search(r"\b(°c|degc|c)\b", t):
        return "C"
    if re.search(r"\b(hpa)\b", t):
        return "hpa"
    if re.search(r"\b(mbar|mb)\b", t):
        return "mbar"
    if re.search(r"\b(pa)\b", t):
        return "pa"
    if re.search(r"\b(m/s|mps)\b", t):
        return "m/s"
    if re.search(r"\b(km/?h|kph)\b", t):
        return "km/h"
    if re.search(r"\b(mph)\b", t):
        return "mph"
    if re.search(r"\b(mm)\b", t):
        return "mm"
    if re.search(r"\b(in|inch|inches)\b", t):
        return "inch"
    return None


