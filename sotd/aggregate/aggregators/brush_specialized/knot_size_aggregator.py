from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class KnotSizeAggregator(BaseAggregator):
    """Aggregator for brush knot size data from enriched records."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract knot size data from records."""
        knot_size_data = []
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

            # Get knot size from knot section (all brushes have consistent handle/knot sections)
            knot_section = matched.get("knot", {})
            knot_size_mm = None

            if knot_section and isinstance(knot_section, dict):
                # Try knot.knot_size_mm first, then fallback to enriched.knot_size_mm
                knot_size_mm = knot_section.get("knot_size_mm") or enriched.get("knot_size_mm")

            # Skip if no knot size data
            if not knot_size_mm:
                continue

            author = record.get("author", "").strip()

            if knot_size_mm and author:
                knot_size_data.append({"knot_size_mm": knot_size_mm, "author": author})

        return knot_size_data

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite name from knot size data."""
        return df["knot_size_mm"].astype(str)

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns to use for grouping."""
        return ["knot_size_mm"]

    def _validate_and_filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and filter knot size data."""
        # Filter invalid sizes (15-50mm range)
        valid_mask = (df["knot_size_mm"] >= 15) & (df["knot_size_mm"] <= 50)
        return df[valid_mask]

    def aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate brush knot size data from enriched records.

        Returns a list of knot size aggregations sorted by shaves desc,
        unique_users desc. Each item includes position field for delta calculations.
        Uses brush.matched.knot.knot_size_mm with fallback to brush.enriched.knot_size_mm.

        Args:
            records: List of enriched comment records

        Returns:
            List of knot size aggregations with position, knot_size_mm, shaves,
            and unique_users fields
        """
        if not records:
            return []

        # Extract data from records
        extracted_data = self._extract_data(records)

        if not extracted_data:
            return []

        # Convert to DataFrame for efficient aggregation
        df = pd.DataFrame(extracted_data)

        # Validate and filter data
        df = self._validate_and_filter_data(df)

        if df.empty:
            return []

        # Create composite name
        df["name"] = self._create_composite_name(df)

        # Group and aggregate
        grouped = self._group_and_aggregate(df)

        # Sort and add position
        result = self._sort_and_rank(grouped)

        # Convert knot_size_mm back to float for output
        for item in result:
            item["knot_size_mm"] = float(item["name"])
            del item["name"]

        return result


# Legacy function interface for backward compatibility
def aggregate_knot_sizes(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function interface for backward compatibility."""
    aggregator = KnotSizeAggregator()
    return aggregator.aggregate(records)
