from typing import Any, Dict, List

import pandas as pd


def aggregate_razors(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor data from enriched records.

    Returns a list of razor aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor aggregations with position, name, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract razor data from records
    razor_data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {})

        # Skip if no matched razor data
        if not matched or not matched.get("brand") or not matched.get("model"):
            continue

        brand = matched.get("brand", "").strip()
        model = matched.get("model", "").strip()
        format_type = matched.get("format", "").strip()
        author = record.get("author", "").strip()

        if brand and model and author:
            razor_data.append(
                {"brand": brand, "model": model, "format": format_type, "author": author}
            )

    if not razor_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(razor_data)

    # Create composite name: "Brand Model"
    df["name"] = df["brand"] + " " + df["model"]

    # Group by name and calculate metrics
    grouped = df.groupby("name").agg({"author": ["count", "nunique"]}).reset_index()

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
