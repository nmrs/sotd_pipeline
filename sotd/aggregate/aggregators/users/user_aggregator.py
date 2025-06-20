from typing import Any, Dict, List

import pandas as pd


def aggregate_users(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate user data from enriched records.

    Returns a list of user aggregations sorted by shaves desc, missed_days desc.
    Each item includes position field for delta calculations.
    Extracts author from comment data and calculates shaves and missed_days.

    Args:
        records: List of enriched comment records

    Returns:
        List of user aggregations with position, user, shaves,
        and missed_days fields
    """
    if not records:
        return []

    # Extract user data from records
    user_data = []
    for record in records:
        author = record.get("author", "").strip()

        # Skip if no author
        if not author:
            continue

        # For now, we'll count each record as one shave
        # In the future, we might want to calculate missed_days from date data
        user_data.append({"author": author})

    if not user_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(user_data)

    # Group by author and calculate metrics
    grouped = df.groupby("author").size().reset_index()
    grouped.columns = ["author", "shaves"]

    # For now, set missed_days to 0 (placeholder for future enhancement)
    grouped["missed_days"] = 0

    # Sort by shaves desc, missed_days desc
    grouped = grouped.sort_values(["shaves", "missed_days"], ascending=[False, False])

    # Add position field (1-based rank)
    grouped["position"] = range(1, len(grouped) + 1)

    # Convert to list of dictionaries
    result = []
    for _, row in grouped.iterrows():
        result.append(
            {
                "position": int(row["position"]),
                "user": row["author"],
                "shaves": int(row["shaves"]),
                "missed_days": int(row["missed_days"]),
            }
        )

    return result
