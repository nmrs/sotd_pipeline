#!/usr/bin/env python3
"""
Data-driven analysis of implicit product mentions in skipped comments.
Extract product names without explicit field labels and test against matchers.
"""

import json
import re
import sys

sys.path.append(".")

from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher


def extract_implicit_products():
    """Extract product mentions that don't have explicit field labels."""

    with open("skipped_patterns_analysis.json", "r") as f:
        data = json.load(f)

    print("=" * 80)
    print("IMPLICIT PRODUCT ANALYSIS - DATA DRIVEN APPROACH")
    print("=" * 80)

    # Look for lines that might contain product names without field labels
    patterns_to_analyze = [
        "dash_prefix_format",
        "plain_colon_format",
        "asterisk_format",
        "other",  # This might contain implicit products
    ]

    implicit_products = []

    for pattern in patterns_to_analyze:
        if pattern in data["examples"]:
            examples = data["examples"][pattern]
            count = data["pattern_counts"][pattern]

            print(f"\n{pattern.upper()} ({count} occurrences):")
            print("-" * 60)

            for example in examples:
                line = example["line"]

                # Skip lines that have explicit field labels
                if re.search(
                    r"[-:]\s*(razor|blade|brush|soap|lather|hardware|software)", line, re.IGNORECASE
                ):
                    continue

                # Look for lines that might contain product names
                # Common patterns: brand names, model numbers, etc.
                if re.search(
                    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\d+[A-Z]*\b", line
                ):  # Brand Model 123
                    implicit_products.append(
                        {
                            "line": line,
                            "month": example["month"],
                            "pattern": pattern,
                            "type": "brand_model_number",
                        }
                    )
                elif re.search(r"\b[A-Z]{2,}\s+[A-Z]{2,}\b", line):  # AB CD format
                    implicit_products.append(
                        {
                            "line": line,
                            "month": example["month"],
                            "pattern": pattern,
                            "type": "abbreviated_brand",
                        }
                    )
                elif re.search(r"\b[A-Z][a-z]+\s+&\s+[A-Z][a-z]+\b", line):  # Brand & Brand
                    implicit_products.append(
                        {
                            "line": line,
                            "month": example["month"],
                            "pattern": pattern,
                            "type": "brand_and_brand",
                        }
                    )
                elif re.search(
                    r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b", line
                ):  # Multi-word brand
                    implicit_products.append(
                        {
                            "line": line,
                            "month": example["month"],
                            "pattern": pattern,
                            "type": "multi_word_brand",
                        }
                    )

    print(f"\nIMPLICIT PRODUCT CANDIDATES FOUND: {len(implicit_products)}")
    print("=" * 60)

    # Show examples by type
    by_type = {}
    for product in implicit_products:
        ptype = product["type"]
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(product)

    for ptype, products in by_type.items():
        print(f"\n{ptype.upper()} ({len(products)} examples):")
        for product in products[:5]:  # Show first 5
            print(f"  {product['line']}")
            print(f"    Month: {product['month']}")
        if len(products) > 5:
            print(f"    ... and {len(products) - 5} more")

    return implicit_products


