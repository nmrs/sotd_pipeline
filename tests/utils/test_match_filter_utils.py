#!/usr/bin/env python3
"""Tests for competition tags utility functions."""

from unittest.mock import mock_open, patch

from sotd.utils.match_filter_utils import (
    load_competition_tags,
    normalize_for_matching,
    strip_competition_tags,
    strip_blade_count_patterns,
    extract_blade_use_count,
    extract_blade_count,
    extract_blade_and_use_count,
    strip_handle_indicators,
    strip_soap_patterns,
    strip_razor_use_counts,
)


class TestLoadCompetitionTags:
    """Test loading competition tags configuration."""

    def test_load_competition_tags_success(self):
        """Test successful loading of competition tags."""
        mock_data = {
            "strip_tags": ["CNC", "ARTISTCLUB", "FLIPTOP"],
            "preserve_tags": ["MODERNGEM", "KAMISORI"],
        }

        mock_yaml_content = (
            "strip_tags:\n  - CNC\n  - ARTISTCLUB\n  - FLIPTOP\n"
            "preserve_tags:\n  - MODERNGEM\n  - KAMISORI"
        )

        with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
            with patch("yaml.safe_load", return_value=mock_data):
                result = load_competition_tags()

        assert result == mock_data

    def test_load_competition_tags_missing_file(self, tmp_path):
        """Test loading when file doesn't exist."""
        tags_path = tmp_path / "nonexistent.yaml"
        result = load_competition_tags(tags_path)
        assert result == {"strip_tags": [], "preserve_tags": []}

    def test_load_competition_tags_corrupted_file(self, tmp_path):
        """Test loading when file is corrupted."""
        tags_path = tmp_path / "corrupted.yaml"
        tags_path.write_text("invalid: yaml: content: [")

        result = load_competition_tags(tags_path)
        assert result == {"strip_tags": [], "preserve_tags": []}

    def test_load_competition_tags_empty_file(self, tmp_path):
        """Test loading when file is empty."""
        tags_path = tmp_path / "empty.yaml"
        tags_path.touch()

        result = load_competition_tags(tags_path)
        assert result == {"strip_tags": [], "preserve_tags": []}


