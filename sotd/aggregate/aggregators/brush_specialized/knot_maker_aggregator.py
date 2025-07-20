from typing import Any, Dict, List

import pandas as pd


def aggregate_knot_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush knot maker data from enriched records.

    Returns a list of knot maker aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of knot maker aggregations with position, brand, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract knot maker data from records
    knot_maker_data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {})

        # Skip if no matched brush data
        if not matched:
            continue

        # Get knot maker from knot section (all brushes have consistent handle/knot sections)
        knot_section = matched.get("knot", {})
        if not knot_section or not isinstance(knot_section, dict):
            continue

        brand = knot_section.get("brand")
        if not brand:
            continue

        brand = brand.strip()
        author = record.get("author", "").strip()

        if brand and author:
            knot_maker_data.append({"brand": brand, "author": author})

    if not knot_maker_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(knot_maker_data)

    # Group by brand (knot maker) and calculate metrics
    grouped = df.groupby("brand").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["brand", "shaves", "unique_users"]

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
                "brand": row["brand"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
