from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class SuperSpeedTipAggregator(BaseAggregator):
    """Aggregator for Super Speed tip data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Super Speed tip data from records."""
        tip_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or no super_speed_tip
            if not enriched or not enriched.get("super_speed_tip"):
                continue

            super_speed_tip = enriched.get("super_speed_tip", "").strip()
            author = record.get("author", "").strip()

            if super_speed_tip and author:
                tip_data.append({"super_speed_tip": super_speed_tip, "author": author})

        return tip_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from super_speed_tip data."""
        return df["super_speed_tip"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["super_speed_tip"]


# Legacy function interface for backward compatibility
def aggregate_super_speed_tips(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = SuperSpeedTipAggregator()
    return aggregator.aggregate(records)
