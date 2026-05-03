from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping, Optional, Union

import pandas as pd

from .core import WeatherSet
from .io import read_csv
from .mapper import Mapper


MappingConfig = Union[str, Path, Mapping]


def _load_mapping(mapping_config: MappingConfig) -> dict:
    if isinstance(mapping_config, (str, Path)):
        return Mapper.load(str(mapping_config))
    return deepcopy(dict(mapping_config))


def _with_timezone(mapping: dict, timezone: Optional[str]) -> dict:
    mapping = deepcopy(mapping)
    if timezone:
        mapping.setdefault("ts", {})
        if not mapping["ts"].get("timezone"):
            mapping["ts"]["timezone"] = timezone
    return mapping


def read_weathercloud_csv(
    path: Union[str, Path],
    mapping_config: Optional[MappingConfig] = None,
    timezone: str = "Europe/Athens",
    delimiter: Optional[str] = None,
) -> pd.DataFrame:
    """Read a Weathercloud CSV export.

    If ``mapping_config`` is omitted, the raw source columns are returned. If a
    mapping is supplied, the output is canonicalized, UTC-indexed, and unit
    normalized.
    """
    df = read_csv(str(path), delimiter=delimiter)
    if mapping_config is None:
        return df

    mapping = _with_timezone(_load_mapping(mapping_config), timezone)
    return WeatherSet.from_mapping(df, mapping).normalize_units(mapping).to_dataframe()


def read_weathercloud_directory(
    path: Union[str, Path],
    mapping_config: MappingConfig,
    timezone: str = "Europe/Athens",
    delimiter: Optional[str] = None,
) -> pd.DataFrame:
    """Load and concatenate all Weathercloud CSV exports in a directory."""
    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"Weathercloud path is not a directory: {directory}")

    csv_paths = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".csv")
    if not csv_paths:
        raise ValueError(f"No Weathercloud CSV files found in {directory}")

    mapping = _with_timezone(_load_mapping(mapping_config), timezone)
    frames = [
        read_weathercloud_csv(csv_path, mapping, timezone=timezone, delimiter=delimiter)
        for csv_path in csv_paths
    ]
    out = pd.concat(frames).sort_index()
    out.index.name = "ts_utc"
    return out
