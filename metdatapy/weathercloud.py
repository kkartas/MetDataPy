from __future__ import annotations

import warnings
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
    nonexistent: str = "shift_forward",
    ambiguous: str = "infer",
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
    return (
        WeatherSet.from_mapping(
            df,
            mapping,
            nonexistent=nonexistent,
            ambiguous=ambiguous,
        )
        .normalize_units(mapping)
        .to_dataframe()
    )


def read_weathercloud_directory(
    path: Union[str, Path],
    mapping_config: MappingConfig,
    timezone: str = "Europe/Athens",
    delimiter: Optional[str] = None,
    duplicate_policy: str = "keep_first",
    return_report: bool = False,
    nonexistent: str = "shift_forward",
    ambiguous: str = "infer",
) -> Union[pd.DataFrame, tuple[pd.DataFrame, dict]]:
    """Load and concatenate all Weathercloud CSV exports in a directory."""
    valid_duplicate_policies = {"keep_first", "keep_last", "drop", "raise", "keep_all"}
    if duplicate_policy not in valid_duplicate_policies:
        raise ValueError(
            f"Unknown duplicate_policy '{duplicate_policy}'. "
            f"Expected one of {sorted(valid_duplicate_policies)}"
        )

    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"Weathercloud path is not a directory: {directory}")

    csv_paths = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".csv")
    if not csv_paths:
        raise ValueError(f"No Weathercloud CSV files found in {directory}")

    mapping = _with_timezone(_load_mapping(mapping_config), timezone)
    frames = [
        read_weathercloud_csv(
            csv_path,
            mapping,
            timezone=timezone,
            delimiter=delimiter,
            nonexistent=nonexistent,
            ambiguous=ambiguous,
        )
        for csv_path in csv_paths
    ]
    out = pd.concat(frames).sort_index(kind="mergesort")
    rows_before = len(out)

    duplicate_mask = out.index.duplicated(keep=False)
    duplicate_rows = int(out.index.duplicated(keep="first").sum())
    duplicate_timestamp_count = int(out.index[duplicate_mask].nunique()) if duplicate_mask.any() else 0

    if duplicate_timestamp_count:
        message = (
            f"Found {duplicate_rows} duplicate Weathercloud timestamps; "
            f"duplicate_policy='{duplicate_policy}'"
        )
        if duplicate_policy == "raise":
            raise ValueError(message)
        warnings.warn(message, UserWarning, stacklevel=2)

        if duplicate_policy == "keep_first":
            out = out[~out.index.duplicated(keep="first")]
        elif duplicate_policy == "keep_last":
            out = out[~out.index.duplicated(keep="last")]
        elif duplicate_policy == "drop":
            out = out[~duplicate_mask]
        elif duplicate_policy == "keep_all":
            pass

    out.index.name = "ts_utc"

    if return_report:
        report = {
            "files_read": [p.name for p in csv_paths],
            "rows_before_duplicate_handling": rows_before,
            "rows_after_duplicate_handling": len(out),
            "duplicate_rows": duplicate_rows,
            "duplicate_timestamp_count": duplicate_timestamp_count,
            "duplicate_policy": duplicate_policy,
        }
        return out, report

    return out
