#!/usr/bin/env python3
"""Tests for competition tags utility functions."""

from unittest.mock import mock_open, patch

from sotd.utils.match_filter_utils import (
    load_competition_tags,
    strip_competition_tags,
    normalize_for_storage,
    strip_blade_count_patterns,
    extract_blade_use_count,
    extract_blade_count,
    extract_blade_and_use_count,
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
    """Test normalization for storage."""

    def test_normalize_for_storage_basic(self):
        """Test basic normalization."""
        competition_tags = {
            "strip_tags": ["CNC", "ARTISTCLUB"],
            "preserve_tags": [],
        }

        result = normalize_for_storage("Razor $CNC $ARTISTCLUB", competition_tags)
        assert result == "Razor"

    def test_normalize_for_storage_auto_load(self):
        """Test automatic loading of competition tags when not provided."""
        with patch("sotd.utils.match_filter_utils.load_competition_tags") as mock_load:
            mock_load.return_value = {
                "strip_tags": ["CNC", "ARTISTCLUB"],
                "preserve_tags": [],
            }

            result = normalize_for_storage("Razor $CNC $ARTISTCLUB")
            assert result == "Razor"
            mock_load.assert_called_once()

    def test_normalize_for_storage_none_input(self):
        """Test None input."""
        result = normalize_for_storage(None)  # type: ignore
        assert result is None

    def test_normalize_for_storage_integration(self):
        """Test integration with strip_blade_count_patterns."""
        # Test with competition tags
        assert normalize_for_storage("treet platinum (3x) #sotd") == "treet platinum #sotd"
        assert (
            normalize_for_storage("[2x] treet platinum (4 times) $TRICKORTREAT")
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
        """Test blade count pattern stripping integrated with normalize_for_storage."""
        # Test that normalize_for_storage now strips blade patterns
        assert normalize_for_storage("treet platinum (3x)") == "treet platinum"
        assert normalize_for_storage("[2x] treet platinum (4 times)") == "treet platinum"
        assert (
            normalize_for_storage("treet platinum (second use) - amazing blade")
            == "treet platinum - amazing blade"
        )

        # Test with competition tags
        assert normalize_for_storage("treet platinum (3x) #sotd") == "treet platinum #sotd"
        assert (
            normalize_for_storage("[2x] treet platinum (4 times) $TRICKORTREAT")
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
