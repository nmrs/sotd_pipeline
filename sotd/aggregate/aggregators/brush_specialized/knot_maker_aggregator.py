from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class KnotMakerAggregator(BaseAggregator):
    """Aggregator for brush knot maker data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract knot maker data from records."""
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

            # Get brand (knot maker) from matched or enriched data
            brand = matched.get("brand") or enriched.get("brand")

            # Skip if no brand data
            if not brand:
                continue

            author = record.get("author", "").strip()

            if brand and author:
                maker_data.append({"brand": brand, "author": author})

        return maker_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand data."""
        return df["brand"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_knot_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = KnotMakerAggregator()
    return aggregator.aggregate(records)
