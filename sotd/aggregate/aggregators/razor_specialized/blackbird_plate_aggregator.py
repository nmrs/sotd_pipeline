from typing import Any, Dict, List

import pandas as pd


def aggregate_blackbird_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Blackbird plate data from enriched records.

    Returns a list of Blackbird plate aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Extracts plate from razor.enriched.plate.

    Args:
        records: List of enriched comment records

    Returns:
        List of Blackbird plate aggregations with position, plate, shaves,
        and unique_users fields
    """
    if not records:
        return []

    # Extract Blackbird plate data from records
    plate_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or no plate
        if not enriched or not enriched.get("plate"):
            continue

        plate = enriched.get("plate", "").strip()
        author = record.get("author", "").strip()

        if plate and author:
            plate_data.append({"plate": plate, "author": author})

    if not plate_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(plate_data)

    # Group by plate and calculate metrics
    grouped = df.groupby("plate").agg({"author": ["count", "nunique"]}).reset_index()

    # Flatten column names
    grouped.columns = ["plate", "shaves", "unique_users"]

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
                "plate": row["plate"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
