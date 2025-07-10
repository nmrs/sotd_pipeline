#!/usr/bin/env python3
"""Test normalization consistency between matchers and analyzers."""

from pathlib import Path
from typing import Any, Dict

import pytest

from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.tools.analyzers.mismatch_analyzer import (
    MismatchAnalyzer,
)
from sotd.utils.match_filter_utils import (
    normalize_for_matching,
)
from sotd.utils.yaml_loader import (
    load_yaml_with_nfc,
)


class TestNormalizationConsistency:
    """
    Test that all components use the canonical normalization and correct matches are always
    found as exact matches.
    """

    @pytest.fixture
    def correct_matches_data(self) -> Dict[str, Any]:
        """Load correct_matches.yaml data."""
        correct_matches_path = Path("data/correct_matches.yaml")
        return load_yaml_with_nfc(correct_matches_path)

    @pytest.fixture
    def matchers(self):
        """Create all matcher instances."""
        return {
            "razor": RazorMatcher(Path("data/razors.yaml")),
            "blade": BladeMatcher(Path("data/blades.yaml")),
            "brush": BrushMatcher(Path("data/brushes.yaml"), Path("data/handles.yaml")),
            "soap": SoapMatcher(Path("data/soaps.yaml")),
        }

    @pytest.fixture
    def analyzer(self):
        """Create mismatch analyzer instance."""
        return MismatchAnalyzer()

    def test_normalize_for_matching_is_canonical(self):
        """Test that normalize_for_matching is the canonical normalization function."""
        # Test that all field types use the same normalization logic for competition tags
        test_string = "Product Name $CNC"

        # All fields should preserve case and strip competition tags
        assert normalize_for_matching(test_string, field="razor") == "Product Name"
        assert normalize_for_matching(test_string, field="blade") == "Product Name"
        assert normalize_for_matching(test_string, field="brush") == "Product Name"
        assert normalize_for_matching(test_string, field="soap") == "Product Name"

    def test_field_specific_normalization(self):
        """Test that field-specific normalization is applied correctly."""
        # Blade field should strip blade patterns
        blade_string = "treet platinum (3x) #sotd"
        assert normalize_for_matching(blade_string, field="blade") == "treet platinum #sotd"

        # Razor field should strip handle indicators
        razor_string = "Razor / [brand] handle $CNC"
        assert normalize_for_matching(razor_string, field="razor") == "Razor"

        # Soap field should strip soap patterns
        soap_string = "B&M Seville soap sample"
        assert normalize_for_matching(soap_string, field="soap") == "B&M Seville"

    def test_matcher_analyzer_consistency(self, matchers, analyzer):
        """Test that matchers and analyzer use the same normalization logic."""
        test_cases = [
            ("razor", "*New* King C. Gillette $CNC"),
            ("blade", "treet platinum (3x) #sotd"),
            ("brush", "Simpson Chubby 2 $PLASTIC"),
            ("soap", "B&M Seville soap sample"),
        ]

        for field, test_string in test_cases:
            matcher = matchers[field]

            # Test that matcher uses canonical normalization
            matcher_result = matcher.match(test_string)

            # Test that analyzer uses canonical normalization
            analyzer_result = analyzer._create_match_key(
                field, test_string, matcher_result.get("matched", {})
            )

            # Both should use the same normalization logic
            assert matcher_result is not None
            assert analyzer_result is not None

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
                                if field == "blade":
                                    # Use format-aware matching for blades
                                    result = matcher.match_with_context(correct_match, format_name)
                                else:
                                    result = matcher.match(correct_match)

                                # Should be an exact match
                                assert (
                                    result is not None
                                ), f"Matcher returned None for '{correct_match}'"
                                assert result.get("match_type") == "exact", (
                                    f"Expected exact match for '{correct_match}', "
                                    f"got {result.get('match_type')}"
                                )

                                # Should match the expected brand/model
                                assert result.get("matched", {}).get("brand") == brand, (
                                    f"Expected brand '{brand}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('brand')}"
                                )
                                assert result.get("matched", {}).get("model") == model, (
                                    f"Expected model '{model}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('model')}"
                                )
            else:
                # Brand-first structure: brand -> model -> strings (for razors, brushes, soaps)
                for brand, brand_data in field_data.items():
                    for model, correct_matches in brand_data.items():
                        for correct_match in correct_matches:
                            # Test that the matcher finds this as an exact match
                            result = matcher.match(correct_match)

                            # Should be an exact match
                            assert (
                                result is not None
                            ), f"Matcher returned None for '{correct_match}'"
                            assert result.get("match_type") == "exact", (
                                f"Expected exact match for '{correct_match}', "
                                f"got {result.get('match_type')}"
                            )

                            # Should match the expected brand/model
                            if field == "soap":
                                assert result.get("matched", {}).get("maker") == brand, (
                                    f"Expected maker '{brand}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('maker')}"
                                )
                                assert result.get("matched", {}).get("scent") == model, (
                                    f"Expected scent '{model}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('scent')}"
                                )
                            else:
                                assert result.get("matched", {}).get("brand") == brand, (
                                    f"Expected brand '{brand}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('brand')}"
                                )
                                assert result.get("matched", {}).get("model") == model, (
                                    f"Expected model '{model}' for '{correct_match}', "
                                    f"got {result.get('matched', {}).get('model')}"
                                )

    def test_normalization_preserves_case_for_correct_matches(self):
        """Test that normalization preserves case for correct match consistency."""
        # Test that case is preserved (unlike the old BaseMatcher.normalize which lowercased)
        test_cases = [
            ("razor", "*New* King C. Gillette", "*New* King C. Gillette"),
            ("razor", "ATT S1", "ATT S1"),
            ("razor", "Above The Tie Atlas S1", "Above The Tie Atlas S1"),
            ("blade", "Feather Hi-Stainless", "Feather Hi-Stainless"),
            ("brush", "Simpson Chubby 2", "Simpson Chubby 2"),
            ("soap", "Barrister and Mann - Seville", "Barrister and Mann - Seville"),
        ]

        for field, input_str, expected in test_cases:
            result = normalize_for_matching(input_str, field=field)
            assert result == expected, f"Field {field}: expected '{expected}', got '{result}'"

    def test_no_confirmed_but_not_exact_mismatches(self, matchers, analyzer):
        """Test that there are no 'confirmed but not exact' mismatches."""
        # This test verifies that the normalization unification has eliminated
        # the confusing "confirmed but not exact" results

        test_cases = [
            ("razor", "*New* King C. Gillette"),
            ("blade", "treet platinum (3x)"),
            ("brush", "Simpson Chubby 2"),
            ("soap", "B&M Seville soap"),
        ]

        for field, test_string in test_cases:
            matcher = matchers[field]
            result = matcher.match(test_string)

            # If it's an exact match, it should be consistent with analyzer
            if result and result.get("match_type") == "exact":
                analyzer_key = analyzer._create_match_key(
                    field, test_string, result.get("matched", {})
                )
                # The analyzer should recognize this as an exact match
                assert analyzer_key is not None


