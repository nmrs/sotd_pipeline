#!/usr/bin/env python3
"""Sample usage metrics aggregator for the SOTD pipeline."""

from typing import Any, Dict, List


def aggregate_sample_usage_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate comprehensive sample usage metrics from enriched records.

    Args:
        records: List of enriched comment records

    Returns:
        Dictionary containing sample usage metrics and distribution data
    """
    if not records:
        return {
            "total_samples": 0,
            "total_shaves": 0,
            "sample_percentage": 0.0,
            "sample_types": {},
            "sample_users": 0,
            "sample_brands": 0,
            "sample_distribution": [],
        }

    # Calculate basic metrics
    total_shaves = len(records)
    total_samples = 0
    sample_records = []
    sample_types = {}
    sample_users = set()
    sample_brands = set()

    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
        enriched = soap.get("enriched", {})

        if enriched.get("sample_type"):
            total_samples += 1

            # Safely get matched data
            matched = soap.get("matched") or {}

            sample_records.append(
                {
                    "author": record.get("author", ""),
                    "sample_type": enriched.get("sample_type"),
                    "sample_number": enriched.get("sample_number"),
                    "total_samples": enriched.get("total_samples"),
                    "brand": matched.get("brand", ""),
                    "scent": matched.get("scent", ""),
                }
            )

            # Track sample types
            sample_type = enriched.get("sample_type", "unknown")
            sample_types[sample_type] = sample_types.get(sample_type, 0) + 1

            # Track unique users and brands
            author = record.get("author", "")
            if author:
                sample_users.add(author)

            brand = matched.get("brand", "")
            if brand:
                sample_brands.add(brand)

    # Calculate percentages
    sample_percentage = (total_samples / total_shaves) * 100 if total_shaves > 0 else 0.0

    # Create sample distribution by type
    sample_distribution = []
    for sample_type, count in sorted(sample_types.items(), key=lambda x: x[1], reverse=True):
        sample_distribution.append(
            {
                "sample_type": sample_type,
                "count": count,
                "percentage": (count / total_samples) * 100 if total_samples > 0 else 0.0,
            }
        )

    return {
        "total_samples": total_samples,
        "total_shaves": total_shaves,
        "sample_percentage": round(sample_percentage, 2),
        "sample_types": sample_types,
        "sample_users": len(sample_users),
        "sample_brands": len(sample_brands),
        "sample_distribution": list(
            sorted(sample_distribution, key=lambda x: x["count"], reverse=True)
        ),
        "unique_sample_users": list(sorted(sample_users)),
        "unique_sample_brands": list(sorted(sample_brands)),
    }
