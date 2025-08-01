#!/usr/bin/env python3
"""
Script to remove user_intent from simple brush entries in correct_matches.yaml.

Simple brushes should not have user_intent since they are not composite
(no separate handle/knot components to analyze).
"""

import yaml
from pathlib import Path


def cleanup_simple_brush_user_intent():
    """Remove user_intent from simple brush entries."""

    correct_matches_path = Path("data/correct_matches.yaml")

    # Load the file
    with open(correct_matches_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Track changes
    changes_made = []

    # Process brush section (simple brushes)
    if "brush" in data:
        for brand, brand_data in data["brush"].items():
            for model, patterns in brand_data.items():
                for i, pattern in enumerate(patterns):
                    if isinstance(pattern, dict):
                        # Dictionary with additional fields
                        pattern_string = list(pattern.keys())[0]
                        pattern_data = pattern[pattern_string]

                        if "user_intent" in pattern_data:
                            del pattern_data["user_intent"]
                            changes_made.append(f"Removed user_intent from: {pattern_string}")
                    else:
                        # Simple string pattern - no changes needed
                        pass

    # Save the cleaned file
    with open(correct_matches_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=False, allow_unicode=True)

    print(f"Cleaned up {len(changes_made)} simple brush entries")
    for change in changes_made:
        print(f"  - {change}")

    return changes_made


if __name__ == "__main__":
    cleanup_simple_brush_user_intent()
