"""
Known Split Wrapper Strategy.

This strategy wraps the legacy system's known split functionality
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class KnownSplitWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper for legacy _match_known_split functionality."""

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
        Match using legacy known split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_known_split(value)
        if result:
            result.strategy = "known_split"
        return result
