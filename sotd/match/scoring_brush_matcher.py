"""
Stub implementation of BrushScoringMatcher for Phase 1 development.

This is a placeholder implementation that will be replaced with the full
scoring system in subsequent phases.
"""

from typing import Optional

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import MatchResult


class BrushScoringMatcher:
    """
    Stub implementation of the brush scoring matcher.

    This is a placeholder that delegates to the existing BrushMatcher
    for Phase 1 development. It will be replaced with the full scoring
    system in subsequent phases.
    """

    def __init__(self, **kwargs):
        """
        Initialize the scoring matcher.

        Args:
            **kwargs: Arguments passed to the underlying BrushMatcher.
        """
        # For now, delegate to the existing BrushMatcher
        self._matcher = BrushMatcher(**kwargs)

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match a brush string using the scoring system.

        Args:
            value: The brush string to match.

        Returns:
            MatchResult or None if no match found.
        """
        # For now, delegate to the existing matcher
        return self._matcher.match(value)

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics.
        """
        # For now, delegate to the existing matcher
        return self._matcher.get_cache_stats()
