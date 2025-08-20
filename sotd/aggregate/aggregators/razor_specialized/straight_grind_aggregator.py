from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class StraightGrindAggregator(BaseAggregator):
    """Aggregator for straight razor grind data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor grind data from records."""
        grind_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or no grind
            if not enriched or not enriched.get("grind"):
                continue

            grind = enriched.get("grind", "").strip()
            author = record.get("author", "").strip()

            if grind and author:
                grind_data.append({"grind": grind, "author": author})

        return grind_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from grind data."""
        return df["grind"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["grind"]


# Legacy function interface for backward compatibility
def aggregate_straight_grinds(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = StraightGrindAggregator()
    return aggregator.aggregate(records)
