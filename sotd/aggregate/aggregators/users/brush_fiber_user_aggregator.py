#!/usr/bin/env python3
"""Brush fiber user aggregator for the SOTD pipeline."""

from typing import Any, Dict, List
import pandas as pd

from ..base_aggregator import BaseAggregator


class BrushFiberUserAggregator(BaseAggregator):
    """Aggregator for tracking top users within each brush fiber type category."""

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract brush fiber data from enriched records."""
        extracted = []
        
        for record in records:
            brush_data = record.get("brush", {})
            matched = brush_data.get("matched", {})
            
            # Skip records without matched brush data
            if not matched:
                continue
                
            # Extract fiber and author
            fiber = matched.get("fiber")
            author = record.get("author")
            
            # Skip if no fiber or author
            if not fiber or not author:
                continue
                
            extracted.append({
                "author": author,
                "fiber": fiber,
            })
            
        return extracted

    def _create_composite_name(self, df: pd.DataFrame) -> pd.Series:
        """Create composite names for grouping (not used in this aggregator)."""
        # This aggregator doesn't use composite names in the traditional sense
        # We group by fiber first, then by user
        return df["fiber"]

    def _group_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group data by fiber first, then by user within each fiber."""
        # Group by fiber and author to count shaves per user per fiber
        grouped = df.groupby(["fiber", "author"]).size().reset_index(name="shaves")  # type: ignore
        
        # Add unique_users field (always 1 for user aggregators)
        grouped["unique_users"] = 1
        
        return grouped

    def _sort_and_rank(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sort grouped data by fiber, then by shaves, and add position rankings."""
        # Sort by fiber asc, then shaves desc, then unique_users desc
        grouped = grouped.sort_values(
            ["fiber", "shaves", "unique_users"], 
            ascending=[True, False, False]
        )
        
        # Add position field within each fiber group
        result = []
        current_fiber = None
        current_position = 1
        
        for _, row in grouped.iterrows():
            fiber_type = str(row["fiber"])
            
            # Reset position counter for new fiber
            if fiber_type != current_fiber:
                current_fiber = fiber_type
                current_position = 1
            
            item = {
                "position": current_position,
                "fiber": fiber_type,
                "user": str(row["author"]),
                "shaves": int(row["shaves"]),
                "unique_users": int(row["unique_users"]),
            }
            result.append(item)
            
            current_position += 1
            
        return result

    def _get_group_columns(self, df: pd.DataFrame) -> List[str]:
        """Get columns for grouping."""
        return ["fiber", "author"]


def aggregate_brush_fiber_users(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate brush fiber usage by user from enriched records."""
    aggregator = BrushFiberUserAggregator()
    return aggregator.aggregate(records)
