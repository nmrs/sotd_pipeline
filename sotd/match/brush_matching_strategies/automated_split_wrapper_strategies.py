"""
Automated Split Wrapper Strategies.

These strategies wrap the legacy system's automated split functionality
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class HighPriorityAutomatedSplitWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper for legacy _match_high_priority_automated_split functionality."""

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
        Match using legacy high priority automated split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_high_priority_automated_split(value)
        if result:
            result.strategy = "high_priority_automated_split"
        return result


class MediumPriorityAutomatedSplitWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper for legacy _match_medium_priority_automated_split functionality."""

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
        Match using legacy medium priority automated split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_medium_priority_automated_split(value)
        if result:
            result.strategy = "medium_priority_automated_split"
        return result
