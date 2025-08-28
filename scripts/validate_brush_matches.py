#!/usr/bin/env python3
"""Simple brush validation script that compares correct_matches.yaml with fresh matcher results.

This script:
1. Extracts brush data from correct_matches.yaml (File A)
2. Runs each string through the brush matcher with bypass_correct_matches=True (File B)
3. Compares the two to find discrepancies
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import SOTD modules after path setup
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


def load_correct_matches() -> Dict[str, Any]:
    """Load correct_matches.yaml and extract brush section."""
    correct_matches_path = project_root / "data" / "correct_matches.yaml"

    with open(correct_matches_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("brush", {})


def create_fresh_matches(brush_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run each brush string through the matcher with bypass_correct_matches=True."""
    # Create brush matcher that bypasses correct_matches.yaml
    config = BrushMatcherConfig(
        catalog_path=project_root / "data" / "brushes.yaml",
        handles_path=project_root / "data" / "handles.yaml",
        knots_path=project_root / "data" / "knots.yaml",
        bypass_correct_matches=True,  # This is crucial!
    )

    brush_matcher = BrushMatcher(config)

    fresh_matches = {}

    for brand, brand_data in brush_data.items():
        fresh_matches[brand] = {}

        for version, version_data in brand_data.items():
            fresh_matches[brand][version] = []

            if isinstance(version_data, list):
                for pattern in version_data:
                    try:
                        # Run through matcher - pass the pattern string directly
                        result = brush_matcher.match(pattern)

                        if result and hasattr(result, "matched") and result.matched:
                            matched_data = result.matched
                            # Store the fresh match result
                            fresh_matches[brand][version].append(
                                {
                                    "pattern": pattern,
                                    "matched_brand": matched_data.get("brand"),
                                    "matched_model": matched_data.get("model"),
                                    "match_type": getattr(result, "match_type", "unknown"),
                                    "strategy": getattr(result, "strategy", "unknown"),
                                }
                            )
                        else:
                            # No match found
                            fresh_matches[brand][version].append(
                                {
                                    "pattern": pattern,
                                    "matched_brand": None,
                                    "matched_model": None,
                                    "match_type": "no_match",
                                    "strategy": "none",
                                }
                            )
                    except Exception as e:
                        # Handle any errors during matching
                        fresh_matches[brand][version].append(
                            {
                                "pattern": pattern,
                                "matched_brand": None,
                                "matched_model": None,
                                "match_type": "error",
                                "strategy": "error",
                                "error": str(e),
                            }
                        )

    return fresh_matches


def find_discrepancies(original: Dict[str, Any], fresh: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find discrepancies between original and fresh matches."""
    discrepancies = []

    for brand, brand_data in original.items():
        if brand not in fresh:
            discrepancies.append(
                {
                    "type": "missing_brand",
                    "brand": brand,
                    "message": f"Brand '{brand}' not found in fresh matches",
                }
            )
            continue

        for version, version_data in brand_data.items():
            if version not in fresh[brand]:
                discrepancies.append(
                    {
                        "type": "missing_version",
                        "brand": brand,
                        "version": version,
                        "message": f"Version '{version}' not found for brand '{brand}' in fresh matches",
                    }
                )
                continue

            if isinstance(version_data, list):
                for i, pattern in enumerate(version_data):
                    if i < len(fresh[brand][version]):
                        fresh_result = fresh[brand][version][i]

                        # Check if pattern matches what we expect
                        if fresh_result["matched_brand"] != brand:
                            expected_msg = f"Pattern '{pattern}' expected brand '{brand}' but got '{fresh_result['matched_brand']}'"
                            discrepancies.append(
                                {
                                    "type": "brand_mismatch",
                                    "brand": brand,
                                    "version": version,
                                    "pattern": pattern,
                                    "expected_brand": brand,
                                    "actual_brand": fresh_result["matched_brand"],
                                    "message": expected_msg,
                                }
                            )

                        # Check if no match was found
                        if fresh_result["match_type"] == "no_match":
                            discrepancies.append(
                                {
                                    "type": "no_match",
                                    "brand": brand,
                                    "version": version,
                                    "pattern": pattern,
                                    "message": f"Pattern '{pattern}' could not be matched by brush matcher",
                                }
                            )
                    else:
                        discrepancies.append(
                            {
                                "type": "missing_pattern",
                                "brand": brand,
                                "version": version,
                                "pattern": pattern,
                                "message": f"Pattern '{pattern}' not found in fresh matches",
                            }
                        )

    return discrepancies


def main():
    """Main validation function."""
    print("🔍 Loading brush data from correct_matches.yaml...")
    original_data = load_correct_matches()

    print(f"📊 Found {len(original_data)} brands in correct_matches.yaml")

    print("🔄 Running fresh brush matching (bypassing correct_matches.yaml)...")
    fresh_data = create_fresh_matches(original_data)

    print("🔍 Comparing original vs fresh matches...")
    discrepancies = find_discrepancies(original_data, fresh_data)

    print("\n📋 Validation Results:")
    print(f"   Total discrepancies found: {len(discrepancies)}")

    if discrepancies:
        print("\n🚨 Discrepancies found:")

        # Group by type
        by_type = {}
        for disc in discrepancies:
            disc_type = disc["type"]
            if disc_type not in by_type:
                by_type[disc_type] = []
            by_type[disc_type].append(disc)

        for disc_type, items in by_type.items():
            print(f"\n   {disc_type.upper()} ({len(items)} items):")
            for item in items:
                print(f"     • {item['message']}")

                # Show specific details for brand mismatches
                if disc_type == "brand_mismatch":
                    print(f"       Expected: {item['expected_brand']}")
                    print(f"       Actual: {item['actual_brand']}")
                    print(f"       Pattern: {item['pattern']}")
    else:
        print("\n✅ No discrepancies found! All patterns match correctly.")

    # Save both files for manual inspection
    output_dir = project_root / "data" / "validation_output"
    output_dir.mkdir(exist_ok=True)

    # Save original data
    with open(output_dir / "original_brush_data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(original_data, f, default_flow_style=False, indent=2)

    # Save fresh data
    with open(output_dir / "fresh_brush_data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(fresh_data, f, default_flow_style=False, indent=2)

    print("\n💾 Output files saved to:")
    print(f"   Original: {output_dir / 'original_brush_data.yaml'}")
    print(f"   Fresh: {output_dir / 'fresh_brush_data.yaml'}")


if __name__ == "__main__":
    main()
