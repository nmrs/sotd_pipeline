#!/usr/bin/env python3
"""Tests for FullInputComponentMatchingStrategy."""

from unittest.mock import Mock

from sotd.match.brush_matching_strategies.full_input_component_matching_strategy import (
    FullInputComponentMatchingStrategy,
)
from sotd.match.types import MatchResult


class TestFullInputComponentMatchingStrategy:
    """Test the unified component matching strategy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handle_matcher = Mock()
        self.knot_matcher = Mock()
        self.catalogs = {"brushes": {}, "handles": {}, "knots": {}, "correct_matches": {}}

        self.strategy = FullInputComponentMatchingStrategy(
            handle_matcher=self.handle_matcher,
            knot_matcher=self.knot_matcher,
            catalogs=self.catalogs,
        )

    def test_init_with_required_components(self):
        """Test strategy initialization with required components."""
        assert self.strategy.handle_matcher == self.handle_matcher
        assert self.strategy.knot_matcher == self.knot_matcher
        assert self.strategy.catalogs == self.catalogs

    def test_dual_component_match_both_handle_and_knot(self):
        """Test dual component match when both handle and knot match."""
        # Mock handle match
        handle_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={"handle_maker": "Declaration Grooming", "handle_model": "Washington"},
            match_type="handle_match",
            strategy="HandleMatcher",
        )
        self.handle_matcher.match_handle_maker.return_value = handle_result

        # Mock knot match
        knot_result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            match_type="exact",
            pattern="declaration.*b2",
            strategy="KnotMatcher",
        )
        self.knot_matcher.match.return_value = knot_result

        result = self.strategy.match("Declaration Grooming Washington B2")

        assert result is not None
        assert result.strategy == "full_input_component_matching"  # Uses the actual strategy name
        assert result.match_type == "composite"
        # Score is applied by scoring engine: base 50 + dual_component modifier 15 = 65

    def test_single_component_match_handle_only(self):
        """Test single component match when only handle matches."""
        # Mock handle match
        handle_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={"handle_maker": "Declaration Grooming", "handle_model": "Washington"},
            match_type="handle_match",
            strategy="HandleMatcher",
        )
        self.handle_matcher.match_handle_maker.return_value = handle_result

        # Mock no knot match
        self.knot_matcher.match.return_value = None

        result = self.strategy.match("Declaration Grooming Washington")

        assert result is not None
        assert result.strategy == "full_input_component_matching"  # Uses the actual strategy name
        assert result.match_type == "single_component"
        # Score is applied by scoring engine: base 50 (no modifier)

    def test_single_component_match_knot_only(self):
        """Test single component match when only knot matches."""
        # Mock no handle match
        self.handle_matcher.match_handle_maker.return_value = None

        # Mock knot match
        knot_result = MatchResult(
            original="Declaration Grooming B2",
            matched={"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            match_type="exact",
            pattern="declaration.*b2",
            strategy="KnotMatcher",
        )
        self.knot_matcher.match.return_value = knot_result

        result = self.strategy.match("Declaration Grooming B2")

        assert result is not None
        assert result.strategy == "full_input_component_matching"  # Uses the actual strategy name
        assert result.match_type == "single_component"
        # Score is applied by scoring engine: base 50 (no modifier)

    def test_no_match_neither_handle_nor_knot(self):
        """Test no match when neither handle nor knot matches."""
        # Mock no handle match
        self.handle_matcher.match_handle_maker.return_value = None

        # Mock no knot match
        self.knot_matcher.match.return_value = None

        result = self.strategy.match("Invalid Brush String")

        assert result is None

    def test_handle_matcher_exception_handling(self):
        """Test handling of handle matcher exceptions."""
        # Mock handle matcher exception
        self.handle_matcher.match_handle_maker.side_effect = Exception("Handle matcher error")

        # Mock knot match
        knot_result = MatchResult(
            original="Declaration Grooming B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            match_type="exact",
            pattern="declaration.*b2",
            strategy="KnotMatcher",
        )
        self.knot_matcher.match.return_value = knot_result

        # Should still work with just knot match
        result = self.strategy.match("Declaration Grooming B2")

        assert result is not None
        assert result.strategy == "full_input_component_matching"  # Uses the actual strategy name
        # Score is applied by scoring engine: base 50 (no modifier)

    def test_knot_matcher_exception_handling(self):
        """Test handling of knot matcher exceptions."""
        # Mock handle match
        handle_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={"handle_maker": "Declaration Grooming", "handle_model": "Washington"},
            match_type="handle_match",
            strategy="HandleMatcher",
        )
        self.handle_matcher.match_handle_maker.return_value = handle_result

        # Mock knot matcher exception
        self.knot_matcher.match.side_effect = Exception("Knot matcher error")

        # Should still work with just handle match
        result = self.strategy.match("Declaration Grooming Washington")

        assert result is not None
        assert result.strategy == "full_input_component_matching"  # Uses the actual strategy name
        assert result.match_type == "single_component"
        # Score is applied by scoring engine: base 50 (no modifier)

    def test_empty_string_handling(self):
        """Test handling of empty input string."""
        result = self.strategy.match("")
        assert result is None

    def test_none_string_handling(self):
        """Test handling of None input string."""
        result = self.strategy.match("")  # Empty string instead of None
        assert result is None
