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


class TestRealCatalogIntegration:
    """Integration tests using actual production YAML catalogs."""

    def test_real_brush_catalog_loads_successfully(self):
        """Test that real brush catalog loads without errors."""
        matcher = BrushMatcher()  # Uses default paths to real files

        # Should not raise exceptions during initialization
        assert matcher.catalog_data is not None
        assert matcher.handles_data is not None
        assert len(matcher.strategies) > 0

    def test_real_soap_catalog_loads_successfully(self):
        """Test that real soap catalog loads without errors."""
        matcher = SoapMatcher()  # Uses default path to real file

        # Should not raise exceptions during initialization
        assert matcher.catalog is not None
        assert len(matcher.scent_patterns) + len(matcher.brand_patterns) > 0

    def test_real_razor_catalog_loads_successfully(self):
        """Test that real razor catalog loads without errors."""
        matcher = RazorMatcher()  # Uses default path to real file

        # Should not raise exceptions during initialization
        assert matcher.catalog is not None

    def test_real_blade_catalog_loads_successfully(self):
        """Test that real blade catalog loads without errors."""
        matcher = BladeMatcher()  # Uses default path to real file

        # Should not raise exceptions during initialization
        assert matcher.catalog is not None

    def test_known_real_brush_patterns_work(self):
        """Test that known brush patterns from real catalog work correctly."""
        matcher = BrushMatcher()

        # Test cases that should definitely work with real catalog
        test_cases = [
            ("Simpson Chubby 2", "Simpson"),
            ("Declaration B15", "Declaration Grooming"),
            ("Omega 10048", "Omega"),
            ("Chisel & Hound V20", "Chisel & Hound"),
        ]

        for input_text, expected_brand in test_cases:
            result = matcher.match(input_text)
            if result.get("matched"):  # Only assert if we get a match
                matched = result["matched"]
                assert matched["brand"] == expected_brand, f"Failed for {input_text}"
                # Model matching may be flexible, so just check it's not None
                assert matched.get("model") is not None, f"No model for {input_text}"

    def test_real_handle_knot_splitting_integration(self):
        """Test handle/knot splitting with real catalog data."""
        matcher = BrushMatcher()

        # Test cases that exercise both brush and handle catalogs
        test_cases = [
            "DG B15 w/ C&H Zebra",
            "Elite handle w/ Declaration B10",
            "Wolf Whiskers w/ Omega knot",
        ]

        for test_case in test_cases:
            result = matcher.match(test_case)
            # Should not crash and should provide some meaningful result
            assert "original" in result
            assert "matched" in result
            assert "match_type" in result
            assert "pattern" in result

    def test_known_real_brush_handle_makers_work(self):
        """Test that brush handle maker patterns from real catalog work correctly."""
        matcher = BrushMatcher()

        # Test cases that should identify specific handle makers
        test_cases = [
            ("DG B15 w/ Elite Zebra", "Elite"),
            ("Declaration B10 w/ Wolf Whiskers handle", "Wolf Whiskers"),
            ("Zenith B2 w/ Chisel & Hound", "Chisel & Hound"),
            ("Simpson handle", "Simpson"),
            ("Paladin custom handle", "Paladin"),
        ]

        for input_text, expected_handle_maker in test_cases:
            result = matcher.match(input_text)
            if result.get("matched") and result["matched"].get("handle_maker"):
                matched = result["matched"]
                actual_handle_maker = matched.get("handle_maker")
                assert actual_handle_maker == expected_handle_maker, (
                    f"Handle maker failed for '{input_text}' - got '{actual_handle_maker}', "
                    f"expected '{expected_handle_maker}'"
                )

    def test_known_real_soap_patterns_work(self):
        """Test that known soap patterns from real catalog work correctly."""
        matcher = SoapMatcher()

        # Test cases based on common brands in real catalog
        test_cases = [
            ("Barrister and Mann Seville", "Barrister and Mann"),
            ("Declaration Grooming Bandwagon", "Declaration Grooming"),
            ("House of Mammoth Hygge", "House of Mammoth"),
            ("Stirling Soap Co Executive Man", "Stirling Soap Co."),
        ]

        for input_text, expected_brand in test_cases:
            result = matcher.match(input_text)
            if result.get("matched"):  # Only assert if we get a match
                matched = result["matched"]
                assert matched["maker"] == expected_brand, f"Failed for {input_text}"

    def test_known_real_soap_scents_work(self):
        """Test that known soap scent patterns from real catalog work correctly."""
        matcher = SoapMatcher()

        # Test cases that should match specific scents, not just makers
        test_cases = [
            ("Barrister and Mann Seville", "Barrister and Mann", "Seville"),
            ("Declaration Grooming Contemplation", "Declaration Grooming", "Contemplation"),
            ("House of Mammoth Hygge", "House of Mammoth", "Hygge"),
            ("Stirling Executive Man", "Stirling Soap Co.", "Executive Man"),
            ("B&M Reserve Fern", "Barrister and Mann", "Fern"),
        ]

        for input_text, expected_maker, expected_scent in test_cases:
            result = matcher.match(input_text)
            if result.get("matched"):  # Only assert if we get a match
                matched = result["matched"]
                assert matched["maker"] == expected_maker, f"Maker failed for {input_text}"
                # Scent matching should be specific
                if matched.get("scent"):
                    assert (
                        expected_scent.lower() in matched["scent"].lower()
                    ), f"Scent failed for {input_text}"

    def test_known_real_razor_patterns_work(self):
        """Test that known razor patterns from real catalog work correctly."""
        matcher = RazorMatcher()

        # Test cases based on common razors in real catalog
        test_cases = [
            ("Karve Christopher Bradley", "Karve"),
            ("Gillette Tech", "Gillette"),
            ("Merkur 34C", "Merkur"),
            ("Blackland Blackbird", "Blackland"),
        ]

        for input_text, expected_brand in test_cases:
            result = matcher.match(input_text)
            if result.get("matched"):  # Only assert if we get a match
                matched = result["matched"]
                assert matched["brand"] == expected_brand, f"Failed for {input_text}"
                assert matched.get("model") is not None, f"No model for {input_text}"

    def test_known_real_blade_patterns_work(self):
        """Test that known blade patterns from real catalog work correctly."""
        matcher = BladeMatcher()

        # Test cases based on common blades in real catalog
        test_cases = [
            ("Feather", "Feather"),
            ("Astra Superior Platinum", "Astra"),
            ("Gillette Silver Blue", "Gillette"),
            ("Personna Lab Blue", "Personna"),
        ]

        for input_text, expected_brand in test_cases:
            result = matcher.match(input_text)
            if result.get("matched"):  # Only assert if we get a match
                matched = result["matched"]
                assert matched["brand"] == expected_brand, f"Failed for {input_text}"

    def test_real_catalog_regex_patterns_compile(self):
        """Test that all regex patterns in real catalogs compile successfully."""
        # This test will catch malformed regex patterns in production catalogs

        # Brush patterns
        brush_matcher = BrushMatcher()
        assert len(brush_matcher.strategies) > 0

        # Handle patterns
        assert len(brush_matcher.handle_patterns) > 0
        for pattern_info in brush_matcher.handle_patterns:
            assert pattern_info["regex"] is not None  # Should have compiled successfully

        # Soap patterns
        soap_matcher = SoapMatcher()
        assert len(soap_matcher.scent_patterns) + len(soap_matcher.brand_patterns) > 0
        for pattern_info in soap_matcher.scent_patterns + soap_matcher.brand_patterns:
            assert pattern_info["regex"] is not None  # Should have compiled successfully

    def test_declaration_grooming_b2_integration(self):
        """Test that the Declaration Grooming B2 bug fix works with real catalogs."""
        brush_matcher = BrushMatcher()

        # This should match as "Zenith B2", not "Declaration Grooming B2"
        result = brush_matcher.match("Zenith B2 w/ Elite Handle")
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Zenith"
        # The Zenith strategy preserves the full model including the brand prefix
        assert result["matched"]["model"] == "B2"

        # Test standalone B2 - should default to Declaration Grooming
        result = brush_matcher.match("B2 w/ Elite Handle")
        assert result["matched"] is not None
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B2"

    def test_delimiter_unification_option1(self):
        """Test that Option 1 delimiter unification works - all non-handle-primary delimiters use smart analysis."""
        brush_matcher = BrushMatcher()

        # These should all behave the same now (using smart analysis)
        test_cases = [
            "DG B15 w/ C&H Zebra",
            "DG B15 with C&H Zebra",
            "DG B15 / C&H Zebra",
            "DG B15 - C&H Zebra",
        ]

        for test_case in test_cases:
            result = brush_matcher.match(test_case)

            # Should match Declaration Grooming B15 as the knot
            assert result["matched"] is not None, f"No match for: {test_case}"
            assert (
                result["matched"]["brand"] == "Declaration Grooming"
            ), f"Wrong brand for: {test_case}"
            assert result["matched"]["model"] == "B15", f"Wrong model for: {test_case}"

            # Should detect Chisel & Hound as handle maker
            assert (
                result["matched"]["handle_maker"] == "Chisel & Hound"
            ), f"Wrong handle maker for: {test_case}"

    def test_real_catalog_files_exist(self):
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
