#!/usr/bin/env python3
"""Detailed analysis of differences between legacy and scoring systems."""

import json


def analyze_differences():
    """Analyze all differences between legacy and scoring systems."""

    # Load data
    old_data = json.load(open("data/matched/2025-05.json"))
    new_data = json.load(open("data/matched_new/2025-05.json"))

    total_records = len(old_data["data"])
    exact_matches = 0
    brand_differences = 0
    model_differences = 0
    structure_differences = 0
    unmatched_differences = 0

    print("🔍 Detailed Analysis of All Differences...")
    print()

    for i, (old_record, new_record) in enumerate(zip(old_data["data"], new_data["data"])):
        old_brush = old_record.get("brush", {}) or {}
        new_brush = new_record.get("brush", {}) or {}

        # Get the matched field (this is what the comparator uses)
        old_matched = old_brush.get("matched", {})
        new_matched = new_brush.get("matched", {})

        old_brand = old_matched.get("brand")
        new_brand = new_matched.get("brand")
        old_model = old_matched.get("model")
        new_model = new_matched.get("model")

        # Check if both are unmatched
        if old_brand is None and new_brand is None:
            exact_matches += 1
            continue

        # Check if one is unmatched and the other isn't
        if (old_brand is None) != (new_brand is None):
            unmatched_differences += 1
            print(f"Record {i}: UNMATCHED DIFFERENCE")
            print(f"  Legacy: {old_brand} {old_model}")
            print(f"  Scoring: {new_brand} {new_model}")
            print(f"  Input: {old_record.get('input_text', 'Unknown')}")
            print()
            continue

        # Both are matched - check for differences
        if old_brand == new_brand and old_model == new_model:
            exact_matches += 1
        else:
            if old_brand != new_brand:
                brand_differences += 1
                print(f"Record {i}: BRAND DIFFERENCE")
                print(f"  Legacy: {old_brand} {old_model}")
                print(f"  Scoring: {new_brand} {new_model}")
                print(f"  Input: {old_record.get('input_text', 'Unknown')}")
                print()
            elif old_model != new_model:
                model_differences += 1
                print(f"Record {i}: MODEL DIFFERENCE")
                print(f"  Brand: {old_brand}")
                print(f"  Legacy model: {old_model}")
                print(f"  Scoring model: {new_model}")
                print(f"  Input: {old_record.get('input_text', 'Unknown')}")
                print()

    print("📊 COMPLETE SUMMARY:")
    print(f"Total records: {total_records}")
    print(f"Exact matches: {exact_matches} ({exact_matches / total_records * 100:.1f}%)")
    print(f"Brand differences: {brand_differences}")
    print(f"Model differences: {model_differences}")
    print(f"Unmatched differences: {unmatched_differences}")
    print(f"Total differences: {brand_differences + model_differences + unmatched_differences}")
    print()

    if brand_differences == 0:
        print("✅ EXCELLENT: No brand differences found!")
        print("   Both systems identify the same brands.")
    else:
        print(f"⚠️  Found {brand_differences} brand differences")

    if model_differences > 0:
        print(f"📝 Found {model_differences} model differences")
        print("   These are likely improvements in the scoring system")

    print(f"🎯 Agreement rate: {exact_matches / total_records * 100:.1f}%")


if __name__ == "__main__":
    analyze_differences()
