#!/usr/bin/env python3
"""Data processing functionality for analysis tools."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sotd.cli_utils.date_span import month_span


def load_analysis_data(args: Any) -> List[Dict[str, Any]]:
    """Load data for analysis from the specified time period."""
    all_data = []

    # Collect all data
    for year, month in month_span(args):
        path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
                all_data.extend(content.get("data", []))

    return all_data


def extract_field_data(
    data: List[Dict[str, Any]], field: str = "brush"
) -> Tuple[List[Tuple[str, str, str, str]], List[str], List[float]]:
    """Extract field-specific data and calculate confidence scores."""
    field_matches = []
    match_types = []
    confidence_scores = []

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and isinstance(field_data.get("matched"), dict):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            field_matches.append((original, brand, model, match_type))
            match_types.append(match_type)

            # Analyze match confidence
            from sotd.match.tools.analyzers.confidence_analyzer import analyze_match_confidence

            confidence = analyze_match_confidence(original, brand, model, match_type)
            confidence_scores.append(confidence["score"])

    return field_matches, match_types, confidence_scores


def calculate_summary_statistics(
    field_matches: List[Tuple[str, str, str, str]],
    match_types: List[str],
    confidence_scores: List[float],
) -> Dict[str, Any]:
    """Calculate summary statistics from the extracted data."""
    from collections import Counter

    total_matches = len(field_matches)
    match_type_counts = Counter(match_types)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    potential_mismatches = sum(1 for score in confidence_scores if score < 70)

    return {
        "total_matches": total_matches,
        "match_type_counts": match_type_counts,
        "avg_confidence": avg_confidence,
        "potential_mismatches": potential_mismatches,
        "confidence_scores": confidence_scores,
    }
