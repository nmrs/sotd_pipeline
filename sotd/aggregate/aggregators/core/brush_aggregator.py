from typing import Any, Dict, List

import pandas as pd


def aggregate_brushes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush data from enriched records.

    Returns a list of brush aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of brush aggregations with position, name, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract brush data from records
    brush_data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {})

        # Skip if no matched brush data
        if not matched or not matched.get("brand") or not matched.get("model"):
            continue

        brand = matched.get("brand", "")
        model = matched.get("model", "")
        fiber = matched.get("fiber", "")
        author = record.get("author", "")

        # Handle None values and strip strings
        brand = brand.strip() if brand else ""
        model = model.strip() if model else ""
        fiber = fiber.strip() if fiber else ""
        author = author.strip() if author else ""

        if brand and model and fiber and author:
            brush_data.append({"brand": brand, "model": model, "fiber": fiber, "author": author})

    if not brush_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(brush_data)

    # Create composite name: "Brand Model"
    df["name"] = df["brand"] + " " + df["model"]

    # Group by name and fiber, calculate metrics
    grouped = df.groupby(["name", "fiber"]).agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["name", "fiber", "shaves", "unique_users"]

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
                "fiber": row["fiber"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
