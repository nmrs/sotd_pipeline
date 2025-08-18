#!/usr/bin/env python3
"""Tests for extract normalization utility functions."""

from sotd.utils.extract_normalization import (
    normalize_for_matching,
    strip_blade_count_patterns,
    strip_handle_indicators,
    strip_razor_use_counts,
    strip_soap_patterns,
    strip_trailing_periods,
)


class TestStripBladeCountPatterns:
    """Test blade count pattern stripping."""

    def test_strip_blade_count_patterns_basic(self):
        """Test basic blade count pattern stripping."""
        test_cases = [
            ("Astra Superior Platinum (5)", "Astra Superior Platinum"),
            ("Feather Hi-Stainless (10)", "Feather Hi-Stainless"),
            ("Gillette Silver Blue (15)", "Gillette Silver Blue"),
            ("Personna Platinum (20)", "Personna Platinum"),
        ]
        for input_str, expected in test_cases:
            result = strip_blade_count_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_blade_count_patterns_with_brackets(self):
        """Test blade count pattern stripping with bracket notation."""
        test_cases = [
            ("Astra Superior Platinum [5]", "Astra Superior Platinum"),
            ("Feather Hi-Stainless [10]", "Feather Hi-Stainless"),
            ("Gillette Silver Blue [15]", "Gillette Silver Blue"),
        ]
        for input_str, expected in test_cases:
            result = strip_blade_count_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_blade_count_patterns_no_match(self):
        """Test strings that don't contain blade count patterns."""
        test_cases = [
            "Astra Superior Platinum",
            "Feather Hi-Stainless",
            "Gillette Silver Blue",
            "Blade without count",
        ]
        for input_str in test_cases:
            result = strip_blade_count_patterns(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_blade_count_patterns_edge_cases(self):
        """Test blade count pattern stripping with edge cases."""
        # Empty string
        assert strip_blade_count_patterns("") == ""

        # None input
        assert strip_blade_count_patterns(None) is None  # type: ignore

        # Only count pattern
        assert strip_blade_count_patterns("(5)") == ""
        assert strip_blade_count_patterns("[10]") == ""

        # Multiple count patterns
        assert strip_blade_count_patterns("Astra (5) (10)") == "Astra"


class TestStripHandleIndicators:
    """Test handle indicator stripping."""

    def test_strip_handle_indicators_basic(self):
        """Test basic handle indicator stripping."""
        test_cases = [
            ("Karve Overlander (in handle)", "Karve Overlander"),
            ("Gillette New (in handle)", "Gillette New"),
            ("Merkur 34C (in handle)", "Merkur 34C"),
        ]
        for input_str, expected in test_cases:
            result = strip_handle_indicators(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_handle_indicators_no_match(self):
        """Test strings that don't contain handle indicators."""
        test_cases = [
            "Karve Overlander",
            "Gillette New",
            "Merkur 34C",
            "Razor without handle info",
        ]
        for input_str in test_cases:
            result = strip_handle_indicators(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_handle_indicators_edge_cases(self):
        """Test handle indicator stripping with edge cases."""
        # Empty string
        assert strip_handle_indicators("") == ""

        # None input
        assert strip_handle_indicators(None) is None  # type: ignore

        # Only handle indicator
        assert strip_handle_indicators("(in handle)") == ""


class TestStripTrailingPeriods:
    """Test trailing period stripping."""

    def test_strip_trailing_periods_basic(self):
        """Test basic trailing period stripping."""
        test_cases = [
            ("Stirling Bay Rum.", "Stirling Bay Rum"),
            ("B&M Seville.", "B&M Seville"),
            ("Declaration Grooming.", "Declaration Grooming"),
            ("Tabac.", "Tabac"),
        ]
        for input_str, expected in test_cases:
            result = strip_trailing_periods(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_trailing_periods_multiple(self):
        """Test stripping multiple trailing periods."""
        test_cases = [
            ("Stirling Bay Rum...", "Stirling Bay Rum"),
            ("B&M Seville..", "B&M Seville"),
            ("Declaration Grooming....", "Declaration Grooming"),
        ]
        for input_str, expected in test_cases:
            result = strip_trailing_periods(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_trailing_periods_no_match(self):
        """Test strings that don't end with periods."""
        test_cases = [
            "Stirling Bay Rum",
            "B&M Seville",
            "Declaration Grooming",
            "Tabac",
        ]
        for input_str in test_cases:
            result = strip_trailing_periods(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_trailing_periods_edge_cases(self):
        """Test trailing period stripping with edge cases."""
        # Empty string
        assert strip_trailing_periods("") == ""

        # None input
        assert strip_trailing_periods(None) is None  # type: ignore

        # Only periods
        assert strip_trailing_periods(".") == ""
        assert strip_trailing_periods("...") == ""

        # Periods in middle
        assert strip_trailing_periods("Stirling.Bay.Rum") == "Stirling.Bay.Rum"


class TestNormalizeForMatching:
    """Test normalize_for_matching function."""

    def test_normalize_for_matching_soap_patterns(self):
        """Test that normalize_for_matching strips soap patterns for soap field."""
        # Test soap-related patterns
        assert normalize_for_matching("B&M Seville soap", field="soap") == "B&M Seville"
        assert normalize_for_matching("Stirling Bay Rum sample", field="soap") == "Stirling Bay Rum"
        assert (
            normalize_for_matching("Declaration Grooming (sample)", field="soap")
            == "Declaration Grooming"
        )

    def test_normalize_for_matching_soap_no_patterns(self):
        """Test that normalize_for_matching doesn't affect soaps without patterns."""
        test_cases = [
            ("B&M Seville", "B&M Seville"),
            ("Stirling Bay Rum", "Stirling Bay Rum"),
        ]
        for input_str, expected in test_cases:
            result = normalize_for_matching(input_str, field="soap")
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"


class TestStripSoapPatterns:
    """Test soap pattern stripping."""

    def test_strip_soap_patterns_basic(self):
        """Test basic soap pattern stripping."""
        test_cases = [
            ("B&M Seville soap", "B&M Seville"),  # "soap" is stripped
            ("Stirling Bay Rum sample", "Stirling Bay Rum"),  # "sample" is stripped
            ("Declaration Grooming soap sample", "Declaration Grooming"),  # Both stripped
            ("Cella croap", "Cella"),  # "croap" is stripped
            ("Proraso cream", "Proraso"),  # "cream" is stripped
            ("MWF puck", "MWF"),  # "puck" is stripped
            ("Arko shaving soap", "Arko"),  # "shaving soap" is stripped
            ("Tabac shaving cream", "Tabac"),  # "shaving cream" is stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_with_use_counts(self):
        """Test soap pattern stripping with use counts."""
        test_cases = [
            ("B&M Seville (23)", "B&M Seville (23)"),  # Use counts not stripped
            ("Stirling Bay Rum (5)", "Stirling Bay Rum (5)"),  # Use counts not stripped
            ("Declaration Grooming ()", "Declaration Grooming ()"),  # Empty parens not stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_with_sample_markers(self):
        """Test soap pattern stripping with sample markers."""
        test_cases = [
            ("B&M Seville (sample)", "B&M Seville (sample)"),  # Parenthetical not stripped
            ("Stirling Bay Rum (SAMPLE)", "Stirling Bay Rum (SAMPLE)"),  # Parenthetical not stripped
            ("Declaration Grooming ( Sample )", "Declaration Grooming ( Sample )"),  # Parenthetical not stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_complex_combinations(self):
        """Test soap pattern stripping with complex combinations."""
        test_cases = [
            ("B&M Seville soap (sample) (23)", "B&M Seville (sample) (23)"),  # Only "soap" stripped
            ("Stirling Bay Rum cream (SAMPLE) (5)", "Stirling Bay Rum (SAMPLE) (5)"),  # Only "cream" stripped
            ("Declaration Grooming croap ( Sample ) ()", "Declaration Grooming ( Sample ) ()"),  # Only "croap" stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_no_match(self):
        """Test strings that don't contain soap patterns."""
        test_cases = [
            "B&M Seville",
            "Stirling Bay Rum",
            "Declaration Grooming",
            "Product without soap patterns",  # "soap" is stripped
        ]
        for input_str in test_cases:
            result = strip_soap_patterns(input_str)
            if "soap" in input_str.lower():
                # If "soap" is in the input, it should be stripped
                assert "soap" not in result.lower(), f"Expected 'soap' to be stripped from '{input_str}', but got '{result}'"
            else:
                # Otherwise, should not change
                assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_soap_patterns_whitespace_cleanup(self):
        """Test that whitespace is properly cleaned up after stripping."""
        test_cases = [
            ("B&M Seville   soap   (sample)   ", "B&M Seville   (sample)   "),  # Only "soap" stripped
            ("Stirling Bay Rum  cream  (23)  ", "Stirling Bay Rum  (23)  "),  # Only "cream" stripped
            ("Declaration Grooming  croap  ", "Declaration Grooming  "),  # Only "croap" stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_none_input(self):
        """Test None input."""
        result = strip_soap_patterns(None)  # type: ignore
        assert result is None

    def test_strip_soap_patterns_empty_string(self):
        """Test empty string input."""
        result = strip_soap_patterns("")
        assert result == ""

    def test_strip_soap_patterns_product_indicators(self):
        """Test enhanced soap product indicator pattern stripping."""
        test_cases = [
            ("Stirling - Friends to the End - Shave Soap", "Stirling - Friends to the End"),
            ("B&M Seville Shaving Soap", "B&M Seville"),
            ("Declaration Grooming - Original - Shave Soap", "Declaration Grooming - Original"),
            ("House of Mammoth - Alive - Shave Soap", "House of Mammoth - Alive"),
            ("Proraso Red Cream", "Proraso Red"),
            ("Tabac Shaving Soap", "Tabac"),
            ("Stirling - Executive Man - Shave Soap (travel size)", "Stirling - Executive Man"),
            ("B&M Seville Shaving Soap (sample)", "B&M Seville"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_delimiter_cleanup(self):
        """Test that leading/trailing delimiters are cleaned up."""
        test_cases = [
            (" - Stirling - Friends to the End - ", "Stirling - Friends to the End"),
            (": B&M Seville :", "B&M Seville"),
            ("/ House of Mammoth /", "House of Mammoth"),
            ("~ Tabac ~", "Tabac"),
            ("_ Declaration Grooming _", "Declaration Grooming"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_preserves_middle_delimiters(self):
        """Test that middle delimiters between brand and scent are preserved."""
        test_cases = [
            ("Stirling - Executive Man - Shave Soap", "Stirling - Executive Man"),
            ("B&M - Seville - Shaving Soap", "B&M - Seville"),
            ("House of Mammoth : Alive : Shave Soap", "House of Mammoth : Alive"),
            ("Declaration Grooming / Original / Shave Soap", "Declaration Grooming / Original"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"


class TestStripRazorUseCounts:
    """Test razor use count stripping."""

    def test_strip_razor_use_counts_basic(self):
        """Test basic razor use count stripping."""
        test_cases = [
            ("Gold Dollar Straight Razor (6)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (12)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (23)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor [5]", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor [10]", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (new)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (NEW)", "Gold Dollar Straight Razor"),
        ]
        for input_str, expected in test_cases:
            result = strip_razor_use_counts(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_razor_use_counts_multiple_patterns(self):
        """Test razor use count stripping with multiple patterns."""
        test_cases = [
            ("Gold Dollar Straight Razor (6) (new)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor [5] (new)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (new) (12)", "Gold Dollar Straight Razor"),
        ]
        for input_str, expected in test_cases:
            result = strip_razor_use_counts(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_razor_use_counts_edge_cases(self):
        """Test razor use count stripping with edge cases."""
        # No patterns
        assert strip_razor_use_counts("Gold Dollar Straight Razor") == "Gold Dollar Straight Razor"

        # Empty string
        assert strip_razor_use_counts("") == ""

        # None input
        assert strip_razor_use_counts(None) is None  # type: ignore

        # Only patterns
        assert strip_razor_use_counts("(6)") == ""
        assert strip_razor_use_counts("[5]") == ""
        assert strip_razor_use_counts("(new)") == ""

    def test_strip_razor_use_counts_preserves_model_names(self):
        """Test that actual model names are preserved, only use counts are stripped."""
        # Real model names should be preserved
        assert strip_razor_use_counts("Gillette New") == "Gillette New"
        assert strip_razor_use_counts("iKon X3") == "iKon X3"
        assert strip_razor_use_counts("Gillette Tech") == "Gillette Tech"
        assert strip_razor_use_counts("Merkur 34C") == "Merkur 34C"

        # Use counts should be stripped from real model names
        assert strip_razor_use_counts("Gillette New (6)") == "Gillette New"
        assert strip_razor_use_counts("iKon X3 (12)") == "iKon X3"
        assert strip_razor_use_counts("Gillette Tech [5]") == "Gillette Tech"
        assert strip_razor_use_counts("Merkur 34C (new)") == "Merkur 34C"

        # Multiple use counts should all be stripped
        assert strip_razor_use_counts("Gillette New (6) (new)") == "Gillette New"
        assert strip_razor_use_counts("iKon X3 [10] (new)") == "iKon X3"

        # Complex model names should be preserved completely
        assert strip_razor_use_counts("Gillette New Standard") == "Gillette New Standard"
        assert strip_razor_use_counts("Gillette New Long Comb") == "Gillette New Long Comb"
        assert strip_razor_use_counts("Gillette New Short Comb") == "Gillette New Short Comb"
        assert strip_razor_use_counts("Gillette New Big Boy") == "Gillette New Big Boy"
