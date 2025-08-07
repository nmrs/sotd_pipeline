#!/usr/bin/env python3
"""Wrapper strategies that reuse legacy system's composite brush methods."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class LegacyDualComponentWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper strategy that uses legacy system's _match_dual_component method."""

    def __init__(self, legacy_matcher):
        """
        Initialize wrapper strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Use legacy system's dual component matching logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_dual_component(value)
        if result and result.matched:
            result.strategy = "dual_component"
            result.match_type = "composite"  # Correct behavior for composite brushes
            return result
        return None


class LegacySingleComponentFallbackWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper strategy that uses legacy system's _match_single_component_fallback method."""

    def __init__(self, legacy_matcher):
        """
        Initialize wrapper strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Use legacy system's single component fallback logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        result = self.legacy_matcher._match_single_component_fallback(value)
        if result and result.matched:
            result.strategy = "single_component_fallback"
            result.match_type = "single_component"
            return result
        return None
