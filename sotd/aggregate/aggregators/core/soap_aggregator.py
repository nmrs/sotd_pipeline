from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


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

            # Skip if no matched soap data
            if not matched or not matched.get("brand") or not matched.get("scent"):
                continue

            brand = matched.get("brand", "").strip()
            scent = matched.get("scent", "").strip()
            author = record.get("author", "").strip()

            if brand and scent and author:
                soap_data.append({"brand": brand, "scent": scent, "author": author})

        return soap_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand and scent.

        Args:
            df: DataFrame with extracted soap data

        Returns:
            Series with composite names in "Brand - Scent" format
        """
        # Handle None values by converting to empty strings
        brand = df["brand"].fillna("")
        scent = df["scent"].fillna("")
        return brand + " - " + scent


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
