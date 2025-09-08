#!/usr/bin/env python3
"""Tests for extract normalization utility functions."""

from sotd.utils.extract_normalization import (
    normalize_for_matching,
    strip_usage_count_patterns,
    strip_handle_indicators,
    strip_soap_patterns,
    strip_trailing_periods,
)


class TestStripUsageCountPatterns:
    """Test usage count pattern stripping for all product types."""

    def test_strip_usage_count_patterns_basic(self):
        """Test basic blade count pattern stripping."""
        test_cases = [
            ("Astra Superior Platinum (5)", "Astra Superior Platinum"),
            ("Feather Hi-Stainless (10)", "Feather Hi-Stainless"),
            ("Gillette Silver Blue (15)", "Gillette Silver Blue"),
            ("Personna Platinum (20)", "Personna Platinum"),
        ]
        for input_str, expected in test_cases:
            result = strip_usage_count_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_usage_count_patterns_with_brackets(self):
        """Test blade count pattern stripping with bracket notation."""
        test_cases = [
            ("Astra Superior Platinum [5]", "Astra Superior Platinum"),
            ("Feather Hi-Stainless [10]", "Feather Hi-Stainless"),
            ("Gillette Silver Blue [15]", "Gillette Silver Blue"),
        ]
        for input_str, expected in test_cases:
            result = strip_usage_count_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_usage_count_patterns_no_match(self):
        """Test strings that don't contain blade count patterns."""
        test_cases = [
            "Astra Superior Platinum",
            "Feather Hi-Stainless",
            "Gillette Silver Blue",
            "Blade without count",
        ]
        for input_str in test_cases:
            result = strip_usage_count_patterns(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_usage_count_patterns_edge_cases(self):
        """Test blade count pattern stripping with edge cases."""
        # Empty string
        assert strip_usage_count_patterns("") == ""

        # None input
        assert strip_usage_count_patterns(None) is None  # type: ignore

        # Only count pattern
        assert strip_usage_count_patterns("(5)") == ""
        assert strip_usage_count_patterns("[10]") == ""

        # Multiple count patterns
        assert strip_usage_count_patterns("Astra (5) (10)") == "Astra"

    def test_strip_usage_count_patterns_comma_ordinal_usage(self):
        """Test blade count pattern stripping with ordinal usage patterns."""
        test_cases = [
            ("treet platinum , 1st use", "treet platinum ,"),  # Cleanup handles trailing comma
            ("treet platinum , 2nd use", "treet platinum ,"),  # Cleanup handles trailing comma
            ("feather artist club , 3rd use", "feather artist club ,"),  # Cleanup handles comma
            ("astra sp , 10th use", "astra sp ,"),  # Cleanup handles comma
            ("personna platinum , 1st use", "personna platinum ,"),  # Cleanup handles comma
            ("feather, 1st use", "feather,"),  # Cleanup handles trailing comma
            ("astra, 2nd use", "astra,"),  # Cleanup handles trailing comma
            ("treet platinum 1st use", "treet platinum"),  # No trailing punctuation
            ("feather 2nd use", "feather"),  # No trailing punctuation
        ]
        for input_str, expected in test_cases:
            result = strip_usage_count_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"


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
        assert strip_trailing_periods(None) == ""  # Now returns empty string instead of None

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
            (
                "Stirling Bay Rum sample",
                "Stirling Bay Rum",
            ),  # "sample" is stripped (standalone at end)
            (
                "Declaration Grooming soap sample",
                "Declaration Grooming",
            ),  # Both "soap" and "sample" stripped
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
            ("B&M Seville (sample)", "B&M Seville"),  # "(sample)" is stripped
            ("Stirling Bay Rum (SAMPLE)", "Stirling Bay Rum"),  # "(SAMPLE)" is stripped
            (
                "Declaration Grooming ( Sample )",
                "Declaration Grooming ( Sample )",
            ),  # "( Sample )" with spaces NOT stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_standalone_sample_indicators(self):
        """Test soap pattern stripping with standalone sample indicators at the end."""
        test_cases = [
            ("Stirling Bay Rum sample", "Stirling Bay Rum"),  # "sample" at end is stripped
            ("Declaration Grooming tester", "Declaration Grooming"),  # "tester" at end is stripped
            ("B&M Seville SAMPLE", "B&M Seville"),  # "SAMPLE" at end is stripped (case insensitive)
            ("Stirling Bay Rum sample ", "Stirling Bay Rum"),  # trailing space stripped
            ("Declaration Grooming sample.", "Declaration Grooming"),  # "sample." stripped
            ("B&M Seville sample!", "B&M Seville"),  # "sample!" stripped
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_complex_combinations(self):
        """Test soap pattern stripping with complex combinations."""
        test_cases = [
            (
                "B&M Seville soap (sample) (23)",
                "B&M Seville (23)",
            ),  # Both "soap" and "(sample)" stripped
            (
                "Stirling Bay Rum cream (SAMPLE) (5)",
                "Stirling Bay Rum (5)",
            ),  # Both "cream" and "(SAMPLE)" stripped
            (
                "Declaration Grooming croap ( Sample ) ()",
                "Declaration Grooming ( Sample ) ()",
            ),  # Only "croap" stripped
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
                assert (
                    "soap" not in result.lower()
                ), f"Expected 'soap' to be stripped from '{input_str}', but got '{result}'"
            else:
                # Otherwise, should not change
                assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_soap_patterns_whitespace_cleanup(self):
        """Test that whitespace is properly cleaned up after stripping."""
        test_cases = [
            (
                "B&M Seville   soap   (sample)   ",
                "B&M Seville",
            ),  # Both "soap" and "(sample)" stripped
            (
                "Stirling Bay Rum  cream  (23)  ",
                "Stirling Bay Rum (23)",
            ),  # "cream" stripped + whitespace normalized
            ("Declaration Grooming  croap  ", "Declaration Grooming"),  # Only "croap" stripped
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
