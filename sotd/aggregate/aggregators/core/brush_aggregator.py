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
            brush = record.get("brush")

            # Skip if no brush data or brush is None
            if not brush:
                continue

            matched = brush.get("matched", {})

            # Skip if no matched brush data
            if not matched:
                continue

            # Get brush info from new format
            brand = matched.get("brand")  # Top-level brand (null for composite brushes)
            model = matched.get("model")  # Top-level model (null for composite brushes)

            # For composite brushes, try to get info from handle/knot sections
            if not brand or not model:
                handle_section = matched.get("handle", {})
                knot_section = matched.get("knot", {})

                if handle_section and isinstance(handle_section, dict):
                    handle_brand = handle_section.get("brand")
                    handle_model = handle_section.get("model")

                    if knot_section and isinstance(knot_section, dict):
                        knot_brand = knot_section.get("brand")
                        knot_model = knot_section.get("model")

                        # For composite brushes, use handle brand + knot model or vice versa
                        if handle_brand and knot_model:
                            brand = handle_brand
                            model = knot_model
                        elif knot_brand and handle_model:
                            brand = knot_brand
                            model = handle_model
                        elif handle_brand and handle_model:
                            brand = handle_brand
                            model = handle_model
                        elif knot_brand and knot_model:
                            brand = knot_brand
                            model = knot_model

            # Get fiber from knot section (all brushes have consistent handle/knot sections)
            fiber = ""
            knot_section = matched.get("knot", {})
            if knot_section and isinstance(knot_section, dict):
                fiber = knot_section.get("fiber", "")

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
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        return brand + " " + model

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
