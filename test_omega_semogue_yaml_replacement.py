#!/usr/bin/env python3
"""
Test script to verify that the YAML approach can replicate the Omega/Semogue strategy functionality.
"""

import re


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

    # Mock catalog data instead of reading from production file
    mock_catalog_data = {
        "known_brushes": {
            "Omega": {
                "10049": {
                    "fiber": "Boar",
                    "knot_size_mm": 24,
                    "patterns": ["omega\\s*10049", "10049"],
                },
                "10005": {
                    "fiber": "Boar",
                    "knot_size_mm": 22,
                    "patterns": ["omega\\s*10005", "10005"],
                },
                "46206": {
                    "fiber": "Boar",
                    "knot_size_mm": 25,
                    "patterns": ["omega\\s*46206", "46206"],
                },
                "80005": {
                    "fiber": "Boar",
                    "knot_size_mm": 24,
                    "patterns": ["omega\\s*80005", "80005"],
                },
            },
            "Semogue": {
                "C3": {"fiber": "Boar", "knot_size_mm": 22, "patterns": ["semogue\\s*c3", "c3"]},
                "C1": {"fiber": "Boar", "knot_size_mm": 20, "patterns": ["semogue\\s*c1", "c1"]},
                "C5": {"fiber": "Boar", "knot_size_mm": 24, "patterns": ["semogue\\s*c5", "c5"]},
            },
        }
    }

    # Extract Omega and Semogue patterns
    omega_patterns = []
    semogue_patterns = []

    # Extract Omega patterns
    if "known_brushes" in mock_catalog_data and "Omega" in mock_catalog_data["known_brushes"]:
        omega_section = mock_catalog_data["known_brushes"]["Omega"]
        for model_name, model_data in omega_section.items():
            if isinstance(model_data, dict) and "patterns" in model_data:
                omega_patterns.extend(model_data["patterns"])

    # Extract Semogue patterns
    if "known_brushes" in mock_catalog_data and "Semogue" in mock_catalog_data["known_brushes"]:
        semogue_section = mock_catalog_data["known_brushes"]["Semogue"]
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
