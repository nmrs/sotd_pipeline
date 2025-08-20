#!/usr/bin/env python3
"""Test script to debug brush matching logic."""

import json
from collections import defaultdict
from pathlib import Path


def extract_text(field_data, field=""):
    """Copy of the extract_text function from unmatched_analyzer.py."""
    if isinstance(field_data, str):
        # Legacy format - already normalized
        return field_data
    elif isinstance(field_data, dict):
        # New structured format - use normalized field
        normalized = field_data.get("normalized", "")
        if normalized:
            return normalized
        # Fallback to original if normalized is not available
        return field_data.get("original", "")
    else:
        return ""


def test_brush_logic():
    """Test the brush matching logic step by step."""
    file_path = Path("data/matched/2025-05.json")

    with open(file_path) as f:
        data = json.load(f)

    brush_records = [
        r
        for r in data["data"]
        if "brush" in r and r["brush"] and "Chisel and Hound" in str(r["brush"].get("original", ""))
    ]

    print(f"Found {len(brush_records)} Chisel and Hound brushes")

    # Test the exact logic from _process_brush_unmatched
    for i, r in enumerate(brush_records[:3]):
        brush = r["brush"]
        matched = brush.get("matched")

        print(f"\n=== Brush {i + 1}: {brush.get('original')} ===")

        if matched is None:
            print("  matched is None - should be unmatched")
            continue

        if not isinstance(matched, dict):
            print("  matched is not dict - should be unmatched")
            continue

        # Check if we have a valid brand match anywhere
        handle = matched.get("handle")
        knot = matched.get("knot")

        has_valid_brand = (
            # Top level brand (not null and not "Unknown" variants)
            (matched.get("brand") and matched.get("brand") not in ["Unknown", "UnknownMaker"])
            or
            # Handle brand (not null and not "Unknown" variants)
            (
                handle
                and handle.get("brand")
                and handle.get("brand") not in ["UnknownMaker", "Unknown"]
            )
            or
            # Knot brand (not null and not "Unknown" variants)
            (knot and knot.get("brand") and knot.get("brand") not in ["UnknownKnot", "Unknown"])
        )

        print(f"  Top brand: {matched.get('brand')}")
        print(f"  Handle brand: {handle.get('brand') if handle else None}")
        print(f"  Knot brand: {knot.get('brand') if knot else None}")
        print(f"  Has valid brand: {has_valid_brand}")

        if has_valid_brand:
            print("  → Should be MATCHED (early return)")
        else:
            print("  → Should be UNMATCHED (continue processing)")

        # Test extract_text
        normalized = extract_text(brush, "brush")
        print(f"  Normalized text: {normalized}")


def test_process_brush_unmatched():
    """Test the exact _process_brush_unmatched method logic."""
    file_path = Path("data/matched/2025-05.json")

    with open(file_path) as f:
        data = json.load(f)

    brush_records = [
        r
        for r in data["data"]
        if "brush" in r and r["brush"] and "Chisel and Hound" in str(r["brush"].get("original", ""))
    ]

    print("\n=== Testing _process_brush_unmatched logic ===")
    print(f"Found {len(brush_records)} Chisel and Hound brushes")

    all_unmatched = defaultdict(list)

    # Simulate the exact logic from _process_brush_unmatched
    for r in brush_records[:3]:
        brush = r["brush"]
        matched = brush.get("matched")

        file_info = {
            "file": r.get("_source_file", ""),
            "line": r.get("_source_line", "unknown"),
            "comment_id": r.get("id", ""),
        }

        print(f"\n--- Processing: {brush.get('original', '')} ---")

        if matched is None:
            print("  matched is None - adding to unmatched")
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(file_info)
            continue

        if not isinstance(matched, dict):
            print("  matched is not dict - adding to unmatched")
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(file_info)
            continue

        # Check if we have a valid brand match anywhere
        handle = matched.get("handle")
        knot = matched.get("knot")

        has_valid_brand = (
            (matched.get("brand") and matched.get("brand") not in ["Unknown", "UnknownMaker"])
            or (
                handle
                and handle.get("brand")
                and handle.get("brand") not in ["UnknownMaker", "Unknown"]
            )
            or (knot and knot.get("brand") and knot.get("brand") not in ["UnknownKnot", "Unknown"])
        )

        print(f"  has_valid_brand: {has_valid_brand}")

        # If we have a valid brand match anywhere, consider it matched
        if has_valid_brand:
            print("  → Early return - brush is MATCHED")
            continue

        print("  → Continue processing - brush is UNMATCHED")
        # ... rest of the logic would continue here

    print(f"\nTotal unmatched: {len(all_unmatched)}")
    for key, value in all_unmatched.items():
        print(f"  {key}: {len(value)} occurrences")


if __name__ == "__main__":
    test_brush_logic()
    test_process_brush_unmatched()
