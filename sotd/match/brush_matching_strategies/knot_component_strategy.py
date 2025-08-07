#!/usr/bin/env python3
"""KnotComponentStrategy for Phase 3.3 dual component breakdown."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class KnotComponentStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching knot components only (partial result)."""

    def __init__(self, knot_matcher):
        """
        Initialize knot component strategy.

        Args:
            knot_matcher: KnotMatcher instance to use for knot matching
        """
        super().__init__()
        self.knot_matcher = knot_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Try to match knot component in the input string.

        Args:
            value: The brush string to match

        Returns:
            MatchResult with knot information only (partial result) if found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use KnotMatcher to find knot component
            knot_match = self.knot_matcher.match(value)

            if knot_match and knot_match.matched:
                # Create partial result with knot information only
                matched_data = {
                    "brand": knot_match.matched.get("brand"),
                    "model": knot_match.matched.get("model"),
                    "fiber": knot_match.matched.get("fiber"),
                    "knot_size_mm": knot_match.matched.get("knot_size_mm"),
                    "_matched_by": "KnotMatcher",
                    "_pattern": knot_match.pattern or "unknown",
                    "_source_text": value,
                }

                return MatchResult(
                    original=value,
                    matched=matched_data,
                    match_type="knot_component",
                    pattern=knot_match.pattern or "unknown",
                    strategy="knot_component",
                )

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Knot component matching failed for '{value}': {e}")
