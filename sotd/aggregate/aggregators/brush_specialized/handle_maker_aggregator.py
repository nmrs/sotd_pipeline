from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class HandleMakerAggregator(BaseAggregator):
    """Aggregator for brush handle maker data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract handle maker data from records."""
        maker_data = []
        for record in records:
            brush = record.get("brush")

            # Skip if no brush data or brush is None
            if not brush:
                continue

            matched = brush.get("matched")
            enriched = brush.get("enriched")

            # Ensure matched and enriched are dicts
            matched = matched if isinstance(matched, dict) else {}
            enriched = enriched if isinstance(enriched, dict) else {}

            # Get handle maker from matched.handle.brand (handle_maker field is deprecated)
            handle = matched.get("handle", {})
            if isinstance(handle, dict):
                handle_maker = handle.get("brand")
            else:
                handle_maker = None

            # Fallback to enriched data if available
            if not handle_maker and enriched:
                handle_maker = enriched.get("handle_maker")

            # Skip if no handle maker data
            if not handle_maker:
                continue

            author = record.get("author", "").strip()

            if handle_maker and author:
                maker_data.append({"handle_maker": handle_maker, "author": author})

        return maker_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from handle maker data."""
        return df["handle_maker"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["handle_maker"]


# Legacy function interface for backward compatibility
def aggregate_handle_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = HandleMakerAggregator()
    return aggregator.aggregate(records)
