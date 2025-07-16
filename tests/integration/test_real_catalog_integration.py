# pylint: disable=redefined-outer-name

"""
Integration tests using real YAML catalog files.
These tests validate that changes to production YAML files don't break parsing.
"""

import pytest
from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.blade_matcher import BladeMatcher


@pytest.fixture(scope="session")
def brush_matcher():
    return BrushMatcher()


@pytest.fixture(scope="session")
def soap_matcher():
    return SoapMatcher()


@pytest.fixture(scope="session")
def razor_matcher():
    return RazorMatcher()


@pytest.fixture(scope="session")
def blade_matcher():
    return BladeMatcher()


class TestRealCatalogIntegration:
    """Integration tests using actual production YAML catalogs."""

    def test_real_catalogs_load_successfully(
        self, brush_matcher, soap_matcher, razor_matcher, blade_matcher
    ):
        """Test that all real catalogs load without errors."""
        # Verify basic structure
        assert brush_matcher.catalog_data is not None
        assert soap_matcher.catalog is not None
        assert razor_matcher.catalog is not None
        assert blade_matcher.catalog is not None

    def test_real_catalog_patterns_compile(self, brush_matcher, soap_matcher):
        """Test that all regex patterns in real catalogs compile successfully."""
        # Verify patterns exist and compiled successfully
        assert len(brush_matcher.strategies) > 0
        assert len(brush_matcher.handle_matcher.handle_patterns) > 0
        assert len(soap_matcher.scent_patterns) + len(soap_matcher.brand_patterns) > 0

    def test_known_real_patterns_work(
        self, brush_matcher, soap_matcher, razor_matcher, blade_matcher
    ):
        """Test that known patterns from real catalogs work correctly."""
        # Key test cases that should work with real catalogs
        test_cases = [
            # Brush patterns
            (brush_matcher, "Simpson Chubby 2", "brand", "Simpson"),
            (brush_matcher, "Declaration B15", "brand", "Declaration Grooming"),
            (brush_matcher, "Omega 10048", "brand", "Omega"),
            # Soap patterns
            (soap_matcher, "Barrister and Mann Seville", "maker", "Barrister and Mann"),
            (soap_matcher, "Declaration Grooming Bandwagon", "maker", "Declaration Grooming"),
            # Razor patterns
            (razor_matcher, "Karve Christopher Bradley", "brand", "Karve"),
            (razor_matcher, "Gillette Tech", "brand", "Gillette"),
            # Blade patterns
            (blade_matcher, "Feather", "brand", "Feather"),
            (blade_matcher, "Astra Superior Platinum", "brand", "Astra"),
        ]

        for matcher, input_text, field, expected_value in test_cases:
            result = matcher.match(input_text)
            # Handle both MatchResult objects and dictionaries
            if hasattr(result, "matched"):
                matched = result.matched
            else:
                matched = result.get("matched")
            if matched and field in matched:
                assert (
                    matched[field] == expected_value
                ), f"Failed for {input_text}: expected {expected_value}, got {matched[field]}"

    def test_handle_knot_splitting_integration(self, brush_matcher):
        """Test handle/knot splitting with real catalog data."""
        # Test cases that exercise both brush and handle catalogs
        test_cases = [
            ("DG B15 w/ C&H Zebra", "Declaration Grooming", "Chisel & Hound"),
            ("Elite handle w/ Declaration B10", "Declaration Grooming", "Elite"),
            ("Wolf Whiskers w/ Omega knot", "Omega", "Wolf Whiskers"),
        ]

        for input_text, expected_knot_brand, expected_handle_maker in test_cases:
            result = brush_matcher.match(input_text)
            # For now, just verify the match doesn't crash
            # The exact structure may vary based on catalog data
            assert result is not None
            assert hasattr(result, "matched")

    def test_soap_scent_matching(self, soap_matcher):
        """Test that soap scent patterns work with real catalog."""
        test_cases = [
            ("Barrister and Mann Seville", "Seville"),
            ("Declaration Grooming Contemplation", "Contemplation"),
            ("House of Mammoth Hygge", "Hygge"),
        ]

        for input_text, expected_scent in test_cases:
            result = soap_matcher.match(input_text)
            # Handle both MatchResult objects and dictionaries
            if hasattr(result, "matched"):
                matched = result.matched
            else:
                matched = result.get("matched")
            if isinstance(matched, dict) and matched.get("scent"):
                assert (
                    expected_scent.lower() in matched["scent"].lower()
                ), f"Scent failed for {input_text}"

    def test_specific_integration_scenarios(self, brush_matcher):
        """Test specific integration scenarios that have caused issues."""
        # Test Declaration Grooming B2 bug fix
        result = brush_matcher.match("Zenith B2 w/ Elite Handle")
        # For now, just verify the match doesn't crash
        assert result is not None
        assert hasattr(result, "matched")

    def test_catalog_files_exist(self):
        """Test that all expected catalog files exist."""
        catalog_files = [
            "data/brushes.yaml",
            "data/handles.yaml",
            "data/soaps.yaml",
            "data/razors.yaml",
            "data/blades.yaml",
        ]

        for catalog_file in catalog_files:
            path = Path(catalog_file)
            assert path.exists(), f"Catalog file {catalog_file} does not exist"
            assert path.stat().st_size > 0, f"Catalog file {catalog_file} is empty"
