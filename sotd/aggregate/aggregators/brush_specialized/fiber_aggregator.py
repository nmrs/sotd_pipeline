from typing import Any, Dict, List

import pandas as pd


def aggregate_fibers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush fiber data from enriched records.

    Returns a list of fiber aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Uses brush.matched.fiber with fallback to brush.enriched.fiber.

    Args:
        records: List of enriched comment records

    Returns:
        List of fiber aggregations with position, fiber, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract fiber data from records
    fiber_data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched")
        enriched = brush.get("enriched")

        # Ensure matched and enriched are dicts
        matched = matched if isinstance(matched, dict) else {}
        enriched = enriched if isinstance(enriched, dict) else {}

        # Try matched.fiber first, then fallback to enriched.fiber
        fiber = matched.get("fiber") or enriched.get("fiber")

        # Skip if no fiber data
        if not fiber:
            continue

        fiber = fiber.strip()
        author = record.get("author", "").strip()

        if fiber and author:
            fiber_data.append({"fiber": fiber, "author": author})

    if not fiber_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(fiber_data)

    # Group by fiber and calculate metrics
    grouped = df.groupby("fiber").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["fiber", "shaves", "unique_users"]

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
                "fiber": row["fiber"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
