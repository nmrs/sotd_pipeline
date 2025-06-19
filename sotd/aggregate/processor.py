from typing import Any, Dict, List

from .aggregators.core import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from .aggregators.formats import aggregate_razor_formats
from .aggregators.manufacturers import (
    aggregate_blade_manufacturers,
    aggregate_razor_manufacturers,
    aggregate_soap_makers,
)
from .utils.metrics import calculate_metadata


def validate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and clean enriched records. Raise ValueError on data quality issues."""
    if not isinstance(records, list):
        raise ValueError("Records must be a list")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each record must be a dictionary")

        # Check for required fields
        if "author" not in record:
            raise ValueError("Each record must have an 'author' field")

    return records


def normalize_fields(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize fields (case, whitespace, etc.) in records."""
    normalized = []
    for record in records:
        normalized_record = record.copy()

        # Normalize author field
        if "author" in normalized_record:
            normalized_record["author"] = normalized_record["author"].strip()

        # Normalize product fields
        for product_type in ["razor", "blade", "brush", "soap"]:
            if product_type in normalized_record:
                product = normalized_record[product_type]
                if isinstance(product, dict) and "matched" in product:
                    matched = product["matched"]
                    for key, value in matched.items():
                        if isinstance(value, str):
                            matched[key] = value.strip()

        normalized.append(normalized_record)

    return normalized


def check_data_quality(records: list[dict[str, Any]]) -> None:
    """Perform data quality checks and raise ValueError if issues are found."""
    if not records:
        return

    # Check for reasonable data volume
    if len(records) < 1:
        raise ValueError("No records to process")

    # Check for reasonable number of unique authors
    authors = set(record.get("author", "") for record in records)
    if len(authors) < 1:
        raise ValueError("No valid authors found in records")


def aggregate_all(records: List[Dict[str, Any]], month: str) -> Dict[str, Any]:
    """Aggregate all categories from enriched records.

    Args:
        records: List of enriched comment records
        month: Month being processed (YYYY-MM format)

    Returns:
        Dictionary containing all aggregated data with metadata
    """
    # Validate and normalize records
    records = validate_records(records)
    records = normalize_fields(records)
    check_data_quality(records)

    # Generate metadata
    meta = calculate_metadata(records, month)

    # Run all aggregators
    aggregated_data = {
        "meta": meta,
        "data": {
            # Core product aggregations
            "razors": aggregate_razors(records),
            "blades": aggregate_blades(records),
            "brushes": aggregate_brushes(records),
            "soaps": aggregate_soaps(records),
            # Manufacturer aggregations
            "razor_manufacturers": aggregate_razor_manufacturers(records),
            "blade_manufacturers": aggregate_blade_manufacturers(records),
            "soap_makers": aggregate_soap_makers(records),
            # Format aggregations
            "razor_formats": aggregate_razor_formats(records),
        },
    }

    return aggregated_data
