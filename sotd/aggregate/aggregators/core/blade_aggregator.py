from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_fields, get_field_value


class BladeAggregator(BaseAggregator):
    """Aggregator for blade data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract blade data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted blade data fields
        """
        blade_data = []
        for record in records:
            blade = record.get("blade") or {}
            matched = blade.get("matched", {})

            # Skip if no matched blade data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "model"):
                continue

            brand = get_field_value(matched, "brand")
            model = get_field_value(matched, "model")
            format_type = get_field_value(matched, "format")
            author = get_field_value(record, "author")

            if brand and author:  # model can be empty string, which is valid
                blade_data.append(
                    {"brand": brand, "model": model, "format": format_type, "author": author}
                )

        return blade_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted blade data

        Returns:
            Series with composite names in "Brand Model" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        # Use pandas string concatenation to avoid Series ambiguity
        return brand.astype(str) + " " + model.astype(str)


# Legacy function interface for backward compatibility
def aggregate_blades(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate blade data from enriched records.

    Returns a list of blade aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of blade aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = BladeAggregator()
    return aggregator.aggregate(records)
