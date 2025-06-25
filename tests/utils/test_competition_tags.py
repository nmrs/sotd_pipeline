#!/usr/bin/env python3
"""Tests for competition tags utility functions."""

from unittest.mock import mock_open, patch

from sotd.utils.competition_tags import (
    load_competition_tags,
    strip_competition_tags,
    normalize_for_storage,
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
        with patch("sotd.utils.competition_tags.load_competition_tags") as mock_load:
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
        with patch("sotd.utils.competition_tags.load_competition_tags") as mock_load:
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
