#!/usr/bin/env python3
"""HandleComponentStrategy for Phase 3.3 dual component breakdown."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class HandleComponentStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching handle components only (partial result)."""

    def __init__(self, handle_matcher):
        """
        Initialize handle component strategy.

        Args:
            handle_matcher: HandleMatcher instance to use for handle matching
        """
        super().__init__()
        self.handle_matcher = handle_matcher

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Try to match handle component in the input string.

        Args:
            value: The brush string to match

        Returns:
            MatchResult with handle information only (partial result) if found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use HandleMatcher to find handle component
            handle_match = self.handle_matcher.match_handle_maker(value)

            if handle_match and handle_match.get("handle_maker"):
                # Create partial result with handle information only
                matched_data = {
                    "handle_maker": handle_match.get("handle_maker"),
                    "handle_model": handle_match.get("handle_model"),
                    "_matched_by": handle_match.get("_matched_by", "HandleMatcher"),
                    "_pattern": handle_match.get("_pattern_used", "unknown"),
                    "_source_text": value,
                }

                return MatchResult(
                    original=value,
                    matched=matched_data,
                    match_type="handle_component",
                    pattern=handle_match.get("_pattern_used", "unknown"),
                    strategy="handle_component",
                )

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Handle component matching failed for '{value}': {e}")
