from typing import Any, Dict, List

from .aggregators.brush_specialized import (
    aggregate_fibers,
    aggregate_handle_makers,
    aggregate_knot_makers,
    aggregate_knot_sizes,
)
from .aggregators.core import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from .aggregators.cross_product import (
    aggregate_highest_use_count_per_blade,
    aggregate_razor_blade_combos,
)
from .aggregators.formats import aggregate_razor_formats
from .aggregators.manufacturers import (
    aggregate_blade_manufacturers,
    aggregate_razor_manufacturers,
    aggregate_soap_makers,
)
from .aggregators.razor_specialized import (
    aggregate_blackbird_plates,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_straight_grinds,
    aggregate_straight_points,
    aggregate_straight_widths,
    aggregate_super_speed_tips,
)
from .aggregators.users import aggregate_users
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
                    if matched is not None and isinstance(matched, dict):
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
    authors = set()
    for record in records:
        author = record.get("author")
        if author and isinstance(author, str) and author.strip():
            authors.add(author.strip())

    if len(authors) < 1:
        raise ValueError("No valid authors found in records")


def aggregate_all(records: List[Dict[str, Any]], month: str, debug: bool = False) -> Dict[str, Any]:
    """Aggregate all categories from enriched records.

    Args:
        records: List of enriched comment records
        month: Month being processed (YYYY-MM format)
        debug: Whether to show verbose debug output

    Returns:
        Dictionary containing all aggregated data with metadata
    """
    # Validate and normalize records
    records = validate_records(records)
    records = normalize_fields(records)
    check_data_quality(records)

    # Generate metadata
    meta = calculate_metadata(records, month)

    # Run all aggregators with minimal debug output
    aggregated_data = {
        "meta": meta,
        "data": {},
    }

    if debug:
        print("[DEBUG] Running 22 aggregators...")

    # Core product aggregations
    aggregated_data["data"]["razors"] = aggregate_razors(records)
    aggregated_data["data"]["blades"] = aggregate_blades(records)
    aggregated_data["data"]["brushes"] = aggregate_brushes(records)
    aggregated_data["data"]["soaps"] = aggregate_soaps(records)

    # Manufacturer aggregations
    aggregated_data["data"]["razor_manufacturers"] = aggregate_razor_manufacturers(records)
    aggregated_data["data"]["blade_manufacturers"] = aggregate_blade_manufacturers(records)
    aggregated_data["data"]["soap_makers"] = aggregate_soap_makers(records)

    # Format aggregations
    aggregated_data["data"]["razor_formats"] = aggregate_razor_formats(records)

    # Brush specialized aggregations
    aggregated_data["data"]["brush_handle_makers"] = aggregate_handle_makers(records)
    aggregated_data["data"]["brush_knot_makers"] = aggregate_knot_makers(records)
    aggregated_data["data"]["brush_fibers"] = aggregate_fibers(records)
    aggregated_data["data"]["brush_knot_sizes"] = aggregate_knot_sizes(records)

    # Razor specialized aggregations
    aggregated_data["data"]["blackbird_plates"] = aggregate_blackbird_plates(records)
    aggregated_data["data"]["christopher_bradley_plates"] = aggregate_christopher_bradley_plates(
        records
    )
    aggregated_data["data"]["game_changer_plates"] = aggregate_game_changer_plates(records)
    aggregated_data["data"]["super_speed_tips"] = aggregate_super_speed_tips(records)
    aggregated_data["data"]["straight_widths"] = aggregate_straight_widths(records)
    aggregated_data["data"]["straight_grinds"] = aggregate_straight_grinds(records)
    aggregated_data["data"]["straight_points"] = aggregate_straight_points(records)

    # User aggregations
    aggregated_data["data"]["users"] = aggregate_users(records)

    # Cross-product aggregations
    aggregated_data["data"]["razor_blade_combinations"] = aggregate_razor_blade_combos(records)
    aggregated_data["data"]["highest_use_count_per_blade"] = aggregate_highest_use_count_per_blade(
        records
    )

    return aggregated_data
