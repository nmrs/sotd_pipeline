from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class KnotMakerAggregator(BaseAggregator):
    """Aggregator for brush knot maker data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["brand"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

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

            # Priority 1: Use matched.knot.brand for split brushes
            knot = matched.get("knot", {})
            if isinstance(knot, dict):
                brand = knot.get("brand")
            else:
                brand = None

            # Priority 2: Fallback to matched.brand for complete brushes
            if not brand:
                brand = matched.get("brand")

            # Priority 3: Fallback to enriched data if available (legacy support)
            if not brand and enriched:
                brand = enriched.get("brand")

            # Skip if no brand data
            if not brand:
                continue

            # Note: _user_override field is for debugging/data quality, not filtering
            # We count all knots regardless of user override status

            author = record.get("author", "").strip()

            if brand and author:
                maker_data.append({"brand": brand, "author": author})

        return maker_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from brand data."""
        # Ensure we get a Series, not DataFrame
        brand_series: pd.Series = df["brand"]  # type: ignore
        return brand_series

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["brand"]


# Legacy function interface for backward compatibility
def aggregate_knot_makers(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = KnotMakerAggregator()
    return aggregator.aggregate(records)
