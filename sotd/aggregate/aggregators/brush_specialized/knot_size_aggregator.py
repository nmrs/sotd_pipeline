from typing import Any, Dict, List

import pandas as pd


def aggregate_knot_sizes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush knot size data from enriched records.

    Returns a list of knot size aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Uses brush.matched.knot_size_mm with fallback to brush.enriched.knot_size_mm.

    Args:
        records: List of enriched comment records

    Returns:
        List of knot size aggregations with position, knot_size_mm, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract knot size data from records
    knot_size_data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched")
        enriched = brush.get("enriched")

        # Ensure matched and enriched are dicts
        matched = matched if isinstance(matched, dict) else {}
        enriched = enriched if isinstance(enriched, dict) else {}

        # Try matched.knot_size_mm first, then fallback to enriched.knot_size_mm
        knot_size_mm = matched.get("knot_size_mm") or enriched.get("knot_size_mm")

        # Skip if no knot size data
        if not knot_size_mm:
            continue

        author = record.get("author", "").strip()

        if knot_size_mm and author:
            knot_size_data.append({"knot_size_mm": knot_size_mm, "author": author})

    if not knot_size_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(knot_size_data)

    # Group by knot_size_mm and calculate metrics
    grouped = df.groupby("knot_size_mm").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["knot_size_mm", "shaves", "unique_users"]

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
                "knot_size_mm": float(row["knot_size_mm"]),
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
