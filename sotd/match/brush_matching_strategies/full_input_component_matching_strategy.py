#!/usr/bin/env python3
"""Unified component matching strategy that handles both dual and single component matches."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class FullInputComponentMatchingStrategy(BaseBrushMatchingStrategy):
    """
    Unified strategy for component matching that handles both dual and single component scenarios.

    This strategy runs HandleMatcher and KnotMatcher once and combines their results:
    - If both match: Creates dual component result (score 65)
    - If only one matches: Creates single component result (score 50)
    - If neither matches: Returns None
    """

    def __init__(self, handle_matcher, knot_matcher, legacy_matcher):
        """
        Initialize the unified component matching strategy.

        Args:
            handle_matcher: HandleMatcher instance for handle matching
            knot_matcher: KnotMatcher instance for knot matching
            legacy_matcher: Legacy BrushMatcher instance for result creation
        """
        super().__init__()
        self.handle_matcher = handle_matcher
        self.knot_matcher = knot_matcher
        self.legacy_matcher = legacy_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match a brush string using unified component matching logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Run both matchers once
        handle_result = None
        knot_result = None

        try:
            handle_result = self.handle_matcher.match_handle_maker(value)
        except Exception:
            # Handle matcher failed, continue with None
            pass

        try:
            knot_result = self.knot_matcher.match(value)
        except Exception:
            # Knot matcher failed, continue with None
            pass

        # Determine match type and create result
        if handle_result and knot_result:
            # Both matched - dual component
            result = self.legacy_matcher.create_dual_component_result(
                handle_result, knot_result, value, "dual_component"
            )
            if result:
                result.strategy = "dual_component"  # Will get base score 65
                result.match_type = "composite"
            return result
        elif handle_result or knot_result:
            # Only one matched - single component
            result = self.legacy_matcher.create_single_component_result(
                handle_result, knot_result, value, "single_component_fallback"
            )
            if result:
                result.strategy = "single_component_fallback"  # Will get base score 50
                result.match_type = "single_component"
            return result
        else:
            # Neither matched
            return None
