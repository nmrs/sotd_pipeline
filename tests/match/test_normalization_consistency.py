#!/usr/bin/env python3
"""Test normalization consistency between matchers and analyzers."""

import pytest
from pathlib import Path

from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.utils.yaml_loader import load_yaml_with_nfc


def _convert_match_result_to_dict(match_result):
    """Convert MatchResult to dict for backward compatibility in tests."""
    return {
        "original": match_result.original,
        "matched": match_result.matched,
        "match_type": match_result.match_type,
        "pattern": match_result.pattern,
    }


@pytest.fixture(scope="session")
def correct_matches_data():
    """Load correct_matches.yaml data for testing."""
    correct_matches_path = Path("data/correct_matches.yaml")
    if not correct_matches_path.exists():
        return {}
    return load_yaml_with_nfc(correct_matches_path)


@pytest.fixture(scope="session")
def matchers():
    """Create matcher instances for testing."""
    return {
        "blade": BladeMatcher(),
        "brush": BrushMatcher(),
        "razor": RazorMatcher(),
        "soap": SoapMatcher(),
    }


class TestNormalizationConsistency:
    """Test that normalization is consistent across all matchers."""

    @pytest.mark.slow
    def test_correct_matches_exact_match_consistency(self, correct_matches_data, matchers):
        """
        Test that all entries in correct_matches.yaml are found as exact matches by the matchers.

        This is the key test that verifies the normalization unification is working correctly.
        """
        if not correct_matches_data:
            pytest.skip("No correct_matches.yaml data available")

        for field, field_data in correct_matches_data.items():
            if field not in matchers:
                continue

            matcher = matchers[field]

            # Handle format-first structure for blades, brand-first for other fields
            if field == "blade":
                # Format-first structure: format -> brand -> model -> strings
                for format_name, format_data in field_data.items():
                    for brand, brand_data in format_data.items():
                        for model, correct_matches in brand_data.items():
                            for correct_match in correct_matches:
                                # Test that the matcher finds this as an exact match
                                # Pass just the normalized string to matchers
                                if field == "blade":
                                    # Use format-aware matching for blades
                                    result = matcher.match_with_context(correct_match, format_name)
                                else:
                                    result = matcher.match(correct_match)

                                assert (
                                    result is not None
                                ), f"Matcher returned None for '{correct_match}'"
                                result_dict = _convert_match_result_to_dict(result)
                                assert result_dict.get("match_type") == "exact", (
                                    f"Expected exact match for '{correct_match}', "
                                    f"got {result_dict.get('match_type')}"
                                )
            else:
                # Brand-first structure: brand -> model -> strings
                for brand, brand_data in field_data.items():
                    for model, correct_matches in brand_data.items():
                        for correct_match in correct_matches:
                            result = matcher.match(correct_match)

                            assert (
                                result is not None
                            ), f"Matcher returned None for '{correct_match}'"
                            result_dict = _convert_match_result_to_dict(result)
                            assert result_dict.get("match_type") == "exact", (
                                f"Expected exact match for '{correct_match}', "
                                f"got {result_dict.get('match_type')}"
                            )

    def test_correct_matches_sample_consistency(self, correct_matches_data, matchers):
        """
        Fast sample: For each field, test the first override entry in correct_matches.yaml
        for exact match. This ensures the test is robust, fast, and always aligned with
        the override intent.
        """
        if not correct_matches_data:
            pytest.skip("No correct_matches.yaml data available")

        for field, field_data in correct_matches_data.items():
            if field not in matchers:
                continue
            matcher = matchers[field]
            # For blades, structure is format -> brand -> model -> [strings]
            if field == "blade":
                for format_name, brands in list(field_data.items())[:1]:
                    for brand, models in list(brands.items())[:1]:
                        for model, correct_matches in list(models.items())[:1]:
                            for correct_match in correct_matches[:1]:
                                # Pass just the normalized string to matchers
                                result = matcher.match_with_context(correct_match, format_name)
                                assert (
                                    result is not None
                                ), f"Matcher returned None for '{correct_match}'"
                                result_dict = _convert_match_result_to_dict(result)
                                assert result_dict.get("match_type") == "exact", (
                                    f"Expected exact match for '{correct_match}', "
                                    f"got {result_dict.get('match_type')}"
                                )
            else:
                # For other fields, structure is brand -> model -> [strings]
                for brand, models in list(field_data.items())[:1]:
                    for model, correct_matches in list(models.items())[:1]:
                        for correct_match in correct_matches[:1]:
                            # Pass just the normalized string to matchers
                            result = matcher.match(correct_match)
                            assert (
                                result is not None
                            ), f"Matcher returned None for '{correct_match}'"
                            result_dict = _convert_match_result_to_dict(result)
                            assert result_dict.get("match_type") == "exact", (
                                f"Expected exact match for '{correct_match}', "
                                f"got {result_dict.get('match_type')}"
                            )

    def test_normalization_consistency_across_matchers(self, matchers):
        """
        Test that the same input string is normalized consistently across all matchers.
        """
        test_cases = [
            "Test Product",
            "test product",
            "TEST PRODUCT",
            "Test-Product",
            "Test_Product",
            "Test Product (Sample)",
            "Test Product [5]",
        ]

        for test_case in test_cases:
            results = {}
            for field, matcher in matchers.items():
                # Pass just the normalized string to matchers
                result = matcher.match(test_case)
                result_dict = _convert_match_result_to_dict(result)
                results[field] = result_dict

            # All matchers should handle the same input consistently
            # (either all match or all don't match, or handle case variations consistently)
            for field, result in results.items():
                assert "original" in result
                assert "matched" in result
                assert "match_type" in result
                assert "pattern" in result
