"""
Enhanced match statistics calculator for match phase metadata.

This module provides comprehensive statistics about match results including
field type counts, match type breakdowns, and performance metrics.
"""

from collections import Counter
from typing import Any, Dict, List


def calculate_match_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive match statistics from processed records.

    Args:
        records: List of processed comment records with match data

    Returns:
        Dictionary containing comprehensive match statistics
    """
    # Initialize counters
    field_counts = Counter()
    match_type_counts = Counter()
    field_match_type_counts = {
        "razor": Counter(),
        "blade": Counter(),
        "brush": Counter(),
        "soap": Counter(),
    }

    # Track total records and successful matches
    total_records = len(records)
    total_matched = 0
    total_unmatched = 0

    # Analyze each record
    for record in records:
        for field in ["razor", "blade", "brush", "soap"]:
            field_data = record.get(field, {})

            if field_data and isinstance(field_data, dict):
                # Count field presence
                field_counts[field] += 1

                # Analyze match results
                matched = field_data.get("matched")
                match_type = field_data.get("match_type")

                if matched is not None:
                    total_matched += 1
                    if match_type:
                        match_type_counts[match_type] += 1
                        field_match_type_counts[field][match_type] += 1
                else:
                    total_unmatched += 1
                    # Count unmatched fields
                    if match_type is None:
                        field_match_type_counts[field]["unmatched"] += 1

    # Calculate percentages
    match_rate = (
        (total_matched / (total_matched + total_unmatched) * 100)
        if (total_matched + total_unmatched) > 0
        else 0
    )

    # Build comprehensive statistics
    statistics = {
        "total_records": total_records,
        "field_presence": dict(field_counts),
        "match_summary": {
            "total_matched": total_matched,
            "total_unmatched": total_unmatched,
            "match_rate_percent": round(match_rate, 2),
        },
        "match_types": {
            "overall": dict(match_type_counts),
            "by_field": {
                field: dict(counter) for field, counter in field_match_type_counts.items()
            },
        },
        "field_analysis": {},
    }

    # Add detailed field analysis
    for field in ["razor", "blade", "brush", "soap"]:
        field_counter = field_match_type_counts[field]
        field_total = field_counts[field]

        if field_total > 0:
            field_stats = {
                "total_present": field_total,
                "match_breakdown": dict(field_counter),
                "success_rate_percent": round(
                    (
                        sum(
                            count
                            for match_type, count in field_counter.items()
                            if match_type != "unmatched"
                        )
                        / field_total
                        * 100
                    ),
                    2,
                ),
            }

            # Add specific match type percentages for each field
            for match_type, count in field_counter.items():
                if field_total > 0:
                    field_stats[f"{match_type}_percent"] = round((count / field_total * 100), 2)

            statistics["field_analysis"][field] = field_stats

    return statistics


def format_match_statistics_for_display(statistics: Dict[str, Any]) -> str:
    """
    Format match statistics into a human-readable string for CLI output.

    Args:
        statistics: Statistics dictionary from calculate_match_statistics

    Returns:
        Formatted string for display
    """
    lines = []
    lines.append("Match Statistics Summary:")
    lines.append("=" * 50)

    # Overall summary
    match_summary = statistics["match_summary"]
    lines.append(f"Total Records: {statistics['total_records']:,}")
    lines.append(f"Total Matched: {match_summary['total_matched']:,}")
    lines.append(f"Total Unmatched: {match_summary['total_unmatched']:,}")
    lines.append(f"Overall Match Rate: {match_summary['match_rate_percent']:.1f}%")

    # Field presence
    lines.append("\nField Presence:")
    for field, count in statistics["field_presence"].items():
        lines.append(f"  {field.capitalize()}: {count:,}")

    # Overall match types
    lines.append("\nOverall Match Types:")
    for match_type, count in statistics["match_types"]["overall"].items():
        lines.append(f"  {match_type}: {count:,}")

    # Field-specific analysis
    lines.append("\nField-Specific Analysis:")
    for field, field_stats in statistics["field_analysis"].items():
        lines.append(f"\n  {field.capitalize()}:")
        lines.append(f"    Present: {field_stats['total_present']:,}")
        lines.append(f"    Success Rate: {field_stats['success_rate_percent']:.1f}%")

        # Show match type breakdown for this field
        for match_type, count in field_stats["match_breakdown"].items():
            if count > 0:
                percentage = field_stats.get(f"{match_type}_percent", 0)
                lines.append(f"      {match_type}: {count:,} ({percentage:.1f}%)")

    return "\n".join(lines)
