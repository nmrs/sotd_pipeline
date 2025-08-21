from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_fields, get_field_value


class RazorAggregator(BaseAggregator):
    """Aggregator for razor data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract razor data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted razor data fields
        """
        razor_data = []
        for record in records:
            razor = record.get("razor") or {}
            matched = razor.get("matched", {})

            # Skip if no matched razor data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "model"):
                continue

            brand = get_field_value(matched, "brand")
            model = get_field_value(matched, "model")
            format_type = get_field_value(matched, "format")
            author = get_field_value(record, "author")

            if brand and author:  # model can be empty string, which is valid
                razor_data.append(
                    {"brand": brand, "model": model, "format": format_type, "author": author}
                )

        return razor_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and model.

        Args:
            df: DataFrame with extracted razor data

        Returns:
            Series with composite names in "Brand Model" format
        """
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        model = df["model"].fillna("")
        return brand + " " + model


# Legacy function interface for backward compatibility
def aggregate_razors(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate razor data from enriched records.

    Returns a list of razor aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of razor aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = RazorAggregator()
    return aggregator.aggregate(records)