class TestStripCompetitionTags:
    """Test stripping competition tags from strings."""

    def test_strip_competition_tags_basic(self):
        """Test basic tag stripping."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB", "FLIPTOP"],
            "preserve_tags": ["MODERNGEM", "KAMISORI"],
        }

        result = strip_competition_tags(
            "Asylum Artist Club RX v2 $CNC $ARTISTCLUB", competition_tags
        )
        assert result == "Asylum Artist Club RX v2"

    def test_strip_competition_tags_preserves_useful_tags(self):
        """Test that useful tags are preserved."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB", "FLIPTOP"],
            "preserve_tags": ["MODERNGEM", "KAMISORI"],
        }

        result = strip_competition_tags("Blackland Sabre $MODERNGEM $CNC", competition_tags)
        assert result == "Blackland Sabre $MODERNGEM"

    def test_strip_competition_tags_multiple_spaces(self):
        """Test handling of multiple spaces after tag removal."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor $CNC  $ARTISTCLUB  Test", competition_tags)
        assert result == "Razor Test"

    def test_strip_competition_tags_case_insensitive(self):
        """Test case-insensitive tag matching."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor $cnc $ArtistClub", competition_tags)
        assert result == "Razor"

    def test_strip_competition_tags_no_tags(self):
        """Test string with no tags."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Plain razor name", competition_tags)
        assert result == "Plain razor name"

    def test_strip_competition_tags_empty_string(self):
        """Test empty string."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("", competition_tags)
        assert result == ""

    def test_strip_competition_tags_none_input(self):
        """Test None input."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags(None, competition_tags)  # type: ignore
        assert result is None

    def test_strip_competition_tags_with_backticks(self):
        """Test tags wrapped in backticks."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor `$CNC` `$ARTISTCLUB`", competition_tags)
        assert result == "Razor"

    def test_strip_competition_tags_with_asterisks(self):
        """Test tags wrapped in asterisks."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor *$CNC* *$ARTISTCLUB*", competition_tags)
        assert result == "Razor"

    def test_strip_competition_tags_partial_matches_preserved(self):
        """Test that partial matches are preserved."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor CNCARTISTCLUB", competition_tags)
        assert result == "Razor CNCARTISTCLUB"

    def test_strip_competition_tags_unknown_tags_preserved(self):
        """Test that unknown tags are preserved."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor $UNKNOWN $OTHER", competition_tags)
        assert result == "Razor $UNKNOWN $OTHER"

    def test_strip_competition_tags_mixed_known_unknown(self):
        """Test mixed known and unknown tags."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = strip_competition_tags("Razor $CNC $UNKNOWN $ARTISTCLUB", competition_tags)
        assert result == "Razor $UNKNOWN"

    def test_strip_competition_tags_preserve_tags_work(self):
        """Test that preserve_tags actually work."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB", "MODERNGEM"],
            "preserve_tags": ["MODERNGEM"],
        }

        result = strip_competition_tags("Razor $CNC $MODERNGEM $ARTISTCLUB", competition_tags)
        assert result == "Razor $MODERNGEM"

    def test_strip_competition_tags_auto_load(self):
        """Test automatic loading of competition tags when not provided."""
        with patch("sotd.utils.match_filter_utils.load_competition_tags") as mock_load:
            mock_load.return_value = {
                "strip_tags": ["CNC", "ARTISTCLUB"],
                "preserve_tags": [],
            }

            result = strip_competition_tags("Razor $CNC $ARTISTCLUB")
            assert result == "Razor"
            mock_load.assert_called_once()


class TestNormalizeForStorage:
    """Test normalization for storage (deprecated, now uses normalize_for_matching)."""

    def test_normalize_for_storage_basic(self):
        """Test basic normalization."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = normalize_for_matching("Razor $CNC $ARTISTCLUB", competition_tags)
        assert result == "Razor"

    def test_normalize_for_storage_auto_load(self):
        """Test automatic loading of competition tags when not provided."""
        with patch("sotd.utils.match_filter_utils.load_competition_tags") as mock_load:
            mock_load.return_value = {
                "strip_tags": ["CNC", "ARTISTCLUB"],
                "preserve_tags": [],
            }

            result = normalize_for_matching("Razor $CNC $ARTISTCLUB")
            assert result == "Razor"
            mock_load.assert_called_once()

    def test_normalize_for_storage_none_input(self):
        """Test None input."""
        result = normalize_for_matching(None)  # type: ignore
        assert result is None

    def test_normalize_for_storage_integration(self):
        """Test integration with strip_blade_count_patterns."""
        # Test with competition tags
        assert (
            normalize_for_matching("treet platinum (3x) #sotd", field="blade")
            == "treet platinum #sotd"
        )
        assert (
            normalize_for_matching("[2x] treet platinum (4 times) $TRICKORTREAT", field="blade")
            == "treet platinum $TRICKORTREAT"
        )


