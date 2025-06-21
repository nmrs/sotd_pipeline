from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class BrushAggregator(BaseAggregator):
    """Aggregator for brush data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract brush data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted brush data fields
        """
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
                brush_data.append(
                    {"brand": brand, "model": model, "fiber": fiber, "author": author}
                )

        return brush_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted brush data

        Returns:
            Series with composite names in "Brand Model" format
        """
        return df["brand"] + " " + df["model"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping.

        Args:
            df: DataFrame with extracted brush data

        Returns:
            List of column names for grouping (name and fiber)
        """
        return ["name", "fiber"]


# Legacy function interface for backward compatibility
def aggregate_brushes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush data from enriched records.

    Returns a list of brush aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of brush aggregations with position, name, fiber, shaves, and unique_users fields
    """
    aggregator = BrushAggregator()
    return aggregator.aggregate(records)
