from typing import Any, Dict, List

import pandas as pd


def aggregate_straight_widths(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor width data from enriched records.

    Returns a list of straight razor width aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts width from razor.enriched.width.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor width aggregations with position, width, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract straight razor width data from records
    width_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no width
        if not enriched or not enriched.get("width"):
            continue

        width = enriched.get("width", "").strip()
        author = record.get("author", "").strip()

        if width and author:
            width_data.append({"width": width, "author": author})

    if not width_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(width_data)

    # Group by width and calculate metrics
    grouped = df.groupby("width").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["width", "shaves", "unique_users"]

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
                "width": row["width"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
