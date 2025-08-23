from typing import Any, Dict, List

import pandas as pd


def aggregate_highest_use_count_per_blade(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate highest use count per blade data from enriched records.

    Returns a list of highest use count per blade aggregations sorted by uses desc.
    Each item includes rank field for delta calculations.
    Tracks per-user blade usage and extracts use_count from blade.enriched.use_count.

    Args:
        records: List of enriched comment records

    Returns:
        List of highest use count per blade aggregations with rank, user,
        blade, format, and uses fields
    """
    if not records:
        return []

    # Extract highest use count per blade data from records
    use_count_data = []
    for record in records:
        blade = record.get("blade", {})
        blade_matched = blade.get("matched", {})
        blade_enriched = blade.get("enriched", {})
        # Also check for blade_enriched at top level (for test compatibility)
        if not blade_enriched:
            blade_enriched = record.get("blade_enriched", {})
        author = record.get("author", "").strip()

        # Skip if no matched blade data or no author
        if not blade_matched or not author:
            continue

        blade_brand = blade_matched.get("brand", "")
        blade_model = blade_matched.get("model", "")
        blade_format = blade_matched.get("format", "")

        # Handle None values and strip strings
        blade_brand = blade_brand.strip() if blade_brand else ""
        blade_model = blade_model.strip() if blade_model else ""
        blade_format = blade_format.strip() if blade_format else ""

        # Skip if missing essential blade data
        if not (blade_brand and blade_model):
            continue

        blade_name = f"{blade_brand} {blade_model}"

        # Get use_count from enriched data, default to 1 if not available
        use_count = blade_enriched.get("use_count", 1)

        # Ensure use_count is an integer
        try:
            use_count = int(use_count) if use_count is not None else 1
        except (ValueError, TypeError):
            use_count = 1

        use_count_data.append(
            {
                "blade_name": blade_name,
                "blade_format": blade_format,
                "author": author,
                "uses": use_count,
            }
        )

    if not use_count_data:
        return []

    # Convert to DataFrame for efficient aggregation
    df = pd.DataFrame(use_count_data)

    # Group by blade_name and author to get per-user usage
    # Then find the maximum use count per blade across all users
    user_max_usage = (
        df.groupby(["blade_name", "blade_format", "author"])["uses"].max().reset_index()
    )

    # Find the highest use count per blade
    # We need to get the author associated with the maximum use count, not just the first author
    blade_max_usage = []
    for (blade_name, blade_format), group in user_max_usage.groupby(["blade_name", "blade_format"]):
        # Find the row with the maximum uses for this blade
        max_uses_row = group.loc[group["uses"].idxmax()]
        blade_max_usage.append(
            {
                "blade_name": blade_name,
                "blade_format": blade_format,
                "uses": max_uses_row["uses"],
                "author": max_uses_row["author"],
            }
        )

    # Convert back to DataFrame and sort
    blade_max_usage = pd.DataFrame(blade_max_usage)

    # Sort by uses desc
    blade_max_usage = blade_max_usage.sort_values("uses", ascending=False)

    # Add competition ranking based on uses
    # Items with same uses get tied ranks
    blade_max_usage = blade_max_usage.reset_index(drop=True)

    # Create a composite key for ranking that preserves the order
    # Use sequential ranks, then group by uses to get same rank for ties
    blade_max_usage["temp_rank"] = range(1, len(blade_max_usage) + 1)
    blade_max_usage["rank"] = blade_max_usage.groupby("uses", sort=False)["temp_rank"].transform(
        "min"
    )
    blade_max_usage = blade_max_usage.drop("temp_rank", axis=1)

    # Sort by ranking first, then by blade_name for consistent ordering of tied entries
    blade_max_usage = blade_max_usage.sort_values(["rank", "blade_name"], ascending=[True, True])
    blade_max_usage = blade_max_usage.reset_index(drop=True)

    # Convert to list of dictionaries
    result = []
    for _, row in blade_max_usage.iterrows():
        result.append(
            {
                "rank": int(row["rank"]),
                "user": row["author"],  # Keep clean, add "u/" in report
                "blade": row["blade_name"],
                "format": row["blade_format"],
                "uses": int(row["uses"]),
            }
        )

    return result
