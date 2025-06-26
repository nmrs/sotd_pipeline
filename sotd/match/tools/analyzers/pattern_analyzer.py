#!/usr/bin/env python3
"""Pattern analysis for product matching validation."""

from collections import defaultdict
from typing import Any, Dict, List

from sotd.match.tools.confidence_analyzer import analyze_match_confidence


def get_pattern_effectiveness(
    data: List[Dict[str, Any]], field: str = "brush"
) -> Dict[str, Dict[str, Any]]:
    """Analyze which patterns are most/least effective."""
    pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "exact": 0, "brand_default": 0, "confidence_scores": []}
    )

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            pattern = field_data.get("pattern", "unknown")
            match_type = field_data.get("match_type", "unknown")

            original = field_data.get("original", "")
            matched = field_data["matched"]
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            confidence = analyze_match_confidence(original, brand, model, match_type)

            pattern_stats[pattern]["total"] += 1
            pattern_stats[pattern][match_type] += 1
            pattern_stats[pattern]["confidence_scores"].append(confidence["score"])

    # Calculate effectiveness scores
    for pattern, stats in pattern_stats.items():
        if stats["total"] > 0:
            stats["exact_rate"] = stats["exact"] / stats["total"]
            stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(
                stats["confidence_scores"]
            )

            # Combined effectiveness based on exact rate and confidence
            combined_score = (stats["exact_rate"] * 0.6) + (stats["avg_confidence"] / 100 * 0.4)

            effectiveness = (
                "high" if combined_score >= 0.8 else "medium" if combined_score >= 0.6 else "low"
            )
            stats["effectiveness"] = effectiveness
            stats["combined_score"] = combined_score

    return dict(pattern_stats)


def identify_improvement_opportunities(
    data: List[Dict[str, Any]], field: str = "brush"
) -> List[Dict[str, Any]]:
    """Identify specific opportunities for improving matches."""
    opportunities = []
    brand_model_counts = defaultdict(int)
    low_confidence_patterns = defaultdict(list)

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            # Analyze confidence
            confidence = analyze_match_confidence(original, brand, model, match_type)

            # Track low confidence matches
            if confidence["is_potential_mismatch"]:
                low_confidence_patterns[f"{brand} {model}"].append(
                    {"original": original, "confidence": confidence, "match_type": match_type}
                )

            # Count brand+model combinations that fall back to brand_default
            if match_type == "brand_default":
                key = f"{brand} {model}".strip()
                brand_model_counts[key] += 1

    # Find high-frequency brand_default matches
    for combo, count in brand_model_counts.items():
        if count >= 3:
            opportunities.append(
                {
                    "type": "frequent_brand_default",
                    "description": f"{combo} appears {count} times as brand_default",
                    "suggestion": f"Consider adding specific pattern for '{combo}'",
                    "count": count,
                    "priority": "high" if count >= 10 else "medium",
                }
            )

    # Find patterns with low confidence
    for pattern, matches in low_confidence_patterns.items():
        if len(matches) >= 2:
            avg_confidence = sum(m["confidence"]["score"] for m in matches) / len(matches)
            sample_warnings = []
            for match in matches[:2]:  # Show first 2 examples
                sample_warnings.extend(match["confidence"]["warnings"])

            opportunities.append(
                {
                    "type": "low_confidence_pattern",
                    "description": (
                        f"{pattern} has {len(matches)} low-confidence matches "
                        f"(avg: {avg_confidence:.1f}%)"
                    ),
                    "suggestion": (f"Review pattern accuracy: {'; '.join(set(sample_warnings))}"),
                    "count": len(matches),
                    "priority": "high" if avg_confidence < 50 else "medium",
                }
            )

    return sorted(
        opportunities, key=lambda x: (x.get("priority") == "high", x["count"]), reverse=True
    )
