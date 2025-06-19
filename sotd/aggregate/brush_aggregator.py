#!/usr/bin/env python3
"""Brush-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class BrushAggregator(BaseAggregator):
    """Aggregator for brush usage statistics."""

    def get_operation_name(self) -> str:
        return "aggregate_brushes"

    def get_product_type(self) -> str:
        return "brush"

    def get_group_column(self) -> str:
        return "name"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        if "brush" not in record:
            return None
        brush_info = record["brush"]
        if not isinstance(brush_info, dict) or "matched" not in brush_info:
            return None
        matched = brush_info["matched"]
        if not isinstance(matched, dict) or not matched.get("brand"):
            return None
        if not self._validate_match_type(matched, record_index):
            return None
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        fiber = matched.get("fiber", "")
        # Create a descriptive brush name (brand + model + fiber)
        brush_name_parts = []
        if brand:
            brush_name_parts.append(brand)
        if model:
            brush_name_parts.append(model)
        if fiber:
            brush_name_parts.append(fiber)
        brush_name = " ".join(brush_name_parts) if brush_name_parts else "Unknown Brush"
        return {
            "name": brush_name,
            "brand": brand,
            "model": model,
            "fiber": fiber,
            "user": record.get("author", "Unknown"),
        }


def aggregate_brushes(records: list[dict[str, Any]], debug: bool = False) -> list[dict[str, Any]]:
    aggregator = BrushAggregator(debug)
    return aggregator.aggregate(records)
