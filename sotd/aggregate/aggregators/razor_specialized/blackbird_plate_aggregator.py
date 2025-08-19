from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class BlackbirdPlateAggregator(BaseAggregator):
    """Aggregator for Blackland Blackbird plate data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Blackbird plate data from records."""
        plate_data = []
        for record in records:
            razor = record.get("razor", {})
            matched = razor.get("matched", {})

            # Skip if no matched razor data
            if not matched:
                continue

            # Check if this is a Blackland Blackbird razor
            brand = matched.get("brand", "").strip()
            if brand.lower() != "blackland":
                continue

            model = matched.get("model", "").strip()
            if "blackbird" not in model.lower():
                continue

            # Get plate information from enriched data
            enriched = razor.get("enriched", {})
            plate = enriched.get("plate", "").strip()
            if not plate:
                continue

            author = record.get("author", "").strip()

            if plate and author:
                plate_data.append({"plate": plate, "author": author})

        return plate_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from plate data."""
        return df["plate"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["plate"]


# Legacy function interface for backward compatibility
def aggregate_blackbird_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = BlackbirdPlateAggregator()
    return aggregator.aggregate(records)
