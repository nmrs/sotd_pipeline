#!/usr/bin/env python3
"""Data loading functionality for the report phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sotd.utils.file_io import load_json_data


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

    # Use unified file I/O utility for loading JSON data
    content = load_json_data(file_path)

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

    # Format previous month name
    prev_month_name = _get_month_name(prev_month)
    periods.append((prev_year, prev_month, f"{prev_month_name} {prev_year}"))

    # Previous year same month
    prev_year_month = year - 1, month
    current_month_name = _get_month_name(month)
    periods.append(
        (prev_year_month[0], prev_year_month[1], f"{current_month_name} {prev_year_month[0]}")
    )

    # 5 years ago same month
    five_years_ago = year - 5, month
    periods.append(
        (five_years_ago[0], five_years_ago[1], f"{current_month_name} {five_years_ago[0]}")
    )

    return periods


def _get_month_name(month: int) -> str:
    """Get month name abbreviation for a given month number.

    Args:
        month: Month number (1-12)

    Returns:
        Three-letter month abbreviation
    """
    month_names = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    return month_names.get(month, "Unknown")


def load_comparison_data(
    base_dir: Path, year: int, month: int, debug: bool = False
) -> Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load all available comparison data for delta calculations.

    Args:
        base_dir: Base directory containing aggregated data (should already be the
        aggregated directory)
        year: Current year
        month: Current month
        debug: Enable debug logging

    Returns:
        Dictionary mapping YYYY-MM format keys to (metadata, data) tuples
    """
    comparison_data = {}
    periods = get_comparison_periods(year, month)

    for comp_year, comp_month, description in periods:
        # Use base_dir directly since it should already point to the aggregated directory
        data = load_historical_data_from_dir(base_dir, comp_year, comp_month, debug)
        if data is not None:
            # Use YYYY-MM format key to match what table generator expects
            key = f"{comp_year:04d}-{comp_month:02d}"
            comparison_data[key] = data
            if debug:
                print(f"[DEBUG] Loaded comparison data for {key}: {description}")
        else:
            if debug:
                print(
                    f"[DEBUG] No comparison data available for {description}: "
                    f"{comp_year:04d}-{comp_month:02d}"
                )

    return comparison_data


def load_historical_data_from_dir(
    base_dir: Path, year: int, month: int, debug: bool = False
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load historical aggregated data from a specific directory for delta calculations.

    Args:
        base_dir: Directory containing aggregated data files
        year: Year of the historical data
        month: Month of the historical data
        debug: Enable debug logging

    Returns:
        Tuple of (metadata, data) if file exists, None otherwise
    """
    file_path = base_dir / f"{year:04d}-{month:02d}.json"

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
