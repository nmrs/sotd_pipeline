#!/usr/bin/env python3
"""Confidence analysis for product matching validation."""

import re
from typing import Any, Dict, List


def analyze_match_confidence(
    original: str, matched_brand: str, matched_model: str, match_type: str
) -> Dict[str, Any]:
    """Analyze the confidence of a match and detect potential mismatches."""
    confidence_score = 100
    issues = []
    warnings = []

    original_lower = original.lower()

    # Basic confidence based on match type
    if match_type == "exact":
        confidence_score = 95
    elif match_type == "brand_default":
        confidence_score = 60  # Lower confidence for generic matches
    else:
        confidence_score = 40

    # Check if matched brand appears in original text
    brand_in_original = matched_brand.lower() in original_lower
    if not brand_in_original and match_type != "brand_default":
        confidence_score -= 20
        issues.append("matched_brand_not_in_original")

    # Check for competing brand names in original
    competing_brands = detect_competing_brands(original, matched_brand)
    if competing_brands:
        confidence_score -= 30
        warnings.append(f"competing_brands_found: {', '.join(competing_brands)}")

    # Check for knot maker vs handle maker confusion
    knot_maker_issues = detect_knot_maker_confusion(original, matched_brand)
    if knot_maker_issues:
        confidence_score -= 25
        warnings.append(f"possible_knot_maker_confusion: {knot_maker_issues}")

    # Check for generic model fallbacks
    if matched_model in ["Synthetic", "Badger", "Boar"] and match_type == "brand_default":
        confidence_score -= 10
        issues.append("generic_model_fallback")

    # Check for specific model in original but generic match
    if match_type == "brand_default" and has_specific_model_info(original):
        confidence_score -= 15
        warnings.append("specific_model_info_ignored")

    # Boost confidence for well-established patterns
    if match_type == "exact" and brand_in_original:
        confidence_score = min(100, confidence_score + 10)

    confidence_level = (
        "high" if confidence_score >= 80 else "medium" if confidence_score >= 60 else "low"
    )

    return {
        "score": max(0, confidence_score),
        "level": confidence_level,
        "issues": issues,
        "warnings": warnings,
        "is_potential_mismatch": confidence_score < 70,
    }


def detect_competing_brands(original: str, matched_brand: str) -> List[str]:
    """Detect if there are other brand names in the original that might be more relevant."""
    # Common brush/knot brands that might be confused
    brush_brands = [
        "maggard",
        "declaration",
        "chisel",
        "hound",
        "ap shave",
        "zenith",
        "omega",
        "semogue",
        "yaqi",
        "oumo",
        "muhle",
        "simpson",
        "stirling",
        "dogwood",
        "grizzly bay",
        "turn.n.shave",
        "wolf whiskers",
        "summer break",
        "elite",
        "farvour",
        "rubberset",
        "ever.ready",
        "parker",
        "kent",
        "vulfix",
    ]

    original_lower = original.lower()
    matched_lower = matched_brand.lower()
    competing = []

    for brand in brush_brands:
        brand_clean = brand.replace(".", "").replace(" ", "")
        original_clean = original_lower.replace(" ", "").replace("-", "").replace(".", "")
        matched_clean = matched_lower.replace(" ", "").replace("-", "").replace(".", "")
        if brand_clean in original_clean:
            if brand_clean != matched_clean:
                competing.append(brand.title())

    return competing


def detect_knot_maker_confusion(original: str, matched_brand: str) -> str:
    """Detect if we might have confused knot maker with handle maker."""
    original_lower = original.lower()

    # Common patterns indicating knot maker
    knot_patterns = [
        r"w/\s*(\w+(?:\s+\w+)?)\s+(?:knot|shd|badger|boar|synthetic)",
        r"with\s+(\w+(?:\s+\w+)?)\s+(?:knot|shd|badger|boar|synthetic)",
        r"(\w+(?:\s+\w+)?)\s+(?:knot|shd)\s+(?:badger|boar|synthetic)",
        r"(\w+)\s+(?:26mm|24mm|28mm|30mm)\s+(?:knot|shd|badger|boar|synthetic)",
    ]

    for pattern in knot_patterns:
        matches = re.findall(pattern, original_lower, re.IGNORECASE)
        for match in matches:
            potential_knot_maker = match.strip()
            if (
                potential_knot_maker
                and potential_knot_maker != matched_brand.lower()
                and len(potential_knot_maker) > 2
            ):
                return potential_knot_maker.title()

    return ""


def has_specific_model_info(original: str) -> bool:
    """Check if original contains specific model information that might be ignored."""
    original_lower = original.lower()

    # Look for specific model indicators
    model_indicators = [
        r"\b(?:tuxedo|cashmere|synbad|g5[abc]|pure\s*bliss|gelousy|titanium)\b",
        r"\b(?:chubby|trafalgar|manchurian|silvertip|finest)\b",
        r"\b(?:v\d+|b\d+|t\d+)\b",  # Version/batch numbers
        r"\b\d{4,5}\b",  # Model numbers like 10048, 20102
    ]

    for pattern in model_indicators:
        if re.search(pattern, original_lower):
            return True

    return False
