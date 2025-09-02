"""Tests for KnotMatcher with unified MatchResult support."""

from unittest.mock import Mock

from sotd.match.brush.knot_matcher import KnotMatcher
from sotd.match.types import MatchResult


class TestKnotMatcherUnifiedMatchResult:
    """Test KnotMatcher with unified MatchResult support."""

    def test_knot_matcher_returns_section_match_result(self):
        """Test that section-based matchers return MatchResult with section/priority."""
        # Create mock strategies
        known_knot_strategy = Mock()
        known_knot_strategy.__class__.__name__ = "KnownKnotMatchingStrategy"
        known_knot_strategy.match.return_value = MatchResult(
            original="Zenith B2",
            matched={"brand": "Zenith", "model": "B2"},
            match_type="regex",
            pattern="zenith.*\\bb2\\b",
        )

        other_knot_strategy = Mock()
        other_knot_strategy.__class__.__name__ = "OtherKnotMatchingStrategy"
        other_knot_strategy.match.return_value = None

        strategies = [known_knot_strategy, other_knot_strategy]
        matcher = KnotMatcher(strategies)

        result = matcher.match("Zenith B2")

        assert isinstance(result, MatchResult)
        assert result.section == "known_knots"  # Zenith should be in known_knots
        assert result.priority == 1  # known_knots should have priority 1
        assert result.matched is not None
        assert result.matched["brand"] == "Zenith"
        assert result.pattern == "zenith.*\\bb2\\b"
        assert result.has_section_info

    def test_knot_matcher_returns_other_knots_section(self):
        """Test that other_knots strategy returns correct section/priority."""
        # Create mock strategies
        known_knot_strategy = Mock()
        known_knot_strategy.__class__.__name__ = "KnownKnotMatchingStrategy"
        known_knot_strategy.match.return_value = None

        other_knot_strategy = Mock()
        other_knot_strategy.__class__.__name__ = "OtherKnotMatchingStrategy"
        other_knot_strategy.match.return_value = MatchResult(
            original="Some Other Knot",
            matched={"brand": "Some", "model": "Other"},
            match_type="regex",
            pattern="some.*other",
        )

        strategies = [known_knot_strategy, other_knot_strategy]
        matcher = KnotMatcher(strategies)

        result = matcher.match("Some Other Knot")

        assert isinstance(result, MatchResult)
        assert result.section == "other_knots"  # Should be in other_knots
        assert result.priority == 2  # Should have priority 2 (second strategy)
        assert result.matched is not None
        assert result.matched["brand"] == "Some"
        assert result.has_section_info

    def test_knot_matcher_no_match_returns_none(self):
        """Test that no match returns None."""
        # Create mock strategies that return no matches
        known_knot_strategy = Mock()
        known_knot_strategy.__class__.__name__ = "KnownKnotMatchingStrategy"
        known_knot_strategy.match.return_value = None

        other_knot_strategy = Mock()
        other_knot_strategy.__class__.__name__ = "OtherKnotMatchingStrategy"
        other_knot_strategy.match.return_value = None

        strategies = [known_knot_strategy, other_knot_strategy]
        matcher = KnotMatcher(strategies)

        result = matcher.match("Unknown Knot")

        assert result is None
