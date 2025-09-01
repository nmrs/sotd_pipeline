from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class ChristopherBradleyPlateAggregator(BaseAggregator):
    """Aggregator for Christopher Bradley plate data from enriched records."""

    @property
    def IDENTIFIER_FIELDS(self) -> List[str]:
        """Fields used for matching/grouping."""
        return ["plate"]

    @property
    def METRIC_FIELDS(self) -> List[str]:
        """Calculated/metric fields."""
        return ["shaves", "unique_users"]

    @property
    def RANKING_FIELDS(self) -> List[str]:
        """Fields used for sorting/ranking."""
        return ["shaves", "unique_users"]

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
                # Combine plate_type and plate_level into single plate field
                plate = f"{plate_type}-{plate_level}"
                plate_data.append({"plate": plate, "author": author})

        return plate_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from plate data."""
        # The plate field is already combined, so just return it
        return df["plate"].fillna("").astype(str)  # type: ignore

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["plate"]


# Legacy function interface for backward compatibility
def aggregate_christopher_bradley_plates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = ChristopherBradleyPlateAggregator()
    return aggregator.aggregate(records)
