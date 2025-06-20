from typing import Any, Dict, List

import pandas as pd


def aggregate_highest_use_count_per_blade(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate highest use count per blade data from enriched records.

    Returns a list of highest use count per blade aggregations sorted by uses desc.
    Each item includes position field for delta calculations.
    Tracks per-user blade usage and extracts use_count from blade.enriched.use_count.

    Args:
        records: List of enriched comment records

    Returns:
        List of highest use count per blade aggregations with position, blade_name,
        author, and uses fields
    """
    if not records:
        return []

    # Extract highest use count per blade data from records
    use_count_data = []
    for record in records:
        blade = record.get("blade", {})
        blade_matched = blade.get("matched", {})
        blade_enriched = blade.get("enriched", {})
        author = record.get("author", "").strip()

        # Skip if no matched blade data or no author
        if not blade_matched or not author:
            continue

        blade_brand = blade_matched.get("brand", "").strip()
        blade_model = blade_matched.get("model", "").strip()

        # Skip if missing essential blade data
        if not (blade_brand and blade_model):
            continue

        blade_name = f"{blade_brand} {blade_model}"

        # Get use_count from enriched data, default to 1 if not available
        use_count = blade_enriched.get("use_count", 1)

        use_count_data.append({"blade_name": blade_name, "author": author, "uses": use_count})

    if not use_count_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(use_count_data)

    # Group by blade_name and author to get per-user usage
    # Then find the maximum use count per blade across all users
    user_max_usage = df.groupby(["blade_name", "author"])["uses"].max().reset_index()

    # Find the highest use count per blade
    blade_max_usage = (
        user_max_usage.groupby("blade_name")
        .agg({"uses": "max", "author": "first"})  # Get the first author who achieved this max
        .reset_index()
    )

    # Sort by uses desc
    blade_max_usage = blade_max_usage.sort_values("uses", ascending=False)

    # Add position field (1-based rank)
    blade_max_usage["position"] = range(1, len(blade_max_usage) + 1)

    # Convert to list of dictionaries
    result = []
    for _, row in blade_max_usage.iterrows():
        result.append(
            {
                "position": int(row["position"]),
                "blade_name": row["blade_name"],
                "author": row["author"],
                "uses": int(row["uses"]),
            }
        )

    return result
