from typing import Any, Dict, List

import pandas as pd


def aggregate_straight_points(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor point data from enriched records.

    Returns a list of straight razor point aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts point from razor.enriched.point.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor point aggregations with position, point, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract straight razor point data from records
    point_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no point
        if not enriched or not enriched.get("point"):
            continue

        point = enriched.get("point", "").strip()
        author = record.get("author", "").strip()

        if point and author:
            point_data.append({"point": point, "author": author})

    if not point_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(point_data)

    # Group by point and calculate metrics
    grouped = df.groupby("point").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["point", "shaves", "unique_users"]

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
                "point": row["point"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
