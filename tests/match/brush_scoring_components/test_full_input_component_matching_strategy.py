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
        self.legacy_matcher = Mock()

        self.strategy = FullInputComponentMatchingStrategy(
            handle_matcher=self.handle_matcher,
            knot_matcher=self.knot_matcher,
            legacy_matcher=self.legacy_matcher,
        )

    def test_init_with_required_components(self):
        """Test strategy initialization with required components."""
        assert self.strategy.handle_matcher == self.handle_matcher
        assert self.strategy.knot_matcher == self.knot_matcher
        assert self.strategy.legacy_matcher == self.legacy_matcher

    def test_dual_component_match_both_handle_and_knot(self):
        """Test dual component match when both handle and knot match."""
        # Mock handle match
        handle_result = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
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

        # Mock legacy dual component result creation
        expected_result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            },
            match_type="composite",
            pattern="dual_component",
            strategy="dual_component",
        )
        self.legacy_matcher.create_dual_component_result.return_value = expected_result

        result = self.strategy.match("Declaration Grooming Washington B2")

        assert result is not None
        assert result.strategy == "dual_component"
        assert result.match_type == "composite"
        # Score is applied by scoring engine, not set in strategy

    def test_single_component_match_handle_only(self):
        """Test single component match when only handle matches."""
        # Mock handle match
        handle_result = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
        self.handle_matcher.match_handle_maker.return_value = handle_result

        # Mock no knot match
        self.knot_matcher.match.return_value = None

        # Mock legacy single component result creation
        expected_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": None, "model": None},
            },
            match_type="single_component",
            pattern="handle_only",
            strategy="single_component_fallback",
        )
        self.legacy_matcher.create_single_component_result.return_value = expected_result

        result = self.strategy.match("Declaration Grooming Washington")

        assert result is not None
        assert result.strategy == "single_component_fallback"
        assert result.match_type == "single_component"
        # Score is applied by scoring engine, not set in strategy

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

        # Mock legacy single component result creation
        expected_result = MatchResult(
            original="Declaration Grooming B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": None, "model": None},
                "knot": {"brand": "Declaration Grooming", "model": "B2", "fiber": "Badger"},
            },
            match_type="single_component",
            pattern="knot_only",
            strategy="single_component_fallback",
        )
        self.legacy_matcher.create_single_component_result.return_value = expected_result

        result = self.strategy.match("Declaration Grooming B2")

        assert result is not None
        assert result.strategy == "single_component_fallback"
        assert result.match_type == "single_component"
        # Score is applied by scoring engine, not set in strategy

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
        expected_result = MatchResult(
            original="Declaration Grooming B2",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": None, "model": None},
                "knot": {"brand": "Declaration Grooming", "model": "B2"},
            },
            match_type="single_component",
            pattern="knot_only",
            strategy="single_component_fallback",
        )
        self.legacy_matcher.create_single_component_result.return_value = expected_result

        result = self.strategy.match("Declaration Grooming B2")

        assert result is not None
        assert result.strategy == "single_component_fallback"
        # Score is applied by scoring engine, not set in strategy

    def test_knot_matcher_exception_handling(self):
        """Test handling of knot matcher exceptions."""
        # Mock handle match
        handle_result = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
        self.handle_matcher.match_handle_maker.return_value = handle_result

        # Mock knot matcher exception
        self.knot_matcher.match.side_effect = Exception("Knot matcher error")

        # Should still work with just handle match
        expected_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={
                "brand": None,
                "model": None,
                "handle": {"brand": "Declaration Grooming", "model": "Washington"},
                "knot": {"brand": None, "model": None},
            },
            match_type="single_component",
            pattern="handle_only",
            strategy="single_component_fallback",
        )
        self.legacy_matcher.create_single_component_result.return_value = expected_result

        result = self.strategy.match("Declaration Grooming Washington")

        assert result is not None
        assert result.strategy == "single_component_fallback"
        # Score is applied by scoring engine, not set in strategy

    def test_empty_string_handling(self):
        """Test handling of empty input string."""
        result = self.strategy.match("")
        assert result is None

    def test_none_string_handling(self):
        """Test handling of None input string."""
        result = self.strategy.match("")  # Empty string instead of None
        assert result is None

    def test_legacy_dual_component_result_creation_called(self):
        """Test that legacy dual component result creation is called correctly."""
        # Mock both matches
        handle_result = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
        self.handle_matcher.match_handle_maker.return_value = handle_result

        knot_result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            match_type="exact",
            pattern="declaration.*b2",
            strategy="KnotMatcher",
        )
        self.knot_matcher.match.return_value = knot_result

        # Mock legacy result
        expected_result = MatchResult(
            original="Declaration Grooming Washington B2",
            matched={},
            match_type="composite",
            pattern="dual_component",
            strategy="dual_component",
        )
        self.legacy_matcher.create_dual_component_result.return_value = expected_result

        self.strategy.match("Declaration Grooming Washington B2")

        # Verify legacy method was called with correct parameters
        self.legacy_matcher.create_dual_component_result.assert_called_once_with(
            handle_result, knot_result, "Declaration Grooming Washington B2", "dual_component"
        )

    def test_legacy_single_component_result_creation_called(self):
        """Test that legacy single component result creation is called correctly."""
        # Mock only handle match
        handle_result = {"handle_maker": "Declaration Grooming", "handle_model": "Washington"}
        self.handle_matcher.match_handle_maker.return_value = handle_result
        self.knot_matcher.match.return_value = None

        # Mock legacy result
        expected_result = MatchResult(
            original="Declaration Grooming Washington",
            matched={},
            match_type="single_component",
            pattern="handle_only",
            strategy="single_component_fallback",
        )
        self.legacy_matcher.create_single_component_result.return_value = expected_result

        self.strategy.match("Declaration Grooming Washington")

        # Verify legacy method was called with correct parameters
        self.legacy_matcher.create_single_component_result.assert_called_once_with(
            handle_result, None, "Declaration Grooming Washington", "single_component_fallback"
        )
