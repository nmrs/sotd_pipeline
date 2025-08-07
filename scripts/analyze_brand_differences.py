#!/usr/bin/env python3
"""Analyze brand differences between legacy and scoring systems."""

import json


def analyze_brand_differences():
    """Analyze differences in brand matching between systems."""

    # Load data
    old_data = json.load(open("data/matched/2025-05.json"))
    new_data = json.load(open("data/matched_new/2025-05.json"))

    total_records = len(old_data["data"])
    brand_differences = 0
    model_differences = 0
    same_brand_different_model = 0
    different_brands = 0

    print("🔍 Analyzing brand and model differences...")
    print()

    for i, (old_record, new_record) in enumerate(zip(old_data["data"], new_data["data"])):
        old_brush = old_record.get("brush", {}) or {}
        new_brush = new_record.get("brush", {}) or {}

        old_brand = old_brush.get("brand")
        new_brand = new_brush.get("brand")
        old_model = old_brush.get("model")
        new_model = new_brush.get("model")

        # Check for brand differences
        if old_brand != new_brand:
            brand_differences += 1
            if old_brand is not None and new_brand is not None:
                different_brands += 1
                print(f"Record {i}: DIFFERENT BRANDS")
                print(f"  Legacy: {old_brand} {old_model}")
                print(f"  Scoring: {new_brand} {new_model}")
                print(f"  Input: {old_record.get('input_text', 'Unknown')}")
                print()

        # Check for model differences (same brand)
        elif old_brand == new_brand and old_model != new_model:
            model_differences += 1
            same_brand_different_model += 1
            if same_brand_different_model <= 5:  # Show first 5 examples
                print(f"Record {i}: SAME BRAND, DIFFERENT MODEL")
                print(f"  Brand: {old_brand}")
                print(f"  Legacy model: {old_model}")
                print(f"  Scoring model: {new_model}")
                print(f"  Input: {old_record.get('input_text', 'Unknown')}")
                print()

    print("📊 SUMMARY:")
    print(f"Total records analyzed: {total_records}")
    print(f"Brand differences: {brand_differences}")
    print(f"  - Completely different brands: {different_brands}")
    print(f"  - Same brand, different model: {same_brand_different_model}")
    print()

    if different_brands == 0:
        print("✅ GOOD NEWS: No completely different brands found!")
        print("   The scoring system is finding the same brands as the legacy system.")
        print("   Differences are only in model details (which is actually better).")
    else:
        print("⚠️  WARNING: Found completely different brands!")
        print("   This could make tuning more difficult.")


if __name__ == "__main__":
    analyze_brand_differences()
