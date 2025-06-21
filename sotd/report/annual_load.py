#!/usr/bin/env python3
"""Annual data loading functionality for the report phase."""

from pathlib import Path
from typing import Any, Dict, Tuple, Union

from sotd.utils.file_io import load_json_data


def get_annual_file_path(base_dir: Path, year: Union[str, int]) -> Path:
    """Get the path to the annual aggregated data file for a specific year.

    Args:
        base_dir: Base directory containing aggregated data
        year: Year to get file path for (YYYY format)

    Returns:
        Path to the annual aggregated data file
    """
    year_str = str(year)
    return base_dir / "aggregated" / "annual" / f"{year_str}.json"


def validate_annual_metadata(metadata: Dict[str, Any]) -> None:
    """Validate annual metadata structure.

    Args:
        metadata: Annual metadata to validate

    Raises:
        ValueError: If metadata is invalid
    """
    required_fields = [
        "year",
        "total_shaves",
        "unique_shavers",
        "included_months",
        "missing_months",
    ]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"Annual metadata must contain '{field}' field")

    # Validate field types
    if not isinstance(metadata["total_shaves"], (int, float)):
        raise ValueError("Annual metadata 'total_shaves' must be a number")

    if not isinstance(metadata["unique_shavers"], (int, float)):
        raise ValueError("Annual metadata 'unique_shavers' must be a number")

    if not isinstance(metadata["included_months"], list):
        raise ValueError("Annual metadata 'included_months' must be a list")

    if not isinstance(metadata["missing_months"], list):
        raise ValueError("Annual metadata 'missing_months' must be a list")


def validate_annual_data_structure(data: Dict[str, Any]) -> None:
    """Validate annual data structure.

    Args:
        data: Annual data to validate

    Raises:
        ValueError: If data structure is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Annual data must be a dictionary")

    if "metadata" not in data:
        raise ValueError("Annual data must contain 'metadata' section")

    # Validate metadata
    validate_annual_metadata(data["metadata"])

    # Validate required product categories
    required_categories = ["razors", "blades", "brushes", "soaps"]
    for category in required_categories:
        if category not in data:
            raise ValueError("Annual data must contain all required product categories")


def load_annual_data(file_path: Path, debug: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load annual aggregated JSON data from file.

    Args:
        file_path: Path to the annual aggregated data file
        debug: Enable debug logging

    Returns:
        Tuple of (metadata, data) from the annual file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If the file doesn't have the expected structure
        ValueError: If the data structure is invalid
    """
    if debug:
        print(f"[DEBUG] Loading annual aggregated data from: {file_path}")

    # Use unified file I/O utility for loading JSON data
    content = load_json_data(file_path)

    # Validate expected structure
    if not isinstance(content, dict):
        raise KeyError(f"Expected dict at root level in {file_path}")

    if "metadata" not in content:
        raise KeyError(f"Missing 'metadata' section in {file_path}")

    metadata = content["metadata"]
    data = content

    # Validate metadata structure
    required_meta_fields = [
        "year",
        "total_shaves",
        "unique_shavers",
        "included_months",
        "missing_months",
    ]
    for field in required_meta_fields:
        if field not in metadata:
            raise KeyError(f"Missing required metadata field '{field}' in {file_path}")

    # Validate data structure
    required_categories = ["razors", "blades", "brushes", "soaps"]
    for category in required_categories:
        if category not in data:
            raise KeyError(f"Missing required product category '{category}' in {file_path}")

    if debug:
        print(f"[DEBUG] Loaded annual data for {metadata['year']}")
        print(f"[DEBUG] Total shaves: {metadata['total_shaves']}")
        print(f"[DEBUG] Unique shavers: {metadata['unique_shavers']}")
        print(f"[DEBUG] Included months: {len(metadata['included_months'])}")
        print(f"[DEBUG] Missing months: {len(metadata['missing_months'])}")
        print(f"[DEBUG] Available categories: {list(data.keys())}")

    return metadata, data
