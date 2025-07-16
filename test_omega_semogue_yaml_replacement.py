#!/usr/bin/env python3
"""
Test script to verify that the YAML approach can replicate the Omega/Semogue strategy functionality.
"""

import re
from pathlib import Path

import yaml


def test_omega_semogue_yaml_coverage():
    """Test that the YAML approach covers the same cases as the Omega/Semogue strategy."""

    # Test cases that the strategy would match
    test_cases = [
        # Omega cases
        "omega 10049",
        "omega 10005",
        "omega 46206",
        "omega 80005",
        "10049",  # Just the model number
        "10005",
        # Semogue cases
        "semogue c3",
        "semogue c1",
        "semogue c5",
        "c3",  # Just the model
        "c1",
        "c5",
        # Edge cases
        "omega 123",  # 3 digits
        "omega 12345",  # 5 digits
        "omega 123456",  # 6 digits
        "semogue c10",  # C with 2 digits
        "semogue c100",  # C with 3 digits
    ]

    # Load the generated YAML to check patterns
    yaml_file = Path("data/brushes.post.yaml")
    if not yaml_file.exists():
        print("❌ brushes.post.yaml not found. Run the preprocessor first.")
        return

    with open(yaml_file, "r") as f:
        catalog_data = yaml.safe_load(f)

    # Extract Omega and Semogue patterns
    omega_patterns = []
    semogue_patterns = []

    # Extract Omega patterns
    if "known_brushes" in catalog_data and "Omega" in catalog_data["known_brushes"]:
        omega_section = catalog_data["known_brushes"]["Omega"]
        for model_name, model_data in omega_section.items():
            if isinstance(model_data, dict) and "patterns" in model_data:
                omega_patterns.extend(model_data["patterns"])

    # Extract Semogue patterns
    if "known_brushes" in catalog_data and "Semogue" in catalog_data["known_brushes"]:
        semogue_section = catalog_data["known_brushes"]["Semogue"]
        for model_name, model_data in semogue_section.items():
            if isinstance(model_data, dict) and "patterns" in model_data:
                semogue_patterns.extend(model_data["patterns"])

    print(f"Found {len(omega_patterns)} Omega patterns")
    print(f"Found {len(semogue_patterns)} Semogue patterns")

    # Test each case
    print("\nTesting cases:")
    for case in test_cases:
        matched = False

        # Test Omega patterns
        for pattern in omega_patterns:
            if re.search(pattern, case, re.IGNORECASE):
                print(f"✅ {case} -> Omega (pattern: {pattern})")
                matched = True
                break

        # Test Semogue patterns
        if not matched:
            for pattern in semogue_patterns:
                if re.search(pattern, case, re.IGNORECASE):
                    print(f"✅ {case} -> Semogue (pattern: {pattern})")
                    matched = True
                    break

        if not matched:
            print(f"❌ {case} -> No match")

    matched_count = len([c for c in test_cases if "✅" in str(c)])
    print(f"\nSummary: {matched_count}/{len(test_cases)} cases matched")


if __name__ == "__main__":
    test_omega_semogue_yaml_coverage()
