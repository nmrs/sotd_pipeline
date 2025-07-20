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
        List of highest use count per blade aggregations with position, user,
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
    blade_max_usage = (
        user_max_usage.groupby(["blade_name", "blade_format"])
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
                "user": row["author"],
                "blade": row["blade_name"],
                "format": row["blade_format"],
                "uses": int(row["uses"]),
            }
        )

    return result
