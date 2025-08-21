from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator
from ...utils.field_validation import has_required_fields, get_field_value


class SoapAggregator(BaseAggregator):
    """Aggregator for soap data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap data from records for aggregation.

        Args:
            records: List of enriched comment records

        Returns:
            List of dictionaries with extracted soap data fields
        """
        soap_data = []
        for record in records:
            soap = record.get("soap") or {}
            matched = soap.get("matched", {})

            # Skip if no matched soap data or missing required fields
            # Note: Empty strings are valid values, only None is invalid
            if not matched or not has_required_fields(matched, "brand", "scent"):
                continue

            brand = get_field_value(matched, "brand")
            scent = get_field_value(matched, "scent")
            author = get_field_value(record, "author")

            if brand and author:  # scent can be empty string, which is valid
                soap_data.append({"brand": brand, "scent": scent, "author": author})

        return soap_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and scent.

        Args:
            df: DataFrame with extracted soap data

        Returns:
            Series with composite names in "Brand - Scent" format
        """
        # Handle None values by converting to empty strings and concatenate properly
        brand = df["brand"].fillna("")
        scent = df["scent"].fillna("")
        
        # Use pandas string concatenation to avoid Series ambiguity
        # Always concatenate with dash - empty scents will just show as "Brand - "
        return brand.astype(str) + " - " + scent.astype(str)


# Legacy function interface for backward compatibility
def aggregate_soaps(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate soap data from enriched records.

    Returns a list of soap aggregations sorted by shaves desc, unique_users desc.
    Each item includes position field for delta calculations.

    Args:
        records: List of enriched comment records

    Returns:
        List of soap aggregations with position, name, shaves, and unique_users fields
    """
    aggregator = SoapAggregator()
    return aggregator.aggregate(records)
