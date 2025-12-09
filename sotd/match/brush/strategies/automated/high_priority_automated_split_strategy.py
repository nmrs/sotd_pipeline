#!/usr/bin/env python3
"""HighPriorityAutomatedSplitStrategy for Phase 3.4 high priority automated split breakdown.

This strategy wraps the legacy system's high_priority_automated_split logic
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.types import MatchResult

from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)


class HighPriorityAutomatedSplitStrategy(BaseBrushMatchingStrategy):
    """Strategy that wraps legacy high_priority_automated_split logic."""

    def __init__(self, legacy_matcher, scoring_config):
        """
        Initialize high priority automated split strategy.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
            scoring_config: BrushScoringConfig instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher
        self.scoring_config = scoring_config
        self.strategy_name = "high_priority_automated_split"

    def match(self, value: str, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """
        Try to match using legacy high_priority_automated_split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if successful split and component matching, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use the legacy system's exact logic
            result = self.legacy_matcher._match_high_priority_automated_split(value)
            if result:
                result.strategy = self.strategy_name
            return result

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"High priority automated split matching failed for '{value}': {e}")