class TestStripBladeCountPatterns:
    """Test stripping blade count patterns from strings."""

    def test_strip_blade_count_patterns_basic(self):
        """Test basic blade count pattern stripping."""
        # Test leading blade count patterns
        assert strip_blade_count_patterns("[2x] treet platinum") == "treet platinum"
        assert strip_blade_count_patterns("(2x) treet platinum") == "treet platinum"
        assert strip_blade_count_patterns("{2x} treet platinum") == "treet platinum"
        assert strip_blade_count_patterns("[X2] treet platinum") == "treet platinum"
        assert strip_blade_count_patterns("(x2) treet platinum") == "treet platinum"

        # Test usage count patterns
        assert strip_blade_count_patterns("treet platinum (3x)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum [x3]") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum {2x}") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (x4)") == "treet platinum"

        # Test "times" patterns
        assert strip_blade_count_patterns("treet platinum (4 times)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum [5 times]") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum {3 times}") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (1 time)") == "treet platinum"

        # Test ordinal patterns
        assert strip_blade_count_patterns("treet platinum (7th use)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum [3rd use]") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum {2nd use}") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (1st use)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (4th use)") == "treet platinum"

        # Test word-based ordinal patterns
        assert strip_blade_count_patterns("treet platinum (second use)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum [third use]") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum {fourth use}") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (first use)") == "treet platinum"

        # Test standalone patterns
        assert strip_blade_count_patterns("treet platinum x4") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum 2x") == "treet platinum"

        # Test complex combinations
        assert strip_blade_count_patterns("[2x] treet platinum (3x)") == "treet platinum"
        assert strip_blade_count_patterns("treet platinum (3x) #sotd") == "treet platinum #sotd"
        assert (
            strip_blade_count_patterns("treet platinum (3) - great shave")
            == "treet platinum - great shave"
        )

        # Test new patterns: "new" (meaning 1st use)
        assert strip_blade_count_patterns("7'o clock - yellow (new)") == "7'o clock - yellow"
        assert strip_blade_count_patterns("astra green new") == "astra green"
        assert strip_blade_count_patterns("new blade") == "blade"

        # Test ordinal use without brackets: 3rd use, 2nd use, etc.
        assert strip_blade_count_patterns("astra green 3rd use") == "astra green"
        assert strip_blade_count_patterns("astra green 2nd use") == "astra green"
        assert strip_blade_count_patterns("astra green 1st use") == "astra green"

        # Test escaped bracket patterns: [2\], [3\], etc.
        assert strip_blade_count_patterns("astra green [2\\]") == "astra green"
        assert strip_blade_count_patterns("astra green [3\\]") == "astra green"

        # Test that "indian" is NOT treated as a use count pattern
        assert strip_blade_count_patterns("astra green (indian)") == "astra green (indian)"
        assert strip_blade_count_patterns("indian blade") == "indian blade"
        assert strip_blade_count_patterns("blade indian") == "blade indian"

        # Test edge cases
        assert strip_blade_count_patterns("") == ""
        assert strip_blade_count_patterns("treet platinum") == "treet platinum"  # No patterns
        assert strip_blade_count_patterns("(3) treet platinum") == "treet platinum"  # Simple number

    def test_strip_blade_count_patterns_integration(self):
        """Test blade count pattern stripping integrated with normalize_for_matching."""
        # Test that normalize_for_matching now strips blade patterns
        assert normalize_for_matching("treet platinum (3x)", field="blade") == "treet platinum"
        assert (
            normalize_for_matching("[2x] treet platinum (4 times)", field="blade")
            == "treet platinum"
        )
        assert (
            normalize_for_matching("treet platinum (second use) - amazing blade", field="blade")
            == "treet platinum - amazing blade"
        )

        # Test with competition tags
        assert (
            normalize_for_matching("treet platinum (3x) #sotd", field="blade")
            == "treet platinum #sotd"
        )
        assert (
            normalize_for_matching("[2x] treet platinum (4 times) $TRICKORTREAT", field="blade")
            == "treet platinum $TRICKORTREAT"
        )


class TestExtractBladeUseCount:
    """Test extracting blade use count from strings."""

    def test_extract_blade_use_count_basic(self):
        """Test basic blade use count extraction."""
        # Test standard patterns
        assert extract_blade_use_count("treet platinum (3x)") == 3
        assert extract_blade_use_count("treet platinum [x3]") == 3
        assert extract_blade_use_count("treet platinum {2x}") == 2
        assert extract_blade_use_count("treet platinum (x4)") == 4

        # Test "times" patterns
        assert extract_blade_use_count("treet platinum (4 times)") == 4
        assert extract_blade_use_count("treet platinum [5 times]") == 5
        assert extract_blade_use_count("treet platinum {3 times}") == 3
        assert extract_blade_use_count("treet platinum (1 time)") == 1

        # Test ordinal patterns
        assert extract_blade_use_count("treet platinum (7th use)") == 7
        assert extract_blade_use_count("treet platinum [3rd use]") == 3
        assert extract_blade_use_count("treet platinum {2nd use}") == 2
        assert extract_blade_use_count("treet platinum (1st use)") == 1
        assert extract_blade_use_count("treet platinum (4th use)") == 4

        # Test word-based ordinal patterns
        assert extract_blade_use_count("treet platinum (second use)") == 2
        assert extract_blade_use_count("treet platinum [third use]") == 3
        assert extract_blade_use_count("treet platinum {fourth use}") == 4
        assert extract_blade_use_count("treet platinum (first use)") == 1

        # Test standalone patterns
        assert extract_blade_use_count("treet platinum x4") == 4
        assert extract_blade_use_count("treet platinum 2x") == 2

        # Test new patterns
        assert extract_blade_use_count("7'o clock - yellow (new)") == 1
        assert extract_blade_use_count("astra green new") == 1
        assert extract_blade_use_count("astra green 3rd use") == 3
        assert extract_blade_use_count("astra green [2\\]") == 2

        # Test edge cases
        assert extract_blade_use_count("") is None
        assert extract_blade_use_count("treet platinum") is None  # No patterns
        assert extract_blade_use_count("astra green (indian)") is None  # Not a use count


