import re
from typing import Any, Dict, List

import pandas as pd


def _determine_razor_format(razor_matched: Dict[str, Any], blade_matched: Dict[str, Any]) -> str:
    """Determine the final razor format using the old implementation logic.

    This function mirrors the logic from the old RazorFormatExtractor.get_name() method:
    1. Check if razor format matches "shavette (.*)" pattern
    2. Handle shavette + blade format combinations
    3. Handle Half DE detection
    4. Use fallback logic (razor format -> blade format -> default to DE)

    Args:
        razor_matched: Matched razor data with format field
        blade_matched: Matched blade data with format field

    Returns:
        The determined format string
    """
    razor_format = razor_matched.get("format", "").strip() if razor_matched else ""
    blade_format = blade_matched.get("format", "").strip() if blade_matched else ""

    # Constants from old implementation
    DE = "DE"
    HALF_DE = "Half DE"
    SHAVETTE = "Shavette"

    # Check if razor format matches "shavette (.*)" pattern
    if razor_format and re.match(r"shavette (.*)", razor_format, re.IGNORECASE):
        return razor_format

    # Handle shavette format combinations
    if razor_format == SHAVETTE:
        if not blade_format:
            blade_format = "Unspecified"
        # Assume random DE shavettes use half DE (from old implementation)
        elif blade_format == DE:
            blade_format = HALF_DE
        return f"{SHAVETTE} ({blade_format})"

    # Fix: Always return the full razor_format if it starts with 'Half DE'
    if razor_format and razor_format.startswith(HALF_DE):
        return razor_format

    # Handle Half DE detection
    if blade_format == DE:
        return DE
    elif blade_format:
        return blade_format
    elif razor_format:
        return razor_format

    # Default to DE (from old implementation)
    return DE


def aggregate_razor_formats(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor format data from enriched records using sophisticated format detection.

    This implementation mirrors the old RazorFormatExtractor logic to determine formats
    by combining razor and blade information, especially for shavettes.

    Returns a list of razor format aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor format aggregations with position, format, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract razor format data from records using sophisticated format detection
    format_data = []
    for record in records:
        razor = record.get("razor", {})
        blade = record.get("blade", {})

        razor_matched = razor.get("matched", {}) if razor else {}
        blade_matched = blade.get("matched", {}) if blade else {}

        # Skip if no matched razor data (but allow empty matched dict for fallback logic)
        if razor_matched is None:
            continue

        # Determine format using the sophisticated logic
        format_type = _determine_razor_format(razor_matched, blade_matched)
        author = record.get("author", "").strip()

        if format_type and author:
            format_data.append({"format": format_type, "author": author})

    if not format_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(format_data)

    # Group by format and calculate metrics
    grouped = df.groupby("format").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["format", "shaves", "unique_users"]

    # Sort by shaves desc, unique_users desc
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Add position field (1-based rank)
    grouped["position"] = range(1, len(grouped) + 1)

    # Convert to list of dictionaries
    result = []
    for _, row in grouped.iterrows():
        result.append(
            {
                "position": int(row["position"]),
                "format": row["format"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
