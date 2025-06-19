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
        ValueError: If the JSON structure is invalid or data quality issues found
        json.JSONDecodeError: If the file is not valid JSON
        OSError: If there are file system issues
    """
    if not data_path.exists():
        if debug:
            print(f"[DEBUG] Enriched data file not found: {data_path}")
        raise FileNotFoundError(f"Enriched data file not found: {data_path}")

    if debug:
        print(f"[DEBUG] Loading enriched data from: {data_path}")

    # Check file size to detect obviously corrupted files
    try:
        file_size = data_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"Enriched data file is empty: {data_path}")
        if debug:
            print(f"[DEBUG] File size: {file_size} bytes")
    except OSError as e:
        raise OSError(f"Cannot access file {data_path}: {e}")

    try:
        with data_path.open("r", encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {data_path}: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Unicode decode error in {data_path}: {e}")
    except OSError as e:
        raise OSError(f"File system error reading {data_path}: {e}")

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

    # Validate metadata structure
    validate_metadata(metadata, data_path, debug)

    # Validate enriched record structure with detailed error reporting
    valid_records = []
    invalid_records = []

    for i, record in enumerate(data):
        if validate_enriched_record(record, i, debug):
            valid_records.append(record)
        else:
            invalid_records.append(record)

    # Data quality checks
    if len(valid_records) == 0:
        raise ValueError(f"No valid records found in {data_path}")

    if len(invalid_records) > 0:
        if debug:
            print(f"[DEBUG] Found {len(invalid_records)} invalid records out of {len(data)} total")
        if len(invalid_records) > len(valid_records):
            # If more than half the records are invalid, this is a serious data quality issue
            raise ValueError(
                f"Data quality issue in {data_path}: {len(invalid_records)} invalid records "
                f"out of {len(data)} total records"
            )

    if debug:
        print(f"[DEBUG] Loaded {len(valid_records)} valid enriched records from {data_path}")
        print(f"[DEBUG] Metadata keys: {list(metadata.keys())}")

    return metadata, valid_records


def validate_metadata(metadata: Dict[str, Any], data_path: Path, debug: bool = False) -> None:
    """
    Validate metadata structure and content.

    Args:
        metadata: The metadata dictionary to validate
        data_path: Path to the file for error reporting
        debug: Enable debug logging

    Raises:
        ValueError: If metadata is invalid
    """
    # Check for required metadata fields
    required_meta_fields = ["month", "extracted_at"]
    for field in required_meta_fields:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field '{field}' in {data_path}")

    # Validate month format (YYYY-MM)
    month = metadata.get("month")
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise ValueError(f"Invalid month format in metadata: {month} (expected YYYY-MM)")

    # Validate extracted_at timestamp
    extracted_at = metadata.get("extracted_at")
    if not isinstance(extracted_at, str):
        raise ValueError(f"Invalid extracted_at format in metadata: {extracted_at}")

    if debug:
        print(f"[DEBUG] Metadata validation passed for {data_path}")


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

    # Validate field types
    if not isinstance(record["id"], str):
        if debug:
            print(f"[DEBUG] Record {record_index}: 'id' should be string, got {type(record['id'])}")
        return False

    if not isinstance(record["author"], str):
        if debug:
            print(
                f"[DEBUG] Record {record_index}: 'author' should be string, "
                f"got {type(record['author'])}"
            )
        return False

    if not isinstance(record["created_utc"], (int, float)):
        if debug:
            print(
                f"[DEBUG] Record {record_index}: 'created_utc' should be numeric, "
                f"got {type(record['created_utc'])}"
            )
        return False

    if not isinstance(record["body"], str):
        if debug:
            print(
                f"[DEBUG] Record {record_index}: 'body' should be string, "
                f"got {type(record['body'])}"
            )
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

                # Validate match_type if present
                if "match_type" in matched_data:
                    match_type = matched_data["match_type"]
                    valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                    if not isinstance(match_type, str) or match_type not in valid_match_types:
                        if debug:
                            print(
                                f"[DEBUG] Record {record_index}: {field}.matched.match_type "
                                f"should be one of {valid_match_types}, got {match_type}"
                            )
                        return False

    return True


def validate_match_type(
    match_type: str, product_field: str, record_index: int, debug: bool = False
) -> bool:
    """
    Validate match_type values for product fields.

    Args:
        match_type: The match_type value to validate
        product_field: The product field name for error reporting
        record_index: Index of the record for error reporting
        debug: Enable debug logging

    Returns:
        True if valid, False otherwise
    """
    valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]

    if not isinstance(match_type, str):
        if debug:
            print(
                f"[DEBUG] Record {record_index}: {product_field}.match_type should be string, "
                f"got {type(match_type)}"
            )
        return False

    if match_type not in valid_match_types:
        if debug:
            print(
                f"[DEBUG] Record {record_index}: {product_field}.match_type should be one of "
                f"{valid_match_types}, got '{match_type}'"
            )
        return False

    return True
