from typing import Any, Dict, List

import pandas as pd


def aggregate_soap_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap maker data from enriched records.

    Returns a list of soap maker aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap maker aggregations with position, name, shaves, and unique_users fields
    """
    if not records:
        return []

    # Extract soap maker data from records
    maker_data = []
    for record in records:
        soap = record.get("soap", {})
        matched = soap.get("matched", {})

        # Skip if no matched soap data or no maker
        if not matched or not matched.get("maker"):
            continue

        maker = matched.get("maker", "").strip()
        author = record.get("author", "").strip()

        if maker and author:
            maker_data.append({"maker": maker, "author": author})

    if not maker_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(maker_data)

    # Group by maker and calculate metrics
    grouped = df.groupby("maker").agg({"author": ["count", "nunique"]}).reset_index()

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
