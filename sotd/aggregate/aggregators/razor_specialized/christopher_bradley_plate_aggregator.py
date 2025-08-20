from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class ChristopherBradleyPlateAggregator(BaseAggregator):
    """Aggregator for Christopher Bradley plate data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Christopher Bradley plate data from records."""
        plate_data = []
        for record in records:
            razor = record.get("razor", {})
            enriched = razor.get("enriched", {})

            # Skip if no enriched razor data or missing plate info
            if not enriched:
                continue

            plate_type = enriched.get("plate_type")
            plate_level = enriched.get("plate_level")

            # Skip if either plate_type or plate_level is missing
            if not plate_type or not plate_level:
                continue

            plate_type = plate_type.strip()
            plate_level = plate_level.strip()
            author = record.get("author", "").strip()

            if plate_type and plate_level and author:
                plate_data.append(
                    {"plate_type": plate_type, "plate_level": plate_level, "author": author}
                )

        return plate_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from plate_type and plate_level data."""
        return df["plate_type"] + " " + df["plate_level"]

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["plate_type", "plate_level"]


# Legacy function interface for backward compatibility
def aggregate_christopher_bradley_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = ChristopherBradleyPlateAggregator()
    return aggregator.aggregate(records)
