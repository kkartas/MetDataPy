"""MetDataPy package init."""

from .core import WeatherSet
from .mapper import Mapper, Detector
from .mlprep import make_supervised, time_split, fit_scaler, apply_scaler
from .qc import qc_range, qc_spike, qc_flatline, qc_consistency

__all__ = [
    "WeatherSet",
    "Mapper",
    "Detector",
    "make_supervised",
    "time_split",
    "fit_scaler",
    "apply_scaler",
    "qc_range",
    "qc_spike",
    "qc_flatline",
    "qc_consistency",
]

__version__ = "1.0.0"

