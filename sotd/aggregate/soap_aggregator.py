#!/usr/bin/env python3
"""Soap-specific aggregation using the base aggregator pattern."""

from typing import Any, Dict, Optional

from sotd.aggregate.base_aggregator import BaseAggregator


class SoapAggregator(BaseAggregator):
    """Aggregator for soap usage statistics."""

    def get_operation_name(self) -> str:
        return "aggregate_soaps"

    def get_product_type(self) -> str:
        return "soap"

    def get_group_column(self) -> str:
        return "name"

    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        if "soap" not in record:
            return None
        soap_info = record["soap"]
        if not isinstance(soap_info, dict) or "matched" not in soap_info:
            return None
        matched = soap_info["matched"]
        if not isinstance(matched, dict) or not matched.get("maker"):
            return None
        if not self._validate_match_type(matched, record_index):
            return None
        maker = matched.get("maker", "")
        scent = matched.get("scent", "")
        # Create a descriptive soap name (maker + scent)
        soap_name_parts = []
        if maker:
            soap_name_parts.append(maker)
        if scent:
            soap_name_parts.append(scent)
        soap_name = " ".join(soap_name_parts) if soap_name_parts else "Unknown Soap"
        return {
            "name": soap_name,
            "maker": maker,
            "scent": scent,
            "user": record.get("author", "Unknown"),
        }


def aggregate_soaps(records: list[dict[str, Any]], debug: bool = False) -> list[dict[str, Any]]:
    aggregator = SoapAggregator(debug)
    return aggregator.aggregate(records)
