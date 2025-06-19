from typing import Any, Dict, List

import pandas as pd


def aggregate_super_speed_tips(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Super Speed tip data from enriched records.

    Returns a list of Super Speed tip aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts super_speed_tip from razor.enriched.super_speed_tip.

    Args:
        records: List of enriched comment records

    Returns:
        List of Super Speed tip aggregations with position, super_speed_tip,
        shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract Super Speed tip data from records
    tip_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no super_speed_tip
        if not enriched or not enriched.get("super_speed_tip"):
            continue

        super_speed_tip = enriched.get("super_speed_tip", "").strip()
        author = record.get("author", "").strip()

        if super_speed_tip and author:
            tip_data.append({"super_speed_tip": super_speed_tip, "author": author})

    if not tip_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(tip_data)

    # Group by super_speed_tip and calculate metrics
    grouped = df.groupby("super_speed_tip").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["super_speed_tip", "shaves", "unique_users"]

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
                "super_speed_tip": row["super_speed_tip"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