def test_against_matchers(implicit_products):
    """Test implicit products against existing matchers."""

    print("=" * 80)
    print("MATCHER TESTING")
    print("=" * 80)

    # Initialize matchers
    razor_matcher = RazorMatcher()
    blade_matcher = BladeMatcher()
    brush_matcher = BrushMatcher()
    soap_matcher = SoapMatcher()

    matchers = {
        "razor": razor_matcher,
        "blade": blade_matcher,
        "brush": brush_matcher,
        "soap": soap_matcher,
    }

    match_results = {
        "razor": {"matches": [], "no_match": []},
        "blade": {"matches": [], "no_match": []},
        "brush": {"matches": [], "no_match": []},
        "soap": {"matches": [], "no_match": []},
    }

    print(f"\nTesting {len(implicit_products)} implicit products against matchers...")

    for product in implicit_products:
        line = product["line"]

        # Extract potential product name (remove common prefixes/suffixes)
        clean_line = re.sub(r"^[-*•‣⁃▪‧·~+]\s*", "", line)  # Remove bullet points
        clean_line = re.sub(r"\s*[-:]\s*.*$", "", clean_line)  # Remove everything after colon/dash
        clean_line = clean_line.strip()

        if not clean_line or len(clean_line) < 2:
            continue

        print(f"\nTesting: '{clean_line}' (from: {line})")

        # Test against each matcher
        for field, matcher in matchers.items():
            try:
                match_result = matcher.match(clean_line)

                # Check if matched using the MatchResult object
                if match_result.matched:
                    match_results[field]["matches"].append(
                        {
                            "original": line,
                            "clean": clean_line,
                            "match": match_result.matched,
                            "match_type": match_result.match_type,
                            "pattern": match_result.pattern,
                            "month": product["month"],
                        }
                    )

                    # Extract brand/model from matched data
                    matched_data = match_result.matched
                    brand = matched_data.get("brand", "Unknown")
                    model = matched_data.get("model", "")
                    print(f"  ✓ {field}: {brand} {model}")
                else:
                    match_results[field]["no_match"].append(
                        {"original": line, "clean": clean_line, "month": product["month"]}
                    )
                    print(f"  ✗ {field}: No match")

            except Exception as e:
                print(f"  ✗ {field}: Error - {e}")

    # Report results
    print("=" * 80)
    print("MATCHER TESTING RESULTS")
    print("=" * 80)

    total_matches = 0
    for field, results in match_results.items():
        matches = len(results["matches"])
        no_matches = len(results["no_match"])
        total_matches += matches

        print(f"\n{field.upper()}:")
        print(f"  Matches: {matches}")
        print(f"  No matches: {no_matches}")

        if matches > 0:
            print("  Examples:")
            for match in results["matches"][:3]:  # Show first 3
                brand = match["match"].get("brand", "Unknown")
                model = match["match"].get("model", "")
                print(f"    '{match['clean']}' → {brand} {model}")
                print(f"      Type: {match['match_type']}")
                print(f"      Pattern: {match['pattern']}")
                print(f"      Month: {match['month']}")

    print(f"\nTOTAL MATCHES: {total_matches} out of {len(implicit_products)} tested")

    return match_results


def analyze_match_quality(match_results):
    """Analyze the quality of matches found."""

    print("=" * 80)
    print("MATCH QUALITY ANALYSIS")
    print("=" * 80)

    # Count matches by confidence/type
    high_confidence_matches = []
    low_confidence_matches = []

    for field, results in match_results.items():
        for match in results["matches"]:
            match_data = match["match"]

            # Check if this looks like a high-confidence match
            has_brand = bool(match_data.get("brand"))
            has_model = bool(match_data.get("model"))
            has_match_type = match["match_type"] in ["exact", "regex"]

            if has_brand and (has_model or has_match_type):
                high_confidence_matches.append(match)
            else:
                low_confidence_matches.append(match)

    print(f"High confidence matches: {len(high_confidence_matches)}")
    print(f"Low confidence matches: {len(low_confidence_matches)}")

    if high_confidence_matches:
        print("\nHIGH CONFIDENCE EXAMPLES:")
        for match in high_confidence_matches[:5]:
            brand = match["match"].get("brand", "Unknown")
            model = match["match"].get("model", "")
            print(f"  '{match['clean']}' → {brand} {model}")
            print(f"    Type: {match['match_type']}")
            print(f"    Month: {match['month']}")

    if low_confidence_matches:
        print("\nLOW CONFIDENCE EXAMPLES:")
        for match in low_confidence_matches[:5]:
            brand = match["match"].get("brand", "Unknown")
            model = match["match"].get("model", "")
            print(f"  '{match['clean']}' → {brand} {model}")
            print(f"    Type: {match['match_type']}")
            print(f"    Month: {match['month']}")


if __name__ == "__main__":
    implicit_products = extract_implicit_products()
    if implicit_products:
        match_results = test_against_matchers(implicit_products)
        analyze_match_quality(match_results)
    else:
        print("\nNo implicit product candidates found.")
