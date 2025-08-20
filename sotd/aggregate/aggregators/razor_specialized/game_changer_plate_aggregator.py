from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class GameChangerPlateAggregator(BaseAggregator):
    """Aggregator for Game Changer plate data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Game Changer plate data from records."""
        gap_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or no gap
            if not enriched or not enriched.get("gap"):
                continue

            gap = enriched.get("gap", "").strip()
            author = record.get("author", "").strip()

            if gap and author:
                gap_data.append({"gap": gap, "author": author})

        return gap_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from gap data."""
        return df["gap"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["gap"]


# Legacy function interface for backward compatibility
def aggregate_game_changer_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = GameChangerPlateAggregator()
    return aggregator.aggregate(records)
