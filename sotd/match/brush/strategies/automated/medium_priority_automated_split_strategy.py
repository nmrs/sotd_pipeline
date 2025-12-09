#!/usr/bin/env python3
"""MediumPriorityAutomatedSplitStrategy for Phase 3.5 medium priority automated split breakdown.

This strategy wraps the legacy system's medium_priority_automated_split logic
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.types import MatchResult

from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)


class MediumPriorityAutomatedSplitStrategy(BaseBrushMatchingStrategy):
    """Strategy that wraps legacy medium_priority_automated_split logic."""

    def __init__(self, legacy_matcher, scoring_config):
        """
        Initialize medium priority automated split strategy.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
            scoring_config: BrushScoringConfig instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher
        self.scoring_config = scoring_config
        self.strategy_name = "medium_priority_automated_split"

    def match(self, value: str, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """
        Try to match using legacy medium_priority_automated_split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if successful split and component matching, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use the legacy system's exact logic
            result = self.legacy_matcher._match_medium_priority_automated_split(value)
            if result:
                result.strategy = self.strategy_name
            return result

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Medium priority automated split matching failed for '{value}': {e}")
