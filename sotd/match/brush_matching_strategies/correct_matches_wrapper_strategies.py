"""
Correct Matches Wrapper Strategies.

These strategies wrap the legacy system's correct matches functionality
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class CorrectCompleteBrushWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper for legacy _match_correct_complete_brush functionality."""

    def __init__(self, legacy_matcher):
        """
        Initialize the strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using legacy correct complete brush logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_correct_complete_brush(value)
        if result:
            result.strategy = "correct_complete_brush"
        return result


class CorrectSplitBrushWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper for legacy _match_correct_split_brush functionality."""

    def __init__(self, legacy_matcher):
        """
        Initialize the strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using legacy correct split brush logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_correct_split_brush(value)
        if result:
            result.strategy = "correct_split_brush"
        return result
