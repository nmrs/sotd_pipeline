from typing import Any, Dict, List

import pandas as pd


def aggregate_razor_blade_combos(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor blade combination data from enriched records.

    Returns a list of razor blade combination aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Combines razor and blade data to create composite keys.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor blade combination aggregations with position, razor_name,
        blade_name, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract razor blade combination data from records
    combo_data = []
    for record in records:
        razor = record.get("razor", {})
        blade = record.get("blade", {})

        razor_matched = razor.get("matched", {})
        blade_matched = blade.get("matched", {})

        # Skip if no matched razor or blade data
        if not razor_matched or not blade_matched:
            continue

        razor_brand = razor_matched.get("brand", "").strip()
        razor_model = razor_matched.get("model", "").strip()
        blade_brand = blade_matched.get("brand", "").strip()
        blade_model = blade_matched.get("model", "").strip()
        author = record.get("author", "").strip()

        # Skip if missing essential data
        if not (razor_brand and razor_model and blade_brand and blade_model and author):
            continue

        razor_name = f"{razor_brand} {razor_model}"
        blade_name = f"{blade_brand} {blade_model}"

        combo_data.append({"razor_name": razor_name, "blade_name": blade_name, "author": author})

    if not combo_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(combo_data)

    # Group by razor_name and blade_name and calculate metrics
    grouped = (
        df.groupby(["razor_name", "blade_name"]).agg({"author": ["count", "nunique"]}).reset_index()
    )

    # Flatten column names
    grouped.columns = ["razor_name", "blade_name", "shaves", "unique_users"]

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
                "razor_name": row["razor_name"],
                "blade_name": row["blade_name"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
