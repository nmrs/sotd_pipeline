from typing import Any, Dict, List

import pandas as pd


def aggregate_straight_grinds(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate straight razor grind data from enriched records.

    Returns a list of straight razor grind aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts grind from razor.enriched.grind.

    Args:
        records: List of enriched comment records

    Returns:
        List of straight razor grind aggregations with position, grind, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract straight razor grind data from records
    grind_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no grind
        if not enriched or not enriched.get("grind"):
            continue

        grind = enriched.get("grind", "").strip()
        author = record.get("author", "").strip()

        if grind and author:
            grind_data.append({"grind": grind, "author": author})

    if not grind_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(grind_data)

    # Group by grind and calculate metrics
    grouped = df.groupby("grind").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["grind", "shaves", "unique_users"]

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
                "grind": row["grind"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