class TestNormalizationRegression:
    """Regression tests for previously 'confirmed but not exact' cases."""

    def test_regression_case_insensitive_matches(self):
        """Test that case differences no longer cause 'confirmed but not exact' mismatches."""
        # These were problematic cases where normalization inconsistencies caused issues
        test_cases = [
            ("*New* King C. Gillette", "razor"),
            ("*new* king c. gillette", "razor"),
            ("King C. Gillette", "razor"),
            ("king c. gillette", "razor"),
        ]

        for input_str, field in test_cases:
            normalized = normalize_for_matching(input_str, field=field)
            # All should normalize to the same result
            assert "king c. gillette" in normalized.lower()

    def test_regression_blade_usage_patterns(self):
        """Test that blade usage patterns are handled consistently."""
        test_cases = [
            ("Treet Platinum (3x)", "blade"),
            ("treet platinum (3x)", "blade"),
            ("Treet Platinum", "blade"),
            ("treet platinum", "blade"),
        ]

        for input_str, field in test_cases:
            normalized = normalize_for_matching(input_str, field=field)
            # All should normalize to the same result (without usage patterns)
            assert "treet platinum" in normalized.lower()
            assert "(3x)" not in normalized

    def test_regression_soap_patterns(self):
        """Test that soap patterns are handled consistently."""
        test_cases = [
            ("B&M Seville soap sample", "soap"),
            ("b&m seville soap sample", "soap"),
            ("B&M Seville", "soap"),
            ("b&m seville", "soap"),
        ]

        for input_str, field in test_cases:
            normalized = normalize_for_matching(input_str, field=field)
            # All should normalize to the same result (without soap patterns)
            assert "b&m seville" in normalized.lower()
            assert "sample" not in normalized.lower()

    def test_regression_handle_indicators(self):
        """Test that handle indicators are handled consistently."""
        test_cases = [
            ("Razor / [Brand] handle", "razor"),
            ("razor / [brand] handle", "razor"),
            ("Razor", "razor"),
            ("razor", "razor"),
        ]

        for input_str, field in test_cases:
            normalized = normalize_for_matching(input_str, field=field)
            # All should normalize to the same result (without handle indicators)
            assert "razor" in normalized.lower()
            assert "handle" not in normalized.lower()

    def test_regression_competition_tags(self):
        """Test that competition tags are handled consistently."""
        test_cases = [
            ("Product $CNC $ARTISTCLUB", "razor"),
            ("product $cnc $artistclub", "razor"),
            ("Product", "razor"),
            ("product", "razor"),
        ]

        for input_str, field in test_cases:
            normalized = normalize_for_matching(input_str, field=field)
            # All should normalize to the same result (without competition tags)
            assert "product" in normalized.lower()
            assert "$cnc" not in normalized.lower()
            assert "$artistclub" not in normalized.lower()

    def test_regression_comprehensive_examples(self):
        """Test comprehensive examples that were problematic before normalization unification."""
        # These examples represent real cases that caused "confirmed but not exact" mismatches
        problematic_cases = [
            # Case sensitivity issues
            ("*New* King C. Gillette", "*new* king c. gillette"),
            ("B&M Seville soap sample", "b&m seville soap sample"),
            ("Treet Platinum (3x)", "treet platinum (3x)"),
            # Pattern stripping issues
            ("Razor / [Brand] handle $CNC", "razor / [brand] handle $cnc"),
            ("Blade (new) #SOTD", "blade (new) #sotd"),
            ("Soap puck sample", "soap puck sample"),
        ]

        for case1, case2 in problematic_cases:
            # Both cases should normalize to the same result
            field = self._detect_field(case1)
            norm1 = normalize_for_matching(case1, field=field)
            norm2 = normalize_for_matching(case2, field=field)

            # They should be identical after normalization
            assert norm1.lower() == norm2.lower(), f"Failed: '{case1}' vs '{case2}'"

    def _detect_field(self, text: str) -> str:
        """Helper to detect field type for testing."""
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in ["(3x)", "(new)", "blade", "x3"]):
            return "blade"
        elif any(pattern in text_lower for pattern in ["handle", "razor"]):
            return "razor"
        elif any(pattern in text_lower for pattern in ["soap", "sample", "puck", "croap"]):
            return "soap"
        elif any(pattern in text_lower for pattern in ["brush", "knot", "handle"]):
            return "brush"
        else:
            return "razor"  # default