class TestExtractBladeCount:
    """Test extracting blade count from strings."""

    def test_extract_blade_count_basic(self):
        """Test basic blade count extraction."""
        # Test leading blade count patterns
        assert extract_blade_count("[2x] treet platinum") == 2
        assert extract_blade_count("(2x) treet platinum") == 2
        assert extract_blade_count("{2x} treet platinum") == 2
        assert extract_blade_count("[X2] treet platinum") == 2
        assert extract_blade_count("(x2) treet platinum") == 2

        # Test that non-leading patterns are not extracted
        assert extract_blade_count("treet platinum [2x]") is None
        assert extract_blade_count("treet platinum (2x)") is None

        # Test edge cases
        assert extract_blade_count("") is None
        assert extract_blade_count("treet platinum") is None  # No patterns


class TestExtractBladeAndUseCount:
    """Test extracting both blade count and use count from strings."""

    def test_extract_blade_and_use_count_basic(self):
        """Test basic extraction of both counts."""
        # Test with both blade count and use count
        blade_count, use_count = extract_blade_and_use_count("[2x] treet platinum (3x)")
        assert blade_count == 2
        assert use_count == 3

        # Test with only use count
        blade_count, use_count = extract_blade_and_use_count("treet platinum (3x)")
        assert blade_count is None
        assert use_count == 3

        # Test with only blade count
        blade_count, use_count = extract_blade_and_use_count("[2x] treet platinum")
        assert blade_count == 2
        assert use_count is None

        # Test with new patterns
        blade_count, use_count = extract_blade_and_use_count("7'o clock - yellow (new)")
        assert blade_count is None
        assert use_count == 1

        blade_count, use_count = extract_blade_and_use_count("astra green 3rd use")
        assert blade_count is None
        assert use_count == 3

        blade_count, use_count = extract_blade_and_use_count("astra green [2\\]")
        assert blade_count is None
        assert use_count == 2

        # Test edge cases
        blade_count, use_count = extract_blade_and_use_count("")
        assert blade_count is None
        assert use_count is None

        blade_count, use_count = extract_blade_and_use_count("treet platinum")
        assert blade_count is None
        assert use_count is None


