#!/usr/bin/env python3
"""Blade-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class BladeAggregator(BaseAggregator):
    """Aggregator for blade usage statistics."""

    def get_operation_name(self) -> str:
        return "aggregate_blades"

    def get_product_type(self) -> str:
        return "blade"

    def get_group_column(self) -> str:
        return "name"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        if "blade" not in record:
            return None
        blade_info = record["blade"]
        if not isinstance(blade_info, dict) or "matched" not in blade_info:
            return None
        matched = blade_info["matched"]
        if not isinstance(matched, dict) or not matched.get("brand"):
            return None
        if not self._validate_match_type(matched, record_index):
            return None
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        blade_name_parts = []
        if brand:
            blade_name_parts.append(brand)
        if model:
            blade_name_parts.append(model)
        blade_name = " ".join(blade_name_parts) if blade_name_parts else "Unknown Blade"
        return {
            "name": blade_name,
            "brand": brand,
            "model": model,
            "user": record.get("author", "Unknown"),
        }


def aggregate_blades(records: list[dict[str, Any]], debug: bool = False) -> list[dict[str, Any]]:
    aggregator = BladeAggregator(debug)
    return aggregator.aggregate(records)
