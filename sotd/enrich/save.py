"""
File I/O operations for the enrich phase.

Handles reading matched data and writing enriched data with comprehensive metadata.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sotd.utils.file_io import load_json_data, save_json_data


def load_matched_data(file_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Load matched data from a JSON file.

    Args:
        file_path: Path to the matched data file

    Returns:
        Tuple of (metadata, data)

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the JSON structure is invalid or data quality issues found
        json.JSONDecodeError: If the file is not valid JSON
        OSError: If there are file system issues
    """
    if not file_path.exists():
        # Fail fast on missing required files - this is a configuration error
        raise FileNotFoundError(f"Matched data file not found: {file_path}")

    try:
        content = load_json_data(file_path)
    except (json.JSONDecodeError, OSError) as e:
        # Re-raise with the same error messages expected by tests
        if isinstance(e, json.JSONDecodeError):
            raise ValueError(f"Invalid JSON in matched data file {file_path}: {e}")
        else:
            raise OSError(f"File system error reading {file_path}: {e}")

    # Fail fast on invalid data structure
    if not isinstance(content, dict):
        raise ValueError(f"Expected dict at root level in {file_path}, got {type(content)}")

    if "data" not in content:
        raise ValueError(f"Missing 'data' section in {file_path}")

    metadata = content.get("meta", {})
    data = content.get("data", [])

    # Fail fast on invalid data types
    if not isinstance(data, list):
        raise ValueError(f"Expected list for 'data' in {file_path}, got {type(data)}")

    if not isinstance(metadata, dict):
        raise ValueError(f"Expected dict for 'meta' in {file_path}, got {type(metadata)}")

    return metadata, data


def save_enriched_data(
    file_path: Path,
    enriched_data: List[Dict[str, Any]],
    original_metadata: Dict[str, Any],
    enrichment_stats: Dict[str, Any],
    force: bool = False,
) -> None:
    """
    Save enriched data to a JSON file with comprehensive metadata.

    Args:
        file_path: Path where to save the enriched data
        enriched_data: List of enriched comment records
        original_metadata: Metadata from the matched data
        enrichment_stats: Statistics about the enrichment process
        force: Whether to overwrite existing files
    """
    # Create output directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file if force is True
    if force and file_path.exists():
        file_path.unlink()

    # Generate enrichment metadata
    enrichment_metadata = {
        "month": original_metadata.get("month", ""),
        "extracted_at": original_metadata.get("extracted_at", ""),
        "enriched_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "records_input": len(enriched_data),
        "record_count": len(enriched_data),
        "fields": ["razor", "blade", "soap", "brush"],
        **enrichment_stats,
    }

    # Prepare output structure
    output = {
        "data": enriched_data,
        "meta": enrichment_metadata,
    }

    # Write to file using unified utilities
    save_json_data(output, file_path, indent=2)


def calculate_enrichment_stats(enriched_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about the enrichment process.

    Args:
        enriched_data: List of enriched comment records

    Returns:
        Dictionary with enrichment statistics
    """
    stats = {
        "blade_enriched": 0,
        "razor_enriched": 0,
        "brush_enriched": 0,
        "soap_enriched": 0,
        "total_enriched": 0,
    }

    for comment in enriched_data:
        enriched_any = False
        for field in ("blade", "razor", "brush", "soap"):
            product = comment.get(field)
            if isinstance(product, dict) and "enriched" in product and product["enriched"]:
                stats[f"{field}_enriched"] += 1
                enriched_any = True
        if enriched_any:
            stats["total_enriched"] += 1

    return stats
