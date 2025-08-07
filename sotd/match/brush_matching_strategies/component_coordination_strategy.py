#!/usr/bin/env python3
"""ComponentCoordinationStrategy for Phase 3.3 dual component breakdown."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class ComponentCoordinationStrategy(BaseBrushMatchingStrategy):
    """Strategy for coordinating handle and knot components into complete composite brush result."""

    def __init__(self, handle_matcher, knot_matcher):
        """
        Initialize component coordination strategy.

        Args:
            handle_matcher: HandleMatcher instance to use for handle matching
            knot_matcher: KnotMatcher instance to use for knot matching
        """
        super().__init__()
        self.handle_matcher = handle_matcher
        self.knot_matcher = knot_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Try to match both handle and knot components in the input string.

        Args:
            value: The brush string to match

        Returns:
            MatchResult with complete composite brush data if both handle and knot found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use HandleMatcher to find handle component
            handle_match = self.handle_matcher.match_handle_maker(value)

            # Use KnotMatcher to find knot component
            knot_match = self.knot_matcher.match(value)

            # Both handle and knot must be found for coordination
            if (
                handle_match
                and handle_match.get("handle_maker")
                and knot_match
                and knot_match.matched
            ):
                # Create complete composite result
                matched_data = {
                    "brand": handle_match.get("handle_maker"),
                    "model": handle_match.get("handle_model"),
                    "_matched_by": "HandleMatcher+KnotMatcher",
                    "_pattern": handle_match.get("_pattern_used") or "unknown",
                    "_source_text": handle_match.get("_source_text", value),
                }

                # Create handle section
                matched_data["handle"] = {
                    "brand": handle_match.get("handle_maker"),
                    "model": handle_match.get("handle_model"),
                    "_matched_by": handle_match.get("_matched_by", "HandleMatcher"),
                    "_pattern": handle_match.get("_pattern_used") or "unknown",
                    "_source_text": handle_match.get("_source_text", value),
                }

                # Create knot section
                matched_data["knot"] = {
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
                    match_type="component_coordination",
                    pattern=handle_match.get("_pattern_used", "unknown"),
                    strategy="component_coordination",
                )

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Component coordination failed for '{value}': {e}")
