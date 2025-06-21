from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


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
            razor = record.get("razor", {})
            matched = razor.get("matched", {})

            # Skip if no matched razor data
            if not matched or not matched.get("brand") or not matched.get("model"):
                continue

            brand = matched.get("brand", "").strip()
            model = matched.get("model", "").strip()
            format_type = matched.get("format", "").strip()
            author = record.get("author", "").strip()

            if brand and model and author:
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
        return df["brand"] + " " + df["model"]


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