class TestStripHandleIndicators:
    """Test handle indicator stripping for razors."""

    def test_strip_handle_indicators_basic(self):
        """Test basic handle indicator patterns."""
        test_cases = [
            ("Razor w/ Blackland handle", "Razor"),
            ("Razor with Merkur handle", "Razor"),
            ("Razor handle: Wolfman", "Razor"),
            ("Razor using Karve handle", "Razor"),
            ("Charcoal Goods LVL II SS on Triad Aristocrat SS handle", "Charcoal Goods LVL II SS"),
        ]
        for input_str, expected in test_cases:
            result = strip_handle_indicators(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_handle_indicators_complex_brands(self):
        """Test handle indicators with complex brand names."""
        test_cases = [
            (
                "Aylsworth Razors - Frank-kant, Drakkant SS w/ Blackland Razors Vector Handle",
                "Aylsworth Razors - Frank-kant, Drakkant SS",
            ),
            ("Razor with Above the Tie handle", "Razor"),
            ("Razor w/ Charcoal Goods handle", "Razor"),
        ]
        for input_str, expected in test_cases:
            result = strip_handle_indicators(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_handle_indicators_case_insensitive(self):
        """Test that handle indicators are stripped case-insensitively."""
        test_cases = [
            ("Razor W/ Blackland Handle", "Razor"),
            ("Razor WITH Merkur HANDLE", "Razor"),
            ("Razor Handle: Wolfman", "Razor"),
            ("Razor USING Karve Handle", "Razor"),
            ("Charcoal Goods LVL II SS ON Triad Aristocrat SS Handle", "Charcoal Goods LVL II SS"),
        ]
        for input_str, expected in test_cases:
            result = strip_handle_indicators(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_handle_indicators_no_match(self):
        """Test strings that don't contain handle indicators."""
        test_cases = [
            "Merkur 34C",
            "Blackland Blackbird",
            "Razor without handle info",
            "Razor handle info",  # No colon or "w/"
        ]
        for input_str in test_cases:
            result = strip_handle_indicators(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_handle_indicators_whitespace_cleanup(self):
        """Test that whitespace is properly cleaned up after stripping."""
        test_cases = [
            ("Razor   w/   Blackland   handle  ", "Razor"),
            ("Razor  with  Merkur  handle  ", "Razor"),
            ("Razor  handle:  Wolfman  ", "Razor"),
        ]
        for input_str, expected in test_cases:
            result = strip_handle_indicators(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_handle_indicators_none_input(self):
        """Test None input."""
        result = strip_handle_indicators(None)  # type: ignore
        assert result is None

    def test_strip_handle_indicators_empty_string(self):
        """Test empty string input."""
        result = strip_handle_indicators("")
        assert result == ""

    def test_normalize_for_storage_razor_with_handle_indicators(self):
        """Test that normalize_for_storage strips handle indicators for razor field."""
        # Use competition tags that don't include our test tags
        test_competition_tags = {
            "strip_tags": ["SOMEOTHER"],
            "preserve_tags": ["CNC", "SOTD", "ARTISTCLUB"],
        }
        test_cases = [
            ("Razor w/ Blackland handle $CNC", "Razor $CNC"),
            ("Razor with Merkur handle #sotd", "Razor #sotd"),
            ("Razor handle: Wolfman $ARTISTCLUB", "Razor $ARTISTCLUB"),
        ]
        for input_str, expected in test_cases:
            result = normalize_for_matching(input_str, test_competition_tags, field="razor")
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_normalize_for_storage_razor_no_handle_indicators(self):
        """Test that normalize_for_matching doesn't affect razors without handle indicators."""
        # Use competition tags that don't include our test tags
        test_competition_tags = {"strip_tags": ["SOMEOTHER"], "preserve_tags": ["CNC", "SOTD"]}
        test_cases = [
            ("Merkur 34C $CNC", "Merkur 34C $CNC"),
            ("Blackland Blackbird #sotd", "Blackland Blackbird #sotd"),
        ]
        for input_str, expected in test_cases:
            result = normalize_for_matching(input_str, test_competition_tags, field="razor")
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"


class TestNormalizeForMatching:
    """Test normalization for matching."""

    def test_normalize_for_matching_basic(self):
        """Test basic normalization functionality."""
        competition_tags = {"strip_tags": ["CNC", "ARTISTCLUB"]}
        result = normalize_for_matching("Razor $CNC $ARTISTCLUB", competition_tags)
        assert result == "Razor"

    def test_normalize_for_matching_auto_load(self):
        """Test normalization with auto-loaded competition tags."""
        result = normalize_for_matching("Razor $CNC $ARTISTCLUB")
        assert result == "Razor"

    def test_normalize_for_matching_none_input(self):
        """Test normalization with None input."""
        result = normalize_for_matching(None)  # type: ignore
        assert result is None

    def test_normalize_for_matching_blade_patterns(self):
        """Test that normalize_for_matching strips blade patterns for blade field."""
        # Test blade count patterns
        assert normalize_for_matching("treet platinum (3x)", field="blade") == "treet platinum"
        assert (
            normalize_for_matching("[2x] treet platinum (4 times)", field="blade")
            == "treet platinum"
        )
        assert (
            normalize_for_matching("treet platinum (second use) - amazing blade", field="blade")
            == "treet platinum - amazing blade"
        )

        # Test with competition tags
        assert (
            normalize_for_matching("treet platinum (3x) #sotd", field="blade")
            == "treet platinum #sotd"
        )
        assert (
            normalize_for_matching("[2x] treet platinum (4 times) $PLASTIC", field="blade")
            == "treet platinum"
        )

    def test_normalize_for_matching_razor_handle_indicators(self):
        """Test that normalize_for_matching strips handle indicators for razor field."""
        test_competition_tags = {"strip_tags": ["CNC", "ARTISTCLUB"]}

        # Test handle indicators
        input_str = "Razor / [brand] handle"
        result = normalize_for_matching(input_str, test_competition_tags, field="razor")
        assert result == "Razor"

        # Test razors without handle indicators
        input_str = "Gillette Tech"
        result = normalize_for_matching(input_str, test_competition_tags, field="razor")
        assert result == "Gillette Tech"

    def test_normalize_for_matching_case_preservation(self):
        """Test that normalize_for_matching preserves case for correct match consistency."""
        # Test that case is preserved (unlike BaseMatcher.normalize which lowercases)
        assert (
            normalize_for_matching("*New* King C. Gillette", field="razor")
            == "*New* King C. Gillette"
        )
        assert normalize_for_matching("ATT S1", field="razor") == "ATT S1"
        assert (
            normalize_for_matching("Above The Tie Atlas S1", field="razor")
            == "Above The Tie Atlas S1"
        )

    def test_normalize_for_matching_field_specific_behavior(self):
        """Test that normalize_for_matching applies field-specific normalization correctly."""
        # Blade field should strip patterns
        assert normalize_for_matching("blade (3x)", field="blade") == "blade"

        # Razor field should strip handle indicators
        assert normalize_for_matching("razor / [brand] handle", field="razor") == "razor"

        # Soap field should strip soap-related patterns
        assert normalize_for_matching("soap sample", field="soap") == "soap"
        assert normalize_for_matching("soap (sample)", field="soap") == "soap"

        # Other fields should only strip competition tags
        assert normalize_for_matching("brush $PLASTIC", field="brush") == "brush"

    def test_normalize_for_matching_whitespace_normalization(self):
        """Test that normalize_for_matching normalizes whitespace correctly."""
        assert normalize_for_matching("  multiple    spaces  ", field="razor") == "multiple spaces"
        assert normalize_for_matching("\ttabs\tand\tspaces\t", field="blade") == "tabs and spaces"

    def test_normalize_for_matching_edge_cases(self):
        """Test normalize_for_matching with edge cases."""
        # Empty string
        assert normalize_for_matching("", field="razor") == ""

        # String with only whitespace
        assert normalize_for_matching("   \t\n   ", field="blade") == ""

        # String with only competition tags
        assert normalize_for_matching("$CNC $ARTISTCLUB", field="razor") == ""

        # String with only blade patterns
        assert normalize_for_matching("(3x)", field="blade") == ""

        # String with only handle indicators
        assert normalize_for_matching("/ [brand] handle", field="razor") == ""

    def test_normalize_for_matching_comprehensive_examples(self):
        """Test normalize_for_matching with comprehensive real-world examples."""
        # Real examples from correct_matches.yaml
        assert (
            normalize_for_matching("*New* King C. Gillette", field="razor")
            == "*New* King C. Gillette"
        )
        assert normalize_for_matching("ATT S1", field="razor") == "ATT S1"
        assert (
            normalize_for_matching("Above The Tie Atlas S1", field="razor")
            == "Above The Tie Atlas S1"
        )

        # Examples with patterns that should be stripped
        assert (
            normalize_for_matching("treet platinum (3x) #sotd", field="blade")
            == "treet platinum #sotd"
        )
        assert normalize_for_matching("Razor / [brand] handle", field="razor") == "Razor"

        # Examples with competition tags
        assert normalize_for_matching("soap $PLASTIC", field="soap") == "soap"


class TestStripSoapPatterns:
    """Test soap pattern stripping."""

    def test_strip_soap_patterns_basic(self):
        """Test basic soap pattern stripping."""
        test_cases = [
            ("B&M Seville soap", "B&M Seville"),
            ("Stirling Bay Rum sample", "Stirling Bay Rum"),
            ("Declaration Grooming soap sample", "Declaration Grooming"),
            ("Cella croap", "Cella"),
            ("Proraso cream", "Proraso"),
            ("MWF puck", "MWF"),
            ("Arko shaving soap", "Arko"),
            ("Tabac shaving cream", "Tabac"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_with_use_counts(self):
        """Test soap pattern stripping with use counts."""
        test_cases = [
            ("B&M Seville (23)", "B&M Seville"),
            ("Stirling Bay Rum (5)", "Stirling Bay Rum"),
            ("Declaration Grooming ()", "Declaration Grooming"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_with_sample_markers(self):
        """Test soap pattern stripping with sample markers."""
        test_cases = [
            ("B&M Seville (sample)", "B&M Seville"),
            ("Stirling Bay Rum (SAMPLE)", "Stirling Bay Rum"),
            ("Declaration Grooming ( Sample )", "Declaration Grooming"),
        ]
        for input_str, expected in test_cases:
            result = strip_soap_patterns(input_str)
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"

    def test_strip_soap_patterns_complex_combinations(self):
        """Test soap pattern stripping with complex combinations."""
        test_cases = [
            ("B&M Seville soap (sample) (23)", "B&M Seville"),
            ("Stirling Bay Rum cream (SAMPLE) (5)", "Stirling Bay Rum"),
            ("Declaration Grooming croap ( Sample ) ()", "Declaration Grooming"),
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
            "Soap without patterns",
        ]
        for input_str in test_cases:
            result = strip_soap_patterns(input_str)
            assert result == input_str, f"Should not change '{input_str}', but got '{result}'"

    def test_strip_soap_patterns_whitespace_cleanup(self):
        """Test that whitespace is properly cleaned up after stripping."""
        test_cases = [
            ("B&M Seville   soap   (sample)   ", "B&M Seville"),
            ("Stirling Bay Rum  cream  (23)  ", "Stirling Bay Rum"),
            ("Declaration Grooming  croap  ", "Declaration Grooming"),
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

    def test_normalize_for_matching_soap_patterns(self):
        """Test that normalize_for_matching strips soap patterns for soap field."""
        # Test soap-related patterns
        assert normalize_for_matching("B&M Seville soap", field="soap") == "B&M Seville"
        assert normalize_for_matching("Stirling Bay Rum sample", field="soap") == "Stirling Bay Rum"
        assert (
            normalize_for_matching("Declaration Grooming (sample)", field="soap")
            == "Declaration Grooming"
        )

        # Test with competition tags
        assert normalize_for_matching("B&M Seville soap $PLASTIC", field="soap") == "B&M Seville"
        assert (
            normalize_for_matching("Stirling Bay Rum (23) #sotd", field="soap")
            == "Stirling Bay Rum #sotd"
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
        assert strip_razor_use_counts("Gillette New DeLuxe") == "Gillette New DeLuxe"
        assert strip_razor_use_counts("iKon X3 Slant") == "iKon X3 Slant"
        assert strip_razor_use_counts("Merkur 34C HD") == "Merkur 34C HD"
        assert strip_razor_use_counts("Gillette Tech Ball End") == "Gillette Tech Ball End"
        assert strip_razor_use_counts("Gillette Tech Fat Handle") == "Gillette Tech Fat Handle"
        assert strip_razor_use_counts("Gillette Tech Flat Bottom") == "Gillette Tech Flat Bottom"

    def test_strip_razor_use_counts_gillette_new_specific(self):
        """Test specifically that 'Gillette New' is preserved exactly as-is."""
        # This is a critical test case - ensure "Gillette New" is never stripped to just "Gillette"
        assert strip_razor_use_counts("Gillette New") == "Gillette New"

        # Test with use counts to ensure they're stripped but "New" is preserved
        assert strip_razor_use_counts("Gillette New (6)") == "Gillette New"
        assert strip_razor_use_counts("Gillette New [5]") == "Gillette New"
        assert strip_razor_use_counts("Gillette New (new)") == "Gillette New"
        assert strip_razor_use_counts("Gillette New (6) (new)") == "Gillette New"

    def test_normalize_for_matching_razor_use_counts(self):
        """Test that normalize_for_matching strips use counts for razor field."""
        test_competition_tags = {"strip_tags": ["CNC", "ARTISTCLUB"]}

        test_cases = [
            ("Gold Dollar Straight Razor (6)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor [5]", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (new)", "Gold Dollar Straight Razor"),
            ("Gold Dollar Straight Razor (6) $CNC", "Gold Dollar Straight Razor"),
        ]
        for input_str, expected in test_cases:
            result = normalize_for_matching(input_str, test_competition_tags, field="razor")
            assert (
                result == expected
            ), f"Failed for '{input_str}': got '{result}', expected '{expected}'"
