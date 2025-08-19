from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class RazorManufacturerAggregator(BaseAggregator):
    """Aggregator for razor manufacturer data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract razor manufacturer data from records."""
        manufacturer_data = []
        for record in records:
            razor = record.get("razor", {})
            matched = razor.get("matched", {})

            # Skip if no matched razor data or no brand
            if not matched or not matched.get("brand"):
                continue

            brand = matched.get("brand", "").strip()
            author = record.get("author", "").strip()

            if brand and author:
                manufacturer_data.append({"brand": brand, "author": author})

        return manufacturer_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand data."""
        return df["brand"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_razor_manufacturers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = RazorManufacturerAggregator()
    return aggregator.aggregate(records)
