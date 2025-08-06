"""
Entry point for brush matching that chooses between old and new systems.

This module provides a unified interface for brush matching that can switch
between the legacy BrushMatcher and the new BrushScoringMatcher based on
configuration.
"""

from typing import Optional

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import MatchResult


class BrushMatcherEntryPoint:
    """
    Entry point that chooses between old and new brush matching systems.

    This class provides a unified interface for brush matching that can switch
    between the legacy BrushMatcher and the new BrushScoringMatcher based on
    the use_scoring_system flag.
    """

    def __init__(self, use_scoring_system: bool = False, **kwargs):
        """
        Initialize the entry point with the specified brush matching system.

        Args:
            use_scoring_system: If True, use the new BrushScoringMatcher.
                               If False, use the legacy BrushMatcher.
            **kwargs: Additional arguments passed to the selected matcher.
        """
        self.use_scoring_system = use_scoring_system

        if use_scoring_system:
            # Import here to avoid circular imports
            from sotd.match.scoring_brush_matcher import BrushScoringMatcher

            self.matcher = BrushScoringMatcher(**kwargs)
        else:
            self.matcher = BrushMatcher(**kwargs)

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match a brush string using the selected system.

        Args:
            value: The brush string to match.

        Returns:
            MatchResult or None if no match found.
        """
        return self.matcher.match(value)

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics from the selected system.

        Returns:
            Dictionary containing cache statistics.
        """
        return self.matcher.get_cache_stats()

    def get_system_name(self) -> str:
        """
        Get the name of the currently active system.

        Returns:
            "legacy" for BrushMatcher, "scoring" for BrushScoringMatcher.
        """
        return "scoring" if self.use_scoring_system else "legacy"
