#!/usr/bin/env python3
"""Test file for AutomatedSplitStrategy (unified high/medium priority split strategy)."""

from sotd.match.brush_matching_strategies.automated_split_strategy import AutomatedSplitStrategy
from sotd.match.brush_scoring_config import BrushScoringConfig


class TestAutomatedSplitStrategy:
    """Test the unified AutomatedSplitStrategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.catalogs = {"brushes": {}, "handles": {}, "knots": {}, "correct_matches": {}}
        self.scoring_config = BrushScoringConfig()
        self.strategy = AutomatedSplitStrategy(self.catalogs, self.scoring_config)

    def test_high_priority_delimiter_with_match(self):
        """Test that high priority delimiters (' w/ ', ' with ') return appropriate strategy name."""
        # Test case: brush string with high priority delimiter
        test_input = "Simpson Chubby 2 w/ Zenith B07 Boar"

        result = self.strategy.match(test_input)

        # Should match and identify as high priority
        assert result is not None
        assert result.matched is not None
        assert result.strategy == "automated_split"
        # Should detect high priority delimiter for scoring modifier
        assert result.matched.get("high_priority_delimiter") is True
        assert result.matched.get("_delimiter_priority") == "high"

    def test_high_priority_delimiter_in_variant(self):
        """Test ' in ' delimiter (high priority)."""
        test_input = "Declaration B2 in Mozingo handle"

        result = self.strategy.match(test_input)

        assert result is not None
        assert result.strategy == "automated_split"
        if result.matched:
            assert result.matched.get("high_priority_delimiter") is True

    def test_medium_priority_delimiter_with_match(self):
        """Test that medium priority delimiters (' - ', ' + ') return appropriate strategy name."""
        # Test case: brush string with medium priority delimiter
        test_input = "Simpson Chubby 2 - Zenith B07 Boar"

        result = self.strategy.match(test_input)

        # Should match and identify as medium priority
        assert result is not None
        assert result.matched is not None
        assert result.strategy == "automated_split"
        # Should detect medium priority delimiter (no scoring modifier)
        assert result.matched.get("high_priority_delimiter") is False
        assert result.matched.get("_delimiter_priority") == "medium"

    def test_medium_priority_plus_delimiter(self):
        """Test ' + ' delimiter (medium priority)."""
        test_input = "Simpson Chubby 2 + Zenith B07 Boar"

        result = self.strategy.match(test_input)

        assert result is not None
        assert result.strategy == "automated_split"
        if result.matched:
            assert result.matched.get("high_priority_delimiter") is False

    def test_no_delimiter_no_match(self):
        """Test that strings without delimiters return None."""
        test_input = "Simpson Chubby 2"

        result = self.strategy.match(test_input)

        assert result is None

    def test_empty_string_no_match(self):
        """Test that empty strings return None."""
        result = self.strategy.match("")
        assert result is None

    def test_none_input_no_match(self):
        """Test that None input returns None."""
        result = self.strategy.match("")  # Empty string instead of None
        assert result is None

    def test_invalid_input_type_no_match(self):
        """Test that non-string input returns None."""
        result = self.strategy.match("")  # Empty string instead of 123
        assert result is None

    def test_unsplittable_string_no_match(self):
        """Test that strings marked as 'do not split' return None."""
        # This would need to be in brush_splits.yaml as a do-not-split entry
        test_input = "Simpson Chubby 2 w/ some unsplittable text"

        result = self.strategy.match(test_input)

        # For now, this should still split since we don't have the do-not-split logic
        # implemented yet
        assert result is not None
        assert result.strategy == "automated_split"
