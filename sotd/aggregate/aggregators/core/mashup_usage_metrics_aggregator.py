#!/usr/bin/env python3
"""Mashup usage metrics aggregator for the SOTD pipeline."""

from typing import Any, Dict, List


def aggregate_mashup_usage_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate mashup usage metrics from enriched records.

    Keys off soap.enriched.is_mashup only. No brand-level metrics (mashup
    content is often unknown or multi-brand).

    Args:
        records: List of enriched comment records

    Returns:
        Dictionary containing total_mashup_shaves, total_shaves, mashup_percentage,
        mashup_users.
    """
    if not records:
        return {
            "total_mashup_shaves": 0,
            "total_shaves": 0,
            "mashup_percentage": 0.0,
            "mashup_users": 0,
        }

    total_shaves = len(records)
    total_mashup_shaves = 0
    mashup_users = set()

    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
        enriched = soap.get("enriched", {})
        if enriched.get("is_mashup") is not True:
            continue
        total_mashup_shaves += 1
        author = record.get("author", "")
        if author and isinstance(author, str) and author.strip():
            mashup_users.add(author.strip())

    mashup_percentage = (
        round((total_mashup_shaves / total_shaves) * 100, 2) if total_shaves > 0 else 0.0
    )

    return {
        "total_mashup_shaves": total_mashup_shaves,
        "total_shaves": total_shaves,
        "mashup_percentage": mashup_percentage,
        "mashup_users": len(mashup_users),
    }
