from typing import Any, Dict, List

import pandas as pd


def aggregate_blade_manufacturers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate blade manufacturer data from enriched records.

    Returns a list of blade manufacturer aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of blade manufacturer aggregations with position, name, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract blade manufacturer data from records
    manufacturer_data = []
    for record in records:
        blade = record.get("blade", {})
        matched = blade.get("matched", {})

        # Skip if no matched blade data or no brand
        if not matched or not matched.get("brand"):
            continue

        brand = matched.get("brand", "").strip()
        author = record.get("author", "").strip()

        if brand and author:
            manufacturer_data.append({"brand": brand, "author": author})

    if not manufacturer_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(manufacturer_data)

    # Group by brand and calculate metrics
    grouped = df.groupby("brand").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["name", "shaves", "unique_users"]

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
                "name": row["name"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
