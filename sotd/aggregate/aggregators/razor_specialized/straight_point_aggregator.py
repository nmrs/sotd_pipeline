from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class StraightPointAggregator(BaseAggregator):
    """Aggregator for straight razor point data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor point data from records."""
        point_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or no point
            if not enriched or not enriched.get("point"):
                continue

            point = enriched.get("point", "").strip()
            author = record.get("author", "").strip()

            if point and author:
                point_data.append({"point": point, "author": author})

        return point_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from point data."""
        return df["point"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["point"]


# Legacy function interface for backward compatibility
def aggregate_straight_points(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = StraightPointAggregator()
    return aggregator.aggregate(records)
