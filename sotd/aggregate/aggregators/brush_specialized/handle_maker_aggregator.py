from typing import Any, Dict, List

import pandas as pd


def aggregate_handle_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush handle maker data from enriched records.

    Returns a list of handle maker aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of handle maker aggregations with position, handle_maker,
        shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract handle maker data from records
    handle_maker_data = []
    for record in records:
        brush = record.get("brush")

        # Skip if no brush data or brush is None
        if not brush:
            continue

        matched = brush.get("matched")

        # Skip if no matched brush data
        if not matched:
            continue

        # Get handle maker from handle section (all brushes have consistent handle/knot sections)
        handle_section = matched.get("handle", {})
        if not handle_section or not isinstance(handle_section, dict):
            continue

        handle_maker = handle_section.get("brand")
        if not handle_maker:
            continue

        handle_maker = handle_maker.strip()
        author = record.get("author", "").strip()

        if handle_maker and author:
            handle_maker_data.append({"handle_maker": handle_maker, "author": author})

    if not handle_maker_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(handle_maker_data)

    # Group by handle_maker and calculate metrics
    grouped = df.groupby("handle_maker").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["handle_maker", "shaves", "unique_users"]

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
                "handle_maker": row["handle_maker"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
