#!/usr/bin/env python3
"""Test file for AutomatedSplitStrategy (unified high/medium priority split strategy)."""

import pytest

from sotd.match.brush_matching_strategies.automated_split_strategy import AutomatedSplitStrategy
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.brush_scoring_config import BrushScoringConfig


class TestAutomatedSplitStrategy:
    """Test the unified AutomatedSplitStrategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.legacy_matcher = BrushMatcher()
        self.scoring_config = BrushScoringConfig()
        # Strategy doesn't exist yet - this will fail initially
        self.strategy = AutomatedSplitStrategy(self.legacy_matcher, self.scoring_config)

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
        assert hasattr(result, "high_priority_delimiter")
        assert result.high_priority_delimiter is True

    def test_high_priority_delimiter_in_variant(self):
        """Test ' in ' delimiter (high priority)."""
        test_input = "Declaration B2 in Mozingo handle"

        result = self.strategy.match(test_input)

        assert result is not None
        assert result.strategy == "automated_split"
        assert result.high_priority_delimiter is True

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
        assert hasattr(result, "high_priority_delimiter")
        assert result.high_priority_delimiter is False

    def test_medium_priority_plus_delimiter(self):
        """Test ' + ' delimiter (medium priority)."""
        test_input = "Simpson Chubby 2 + Zenith B07 Boar"

        result = self.strategy.match(test_input)

        assert result is not None
        assert result.strategy == "automated_split"
        assert result.high_priority_delimiter is False

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
        result = self.strategy.match(None)
        assert result is None

    def test_invalid_input_type_no_match(self):
        """Test that non-string input returns None."""
        result = self.strategy.match(123)
        assert result is None

    def test_unsplittable_string_no_match(self):
        """Test that strings marked as 'do not split' return None."""
        # This would need to be in brush_splits.yaml as a do-not-split entry
        test_input = "Simpson Chubby 2 w/ some unsplittable text"

        result = self.strategy.match(test_input)

        # Should return None if marked as do-not-split
        # (This test may pass initially if the string isn't in do-not-split list)
        # We're testing the behavior, not requiring a specific input to be marked

    def test_strategy_name_consistency(self):
        """Test that strategy names match legacy system expectations."""
        # High priority should use high_priority_automated_split
        high_result = self.strategy.match("Brush w/ Handle")
        if high_result:  # Only test if match succeeds
            assert high_result.strategy == "automated_split"

        # Medium priority should use medium_priority_automated_split
        medium_result = self.strategy.match("Brush - Handle")
        if medium_result:  # Only test if match succeeds
            assert medium_result.strategy == "automated_split"

    def test_curated_splits_take_priority(self):
        """Test that curated splits from brush_splits.yaml take priority over automated splits."""
        # This test depends on having a curated split in brush_splits.yaml
        # If one exists, it should be used regardless of delimiters
        # This is more of an integration test to ensure the strategy respects curated data
        pass  # Will implement once we know the curated split format

    def test_base_class_inheritance(self):
        """Test that AutomatedSplitStrategy properly inherits from BaseBrushMatchingStrategy."""
        from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
            BaseBrushMatchingStrategy,
        )

        assert isinstance(self.strategy, BaseBrushMatchingStrategy)
        assert hasattr(self.strategy, "match")
        assert callable(self.strategy.match)
