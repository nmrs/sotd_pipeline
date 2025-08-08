#!/usr/bin/env python3
"""AutomatedSplitStrategy for unified high/medium priority split handling.

This strategy merges the functionality of HighPriorityAutomatedSplitStrategy
and MediumPriorityAutomatedSplitStrategy into a single strategy that uses
scoring modifiers to differentiate between high and medium priority delimiters.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class AutomatedSplitStrategy(BaseBrushMatchingStrategy):
    """Unified strategy for automated split handling with priority-based scoring."""

    def __init__(self, legacy_matcher, scoring_config):
        """
        Initialize automated split strategy.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
            scoring_config: BrushScoringConfig instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher
        self.scoring_config = scoring_config
        self.strategy_name = "automated_split"

        # Define delimiter priorities based on BrushSplitter logic
        self.high_priority_delimiters = [" w/ ", " w/", " with ", " in "]
        self.medium_priority_delimiters = [" - ", " + "]

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Try to match using unified automated split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if successful split and component matching, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # First try high priority splitting
            result = self._try_high_priority_split(value)
            if result:
                # Mark as high priority for scoring modifier
                result.high_priority_delimiter = True
                result.strategy = "automated_split"
                # Store which delimiter type was used for scoring
                result._delimiter_priority = "high"
                return result

            # Then try medium priority splitting
            result = self._try_medium_priority_split(value)
            if result:
                # Mark as medium priority (no modifier)
                result.high_priority_delimiter = False
                result.strategy = "automated_split"
                # Store which delimiter type was used for scoring
                result._delimiter_priority = "medium"
                return result

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Automated split matching failed for '{value}': {e}")

    def _try_high_priority_split(self, value: str) -> Optional[MatchResult]:
        """Try splitting using high priority delimiters."""
        # Use the legacy system's exact logic for high priority
        return self.legacy_matcher._match_high_priority_automated_split(value)

    def _try_medium_priority_split(self, value: str) -> Optional[MatchResult]:
        """Try splitting using medium priority delimiters."""
        # Use the legacy system's exact logic for medium priority
        return self.legacy_matcher._match_medium_priority_automated_split(value)

    def _detect_delimiter_priority(self, value: str) -> str:
        """
        Detect whether the string contains high or medium priority delimiters.

        Args:
            value: The brush string to analyze

        Returns:
            "high" if contains high priority delimiters, "medium" if medium, "none" if neither
        """
        # Check for high priority delimiters first
        for delimiter in self.high_priority_delimiters:
            if delimiter in value:
                return "high"

        # Check for medium priority delimiters
        for delimiter in self.medium_priority_delimiters:
            if delimiter in value:
                return "medium"

        return "none"
