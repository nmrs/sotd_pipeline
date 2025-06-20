#!/usr/bin/env python3
"""Data loading functionality for the report phase."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def get_aggregated_file_path(base_dir: Path, year: int, month: int) -> Path:
    """Get the path to the aggregated data file for a specific month."""
    return base_dir / "aggregated" / f"{year:04d}-{month:02d}.json"


def load_aggregated_data(
    file_path: Path, debug: bool = False
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load aggregated JSON data from file.

    Args:
        file_path: Path to the aggregated data file
        debug: Enable debug logging

    Returns:
        Tuple of (metadata, data) from the aggregated file

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        KeyError: If the file doesn't have the expected structure
    """
    if debug:
        print(f"[DEBUG] Loading aggregated data from: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"Aggregated data file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}", e.doc, e.pos)

    # Validate expected structure
    if not isinstance(content, dict):
        raise KeyError(f"Expected dict at root level in {file_path}")

    if "meta" not in content:
        raise KeyError(f"Missing 'meta' section in {file_path}")

    if "data" not in content:
        raise KeyError(f"Missing 'data' section in {file_path}")

    metadata = content["meta"]
    data = content["data"]

    # Validate metadata structure
    required_meta_fields = ["month", "total_shaves", "unique_shavers"]
    for field in required_meta_fields:
        if field not in metadata:
            raise KeyError(f"Missing required metadata field '{field}' in {file_path}")

    if debug:
        print(f"[DEBUG] Loaded data for {metadata['month']}")
        print(f"[DEBUG] Total shaves: {metadata['total_shaves']}")
        print(f"[DEBUG] Unique shavers: {metadata['unique_shavers']}")
        print(f"[DEBUG] Available categories: {list(data.keys())}")

    return metadata, data


def get_historical_file_path(base_dir: Path, year: int, month: int) -> Path:
    """Get the path to a historical aggregated data file."""
    return get_aggregated_file_path(base_dir, year, month)


def load_historical_data(
    base_dir: Path, year: int, month: int, debug: bool = False
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load historical aggregated data for delta calculations.

    Args:
        base_dir: Base directory containing aggregated data
        year: Year of the historical data
        month: Month of the historical data
        debug: Enable debug logging

    Returns:
        Tuple of (metadata, data) if file exists, None otherwise
    """
    file_path = get_historical_file_path(base_dir, year, month)

    if not file_path.exists():
        if debug:
            print(f"[DEBUG] Historical data not found: {file_path}")
        return None

    try:
        return load_aggregated_data(file_path, debug)
    except Exception as e:
        if debug:
            print(f"[DEBUG] Failed to load historical data from {file_path}: {e}")
        return None


def get_comparison_periods(year: int, month: int) -> List[Tuple[int, int, str]]:
    """Get comparison periods for delta calculations.

    Args:
        year: Current year
        month: Current month

    Returns:
        List of (year, month, description) tuples for comparison periods
    """
    periods = []

    # Previous month
    prev_year, prev_month = year, month - 1
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1
    periods.append((prev_year, prev_month, "previous month"))

    # Previous year same month
    prev_year_month = year - 1, month
    periods.append((prev_year_month[0], prev_year_month[1], "previous year"))

    # 5 years ago same month
    five_years_ago = year - 5, month
    periods.append((five_years_ago[0], five_years_ago[1], "5 years ago"))

    # Specific periods for hardware report (if current month is May 2025)
    if year == 2025 and month == 5:
        periods = [
            (2025, 4, "Apr 2025"),  # Previous month
            (2024, 5, "May 2024"),  # Previous year
            (
                2020,
                4,
                "Apr 2020",
            ),  # Use April 2020 instead of May 2020 (since May 2020 doesn't exist)
        ]

    return periods


def load_comparison_data(
    base_dir: Path, year: int, month: int, debug: bool = False
) -> Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load all available comparison data for delta calculations.

    Args:
        base_dir: Base directory containing aggregated data
        year: Current year
        month: Current month
        debug: Enable debug logging

    Returns:
        Dictionary mapping period description to (metadata, data) tuples
    """
    comparison_data = {}
    periods = get_comparison_periods(year, month)

    for comp_year, comp_month, description in periods:
        data = load_historical_data(base_dir, comp_year, comp_month, debug)
        if data is not None:
            comparison_data[description] = data
            if debug:
                print(
                    f"[DEBUG] Loaded comparison data for {description}: "
                    f"{comp_year:04d}-{comp_month:02d}"
                )
        else:
            if debug:
                print(
                    f"[DEBUG] No comparison data available for {description}: "
                    f"{comp_year:04d}-{comp_month:02d}"
                )

    return comparison_data
