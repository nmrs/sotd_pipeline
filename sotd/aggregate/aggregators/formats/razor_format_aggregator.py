from typing import Any, Dict, List

import pandas as pd


def aggregate_razor_formats(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor format data from enriched records.

    This implementation uses the format that was already determined during the enrich phase,
    rather than re-determining it. Format determination logic has been moved to the enrich
    phase (RazorFormatEnricher) to ensure consistency and avoid duplication.

    Returns a list of razor format aggregations sorted by shaves desc, unique_users desc.
    Each item includes rank field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor format aggregations with rank, format, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract razor format data from records
    format_data = []
    for record in records:
        razor = record.get("razor", {})
        razor_matched = razor.get("matched") if razor else None

        # Skip records with no razor match at all
        if razor_matched is None:
            continue

        # Use enriched format if available, otherwise fall back to matched format
        # This supports backward compatibility with records that haven't been enriched yet
        razor_enriched = razor.get("enriched", {})
        razor_format = razor_enriched.get("format") or razor_matched.get("format", "").strip()

        # Skip if no format determined
        if not razor_format:
            continue

        author = record.get("author", "").strip()

        if razor_format and author:
            format_data.append({"format": razor_format, "author": author})

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

    # Add rank field (1-based rank)
    grouped["rank"] = range(1, len(grouped) + 1)

    # Convert to list of dictionaries
    result = []
    for _, row in grouped.iterrows():
        result.append(
            {
                "rank": int(row["rank"]),
                "format": row["format"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
