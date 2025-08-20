from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class StraightWidthAggregator(BaseAggregator):
    """Aggregator for straight razor width data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract straight razor width data from records."""
        width_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or no width
            if not enriched or not enriched.get("width"):
                continue

            width = enriched.get("width", "").strip()
            author = record.get("author", "").strip()

            if width and author:
                width_data.append({"width": width, "author": author})

        return width_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from width data."""
        return df["width"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["width"]


# Legacy function interface for backward compatibility
def aggregate_straight_widths(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = StraightWidthAggregator()
    return aggregator.aggregate(records)
