#!/usr/bin/env python3
"""
Validation script to check brush brand matching logic
"""

import json
from pathlib import Path


def validate_brand_matching():
    """Validate brush brand matching logic"""

    # Load the matched data
    matched_file = Path("data/matched/2025-06.json")
    if not matched_file.exists():
        print(f"Error: {matched_file} not found")
        return

    with open(matched_file, "r") as f:
        data = json.load(f)

    records = data.get("data", data)
    print(f"Total records: {len(records)}")

    # Extract brush records
    brush_records = []
    for record in records:
        if "brush" in record and "matched" in record["brush"]:
            brush_records.append(record["brush"])

    print(f"Brush records with matched data: {len(brush_records)}")

    # Analyze brand matching
    same_brand_cases = 0
    correct_brand_cases = 0
    different_brand_cases = 0

    for brush in brush_records:
        matched = brush.get("matched")
        if not matched:
            continue

        handle_brand = matched.get("handle", {}).get("brand")
        knot_brand = matched.get("knot", {}).get("brand")
        top_brand = matched.get("brand")

        if handle_brand and knot_brand and handle_brand == knot_brand:
            same_brand_cases += 1
            if top_brand == handle_brand:
                correct_brand_cases += 1
            else:
                print(
                    f"❌ Brand mismatch: handle={handle_brand}, knot={knot_brand}, "
                    f"top={top_brand} (case sensitive: {handle_brand == knot_brand})"
                )
                # Add more debugging info for the remaining cases
                print(f"  - Source text: {matched.get('source_text', 'N/A')}")
                print(f"  - Matched by: {matched.get('_matched_by', 'N/A')}")
                print(f"  - Pattern: {matched.get('_pattern', 'N/A')}")
                print(
                    f"  - Handle matched by: {matched.get('handle', {}).get('_matched_by', 'N/A')}"
                )
                print(f"  - Knot matched by: {matched.get('knot', {}).get('_matched_by', 'N/A')}")
                print(f"  - Strategy: {matched.get('_matched_by_strategy', 'N/A')}")
                print("  ---")
        elif handle_brand and knot_brand and handle_brand != knot_brand:
            different_brand_cases += 1

    print("\n=== BRAND MATCHING ANALYSIS ===")
    print(f"Same knot/handle brand cases: {same_brand_cases}")
    print(f"Correctly matched brands: {correct_brand_cases}")
    print(f"Different knot/handle brand cases: {different_brand_cases}")

    if same_brand_cases > 0:
        success_rate = correct_brand_cases / same_brand_cases * 100
        print(f"Success rate: {success_rate:.1f}%")
    else:
        print("No cases to test")

    if correct_brand_cases == same_brand_cases and same_brand_cases > 0:
        print("✅ FIX SUCCESSFUL: All same-brand cases now have correct top-level brand!")
    elif same_brand_cases > 0:
        print("❌ FIX INCOMPLETE: Some cases still have brand mismatches")


if __name__ == "__main__":
    validate_brand_matching()
