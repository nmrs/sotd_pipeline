#!/usr/bin/env python3
"""Brush diversity aggregator for the SOTD pipeline."""

from typing import Any, Dict, List

import pandas as pd

from ..base_aggregator import BaseAggregator


class BrushDiversityAggregator(BaseAggregator):
    """Aggregator for tracking user brush diversity across multiple brush components."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract brush data from enriched records."""
        extracted = []

        for record in records:
            brush_data = record.get("brush")
            if brush_data is None or not isinstance(brush_data, dict):
                continue
            matched = brush_data.get("matched", {})

            # Skip records without matched brush data
            if not matched:
                continue

            # Extract all available brush fields
            brand = matched.get("brand")
            model = matched.get("model")
            knot_brand = matched.get("knot_brand")
            knot_model = matched.get("knot_model")
            handle_brand = matched.get("handle_brand")

            # Skip if no basic brand/model info
            if not brand or not model:
                continue

            extracted.append(
                {
                    "author": record["author"],
                    "brand": brand,
                    "model": model,
                    "knot_brand": knot_brand,
                    "knot_model": knot_model,
                    "handle_brand": handle_brand,
                }
            )

        return extracted

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite names combining all brush fields."""

        def create_brush_key(row):
            parts = []

            # Add top-level brand and model
            if pd.notna(row["brand"]) and row["brand"]:
                parts.append(str(row["brand"]))
            if pd.notna(row["model"]) and row["model"]:
                parts.append(str(row["model"]))

            # Add knot information if available
            if pd.notna(row["knot_brand"]) and row["knot_brand"]:
                parts.append(f"knot:{row['knot_brand']}")
            if pd.notna(row["knot_model"]) and row["knot_model"]:
                parts.append(f"knot:{row['knot_model']}")

            # Add handle information if available
            if pd.notna(row["handle_brand"]) and row["handle_brand"]:
                parts.append(f"handle:{row['handle_brand']}")

            return " ".join(parts) if parts else "unknown"

        result = df.apply(create_brush_key, axis=1)
        # Ensure we return a Series
        if isinstance(result, pd.Series):
            return result
        else:
            return pd.Series(result, index=df.index)

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data and calculate aggregation metrics."""
        # Create composite brush key for uniqueness counting
        df["brush_key"] = self._create_composite_name(df)

        # Group by author to count unique brushes
        grouped = (
            df.groupby("author")
            .agg(
                {
                    "brush_key": "nunique",
                }
            )
            .reset_index()
        )
        grouped.columns = ["author", "unique_brushes"]

        # Get total shaves per user
        shave_counts = df.groupby("author").size().reset_index(name="total_shaves")  # type: ignore
        grouped = grouped.merge(shave_counts, on="author")



        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data and add rank rankings."""
        grouped = grouped.sort_values(["unique_brushes", "total_shaves"], ascending=[False, False])
        grouped = grouped.reset_index(drop=True).assign(rank=lambda df: range(1, len(df) + 1))  # type: ignore

        result = []
        for _, row in grouped.iterrows():
            item = {
                "rank": int(row["rank"]),
                "user": str(row["author"]),
                "unique_brushes": int(row["unique_brushes"]),
                "total_shaves": int(row["total_shaves"]),

            }
            result.append(item)

        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns for grouping."""
        return ["author"]


def aggregate_brush_diversity(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush diversity by user from enriched records."""
    aggregator = BrushDiversityAggregator()
    return aggregator.aggregate(records)
