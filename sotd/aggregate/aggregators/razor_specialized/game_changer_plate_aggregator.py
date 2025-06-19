from typing import Any, Dict, List

import pandas as pd


def aggregate_game_changer_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Game Changer plate data from enriched records.

    Returns a list of Game Changer plate aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts gap from razor.enriched.gap.

    Args:
        records: List of enriched comment records

    Returns:
        List of Game Changer plate aggregations with position, gap, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract Game Changer plate data from records
    gap_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no gap
        if not enriched or not enriched.get("gap"):
            continue

        gap = enriched.get("gap", "").strip()
        author = record.get("author", "").strip()

        if gap and author:
            gap_data.append({"gap": gap, "author": author})

    if not gap_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(gap_data)

    # Group by gap and calculate metrics
    grouped = df.groupby("gap").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["gap", "shaves", "unique_users"]

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
                "gap": row["gap"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
