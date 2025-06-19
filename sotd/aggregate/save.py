"""File I/O functionality for the aggregate phase."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def get_aggregated_file_path(base_dir: Path, year: int, month: int) -> Path:
    """
    Get the path to the aggregated data file for a specific month.

    Args:
        base_dir: Base data directory
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Path to the aggregated JSON file
    """
    return base_dir / "aggregated" / f"{year:04d}-{month:02d}.json"


def save_aggregated_data(
    results: Dict[str, Any],
    output_path: Path,
    force: bool = False,
    debug: bool = False,
) -> None:
    """
    Save aggregated data to JSON file with proper structure.

    Args:
        results: Aggregation results from process_month
        output_path: Path to save the aggregated data
        force: Force overwrite existing file
        debug: Enable debug logging

    Raises:
        FileExistsError: If file exists and force=False
        OSError: If file cannot be written
    """
    if output_path.exists() and not force:
        raise FileExistsError(f"Aggregated file already exists: {output_path}")

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare the output structure
    month_str = f"{results['year']:04d}-{results['month']:02d}"
    aggregated_at = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    if results["status"] == "success":
        # Successful aggregation
        basic_metrics = results["basic_metrics"]
        aggregations = results["aggregations"]

        output_data = {
            "meta": {
                "month": month_str,
                "aggregated_at": aggregated_at,
                "total_shaves": basic_metrics["total_shaves"],
                "unique_shavers": basic_metrics["unique_shavers"],
                "avg_shaves_per_user": basic_metrics["avg_shaves_per_user"],
                "categories": ["razors", "blades", "soaps", "brushes", "users"],
                "summary": results["summary"],
            },
            "data": {
                "razors": aggregations["razors"],
                "blades": aggregations["blades"],
                "soaps": aggregations["soaps"],
                "brushes": aggregations["brushes"],
                "users": aggregations["users"],
            },
        }
    else:
        # Failed or skipped aggregation
        output_data = {
            "meta": {
                "month": month_str,
                "aggregated_at": aggregated_at,
                "status": results["status"],
                "error": results.get("error", ""),
                "reason": results.get("reason", ""),
            },
            "data": {},
        }

    # Write the file
    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        if debug:
            print(f"[DEBUG] Saved aggregated data to: {output_path}")

    except OSError as e:
        raise OSError(f"Failed to write aggregated file {output_path}: {e}")


def load_aggregated_data(data_path: Path, debug: bool = False) -> Dict[str, Any]:
    """
    Load aggregated JSON data from the specified path.

    Args:
        data_path: Path to the aggregated JSON file
        debug: Enable debug logging

    Returns:
        Dictionary containing the aggregated data

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the JSON structure is invalid
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not data_path.exists():
        if debug:
            print(f"[DEBUG] Aggregated data file not found: {data_path}")
        raise FileNotFoundError(f"Aggregated data file not found: {data_path}")

    if debug:
        print(f"[DEBUG] Loading aggregated data from: {data_path}")

    try:
        with data_path.open("r", encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {data_path}: {e}")

    # Validate structure
    if not isinstance(content, dict):
        raise ValueError(f"Expected dict at root level in {data_path}, got {type(content)}")

    if "meta" not in content:
        raise ValueError(f"Missing 'meta' section in {data_path}")

    if "data" not in content:
        raise ValueError(f"Missing 'data' section in {data_path}")

    metadata = content["meta"]
    data = content["data"]

    if not isinstance(metadata, dict):
        raise ValueError(f"Expected dict for 'meta' in {data_path}, got {type(metadata)}")

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict for 'data' in {data_path}, got {type(data)}")

    if debug:
        print(f"[DEBUG] Loaded aggregated data from {data_path}")
        print(f"[DEBUG] Metadata keys: {list(metadata.keys())}")
        print(f"[DEBUG] Data keys: {list(data.keys())}")

    return content


def validate_aggregated_data(data: Dict[str, Any], debug: bool = False) -> bool:
    """
    Validate aggregated data structure.

    Args:
        data: Aggregated data to validate
        debug: Enable debug logging

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        if debug:
            print("[DEBUG] Expected dict at root level")
        return False

    if "meta" not in data:
        if debug:
            print("[DEBUG] Missing 'meta' section")
        return False

    if "data" not in data:
        if debug:
            print("[DEBUG] Missing 'data' section")
        return False

    metadata = data["meta"]
    content_data = data["data"]

    if not isinstance(metadata, dict):
        if debug:
            print("[DEBUG] Expected dict for 'meta'")
        return False

    if not isinstance(content_data, dict):
        if debug:
            print("[DEBUG] Expected dict for 'data'")
        return False

    # Check required metadata fields
    required_meta_fields = ["month", "aggregated_at"]
    for field in required_meta_fields:
        if field not in metadata:
            if debug:
                print(f"[DEBUG] Missing required metadata field: {field}")
            return False

    # Check for expected data categories
    expected_categories = ["razors", "blades", "soaps", "brushes", "users"]
    for category in expected_categories:
        if category in content_data:
            category_data = content_data[category]
            if not isinstance(category_data, list):
                if debug:
                    print(
                        f"[DEBUG] Expected list for category '{category}', "
                        f"got {type(category_data)}"
                    )
                return False

    return True
