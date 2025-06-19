"""Data loading functionality for the aggregate phase."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_enriched_data(
    data_path: Path, debug: bool = False
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Load enriched JSON data from the specified path.

    Args:
        data_path: Path to the enriched JSON file
        debug: Enable debug logging

    Returns:
        Tuple of (metadata, data) where metadata is a dict and data is a list of enriched records

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the JSON structure is invalid
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not data_path.exists():
        if debug:
            print(f"[DEBUG] Enriched data file not found: {data_path}")
        raise FileNotFoundError(f"Enriched data file not found: {data_path}")

    if debug:
        print(f"[DEBUG] Loading enriched data from: {data_path}")

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

    if not isinstance(data, list):
        raise ValueError(f"Expected list for 'data' in {data_path}, got {type(data)}")

    # Validate enriched record structure
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"Expected dict for record {i} in {data_path}, got {type(record)}")

        # Check for required fields in enriched records
        required_fields = ["id", "author", "created_utc", "body"]
        for field in required_fields:
            if field not in record:
                raise ValueError(f"Missing required field '{field}' in record {i} in {data_path}")

        # Check for product fields (at least one should be present)
        product_fields = ["razor", "blade", "soap", "brush"]
        if not any(field in record for field in product_fields):
            if debug:
                print(f"[DEBUG] Record {i} has no product fields: {list(record.keys())}")

    if debug:
        print(f"[DEBUG] Loaded {len(data)} enriched records from {data_path}")
        print(f"[DEBUG] Metadata keys: {list(metadata.keys())}")

    return metadata, data


def get_enriched_file_path(base_dir: Path, year: int, month: int) -> Path:
    """
    Get the path to the enriched data file for a specific month.

    Args:
        base_dir: Base data directory
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Path to the enriched JSON file
    """
    return base_dir / "enriched" / f"{year:04d}-{month:02d}.json"


def validate_enriched_record(
    record: Dict[str, Any], record_index: int, debug: bool = False
) -> bool:
    """
    Validate a single enriched record structure.

    Args:
        record: The enriched record to validate
        record_index: Index of the record for error reporting
        debug: Enable debug logging

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(record, dict):
        if debug:
            print(f"[DEBUG] Record {record_index}: Expected dict, got {type(record)}")
        return False

    # Check required fields
    required_fields = ["id", "author", "created_utc", "body"]
    for field in required_fields:
        if field not in record:
            if debug:
                print(f"[DEBUG] Record {record_index}: Missing required field '{field}'")
            return False

    # Check product fields structure
    product_fields = ["razor", "blade", "soap", "brush"]
    for field in product_fields:
        if field in record:
            product_data = record[field]
            if not isinstance(product_data, dict):
                if debug:
                    print(
                        f"[DEBUG] Record {record_index}: {field} should be dict, "
                        f"got {type(product_data)}"
                    )
                return False

            # Check for matched field in product data
            if "matched" in product_data:
                matched_data = product_data["matched"]
                if not isinstance(matched_data, dict):
                    if debug:
                        print(
                            f"[DEBUG] Record {record_index}: {field}.matched should be dict, "
                            f"got {type(matched_data)}"
                        )
                    return False

    return True
