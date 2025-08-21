from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class SoapMakerAggregator(BaseAggregator):
    """Aggregator for soap maker data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract soap maker data from records."""
        maker_data = []
        for record in records:
            soap = record.get("soap", {})
            matched = soap.get("matched", {})

            # Skip if no matched soap data or no brand
            if not matched or not matched.get("brand"):
                continue

            maker = matched.get("brand", "").strip()
            author = record.get("author", "").strip()

            if maker and author:
                maker_data.append({"maker": maker, "author": author})

        return maker_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from maker data."""
        return df["maker"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["maker"]


# Legacy function interface for backward compatibility
def aggregate_soap_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = SoapMakerAggregator()
    return aggregator.aggregate(records)
