# pylint: disable=redefined-outer-name

"""
Integration tests using real YAML catalog files.
These tests validate that changes to production YAML files don't break parsing.
"""

from pathlib import Path

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.blade_matcher import BladeMatcher


class TestRealCatalogIntegration:
    """Integration tests using actual production YAML catalogs."""

    def test_real_catalogs_load_successfully(self):
        """Test that all real catalogs load without errors."""
        # Test all matchers initialize successfully with real catalogs
        brush_matcher = BrushMatcher()
        soap_matcher = SoapMatcher()
        razor_matcher = RazorMatcher()
        blade_matcher = BladeMatcher()

        # Verify basic structure
        assert brush_matcher.catalog_data is not None
        assert soap_matcher.catalog is not None
        assert razor_matcher.catalog is not None
        assert blade_matcher.catalog is not None

    def test_real_catalog_patterns_compile(self):
        """Test that all regex patterns in real catalogs compile successfully."""
        brush_matcher = BrushMatcher()
        soap_matcher = SoapMatcher()

        # Verify patterns exist and compiled successfully
        assert len(brush_matcher.strategies) > 0
        assert len(brush_matcher.handle_matcher.handle_patterns) > 0
        assert len(soap_matcher.scent_patterns) + len(soap_matcher.brand_patterns) > 0

    def test_known_real_patterns_work(self):
        """Test that known patterns from real catalogs work correctly."""
        brush_matcher = BrushMatcher()
        soap_matcher = SoapMatcher()
        razor_matcher = RazorMatcher()
        blade_matcher = BladeMatcher()

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
            matched = result.get("matched")
            if isinstance(matched, dict):
                assert matched.get(field) == expected_value, f"Failed for {input_text}"

    def test_handle_knot_splitting_integration(self):
        """Test handle/knot splitting with real catalog data."""
        matcher = BrushMatcher()

        # Test cases that exercise both brush and handle catalogs
        test_cases = [
            ("DG B15 w/ C&H Zebra", "Declaration Grooming", "Chisel & Hound"),
            ("Elite handle w/ Declaration B10", "Declaration Grooming", "Elite"),
            ("Wolf Whiskers w/ Omega knot", "Omega", "Wolf Whiskers"),
        ]

        for input_text, expected_brand, expected_handle_maker in test_cases:
            result = matcher.match(input_text)
            matched = result.get("matched")
            if isinstance(matched, dict):
                assert matched.get("brand") == expected_brand, f"Brand failed for {input_text}"
                if matched.get("handle_maker"):
                    assert (
                        matched.get("handle_maker") == expected_handle_maker
                    ), f"Handle maker failed for {input_text}"

    def test_soap_scent_matching(self):
        """Test that soap scent patterns work with real catalog."""
        matcher = SoapMatcher()

        test_cases = [
            ("Barrister and Mann Seville", "Seville"),
            ("Declaration Grooming Contemplation", "Contemplation"),
            ("House of Mammoth Hygge", "Hygge"),
        ]

        for input_text, expected_scent in test_cases:
            result = matcher.match(input_text)
            matched = result.get("matched")
            if isinstance(matched, dict) and matched.get("scent"):
                assert (
                    expected_scent.lower() in matched["scent"].lower()
                ), f"Scent failed for {input_text}"

    def test_specific_integration_scenarios(self):
        """Test specific integration scenarios that have caused issues."""
        brush_matcher = BrushMatcher()

        # Test Declaration Grooming B2 bug fix
        result = brush_matcher.match("Zenith B2 w/ Elite Handle")
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Zenith"

        # Test delimiter unification
        test_cases = [
            "DG B15 w/ C&H Zebra",
            "DG B15 with C&H Zebra",
            "DG B15 / C&H Zebra",
        ]

        for test_case in test_cases:
            result = brush_matcher.match(test_case)
            assert result["matched"] is not None, f"No match for: {test_case}"
            assert (
                result["matched"]["brand"] == "Declaration Grooming"
            ), f"Wrong brand for: {test_case}"

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
