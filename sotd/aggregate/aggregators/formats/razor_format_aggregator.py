from typing import Any, Dict, List

import pandas as pd


def aggregate_razor_formats(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor format data from enriched records.

    Returns a list of razor format aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor format aggregations with position, format, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract razor format data from records
    format_data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {})

        # Skip if no matched razor data or no format
        if not matched or not matched.get("format"):
            continue

        format_type = matched.get("format", "").strip()
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
