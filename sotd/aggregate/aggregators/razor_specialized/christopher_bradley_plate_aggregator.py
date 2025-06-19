from typing import Any, Dict, List

import pandas as pd


def aggregate_christopher_bradley_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate Christopher Bradley plate data from enriched records.

    Returns a list of Christopher Bradley plate aggregations sorted by shaves desc,
    unique_users desc. Each item includes position field for delta calculations.
    Combines plate_type and plate_level into composite key.

    Args:
        records: List of enriched comment records

    Returns:
        List of Christopher Bradley plate aggregations with position, plate_type,
        plate_level, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract Christopher Bradley plate data from records
    plate_data = []
    for record in records:
        razor = record.get("razor", {})
        enriched = razor.get("enriched", {})

        # Skip if no enriched razor data or missing plate info
        if not enriched:
            continue

        plate_type = enriched.get("plate_type")
        plate_level = enriched.get("plate_level")

        # Skip if either plate_type or plate_level is missing
        if not plate_type or not plate_level:
            continue

        plate_type = plate_type.strip()
        plate_level = plate_level.strip()
        author = record.get("author", "").strip()

        if plate_type and plate_level and author:
            plate_data.append(
                {"plate_type": plate_type, "plate_level": plate_level, "author": author}
            )

    if not plate_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(plate_data)

    # Group by plate_type and plate_level and calculate metrics
    grouped = (
        df.groupby(["plate_type", "plate_level"])
        .agg({"author": ["count", "nunique"]})
        .reset_index()
    )

    # Flatten column names
    grouped.columns = ["plate_type", "plate_level", "shaves", "unique_users"]

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
                "plate_type": row["plate_type"],
                "plate_level": row["plate_level"],
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
        )

    return result
