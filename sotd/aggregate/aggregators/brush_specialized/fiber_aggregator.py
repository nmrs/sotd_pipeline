from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class FiberAggregator(BaseAggregator):
    """Aggregator for brush fiber data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract fiber data from records."""
        fiber_data = []
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

            # Get fiber from matched.knot.fiber
            knot = matched.get("knot", {})
            if isinstance(knot, dict):
                fiber = knot.get("fiber")
            else:
                fiber = None

            # Fallback to enriched data if available
            if not fiber and enriched:
                fiber = enriched.get("fiber")

            # Skip if no fiber data
            if not fiber:
                continue

            author = record.get("author", "").strip()

            if fiber and author:
                fiber_data.append({"fiber": fiber, "author": author})

        return fiber_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from fiber data."""
        return df["fiber"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["fiber"]


# Legacy function interface for backward compatibility
def aggregate_fibers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = FiberAggregator()
    return aggregator.aggregate(records)
