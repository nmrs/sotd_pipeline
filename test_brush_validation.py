#!/usr/bin/env python3
"""Test brush validation logic to debug mismatch detection."""

from pathlib import Path
from sotd.match.config import BrushMatcherConfig
from sotd.match.brush_matcher import BrushMatcher


def test_brush_validation():
    """Test brush validation logic for the problematic entries."""

    # Create brush matcher with bypass_correct_matches=True
    config = BrushMatcherConfig(
        catalog_path=Path("data/brushes.yaml"),
        handles_path=Path("data/handles.yaml"),
        knots_path=Path("data/knots.yaml"),
        bypass_correct_matches=True,
    )

    matcher = BrushMatcher(config)
    print(f"Brush matcher created with bypass_correct_matches={config.bypass_correct_matches}")
    print(f"Correct matches loaded: {len(matcher.correct_matches)}")
    print(f"Correct matches checker: {matcher.correct_matches_checker is not None}")
    print()

    # Test the problematic entry
    test_entry = "c&h x mammoth dinos'mores (5407mc) 26mm v27 fanchurian"
    print(f"Testing entry: {test_entry}")

    # Test with brush matcher
    result = matcher.match(test_entry)
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")

    if result:
        print(f"Result attributes: {dir(result)}")

        # Check if it has matched attribute
        if hasattr(result, "matched"):
            print(f"Has matched attribute: {hasattr(result, 'matched')}")
            matched_data = result.matched
            print(f"Matched data: {matched_data}")

            if matched_data:
                actual_brand = matched_data.get("brand")
                actual_model = matched_data.get("model")
                print(f"Actual brand: {actual_brand}")
                print(f"Actual model: {actual_model}")

                # Simulate validation logic
                expected_brand = "Chisel & Hound"
                expected_model = "v26"  # Current placement in correct_matches.yaml

                print(f"Expected brand: {expected_brand}")
                print(f"Expected model: {expected_model}")

                if actual_brand != expected_brand or actual_model != expected_model:
                    print("❌ MISMATCH DETECTED!")
                    print(f"  Expected: {expected_brand} {expected_model}")
                    print(f"  Actual: {actual_brand} {actual_model}")
                else:
                    print("✅ No mismatch detected")
            else:
                print("❌ No matched data")
        else:
            print("❌ Result does not have 'matched' attribute")
    else:
        print("❌ No result returned")


if __name__ == "__main__":
    test_brush_validation()
