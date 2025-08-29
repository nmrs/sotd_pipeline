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

    def __init__(self, catalogs, scoring_config, handle_matcher, knot_matcher):
        """
        Initialize automated split strategy.

        Args:
            catalogs: Dictionary containing all catalog data
            scoring_config: BrushScoringConfig instance
            handle_matcher: HandleMatcher instance for matching handle components
            knot_matcher: KnotMatcher instance for matching knot components
        """
        super().__init__()
        self.catalogs = catalogs
        self.scoring_config = scoring_config
        self.handle_matcher = handle_matcher
        self.knot_matcher = knot_matcher
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
                result.strategy = "automated_split"
                return result

            # Then try medium priority splitting
            result = self._try_medium_priority_split(value)
            if result:
                # Mark as medium priority (no modifier)
                result.strategy = "automated_split"
                return result

            return None

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Automated split matching failed for '{value}': {e}")

    def _try_high_priority_split(self, value: str) -> Optional[MatchResult]:
        """Try splitting using high priority delimiters."""
        # Use the new system's logic for high priority
        return self._match_high_priority_automated_split(value)

    def _try_medium_priority_split(self, value: str) -> Optional[MatchResult]:
        """Try splitting using medium priority delimiters."""
        # Use the new system's logic for medium priority
        return self._match_medium_priority_automated_split(value)

    def _match_high_priority_automated_split(self, value: str) -> Optional[MatchResult]:
        """
        Match using high priority automated split logic.

        This method implements the high priority split logic directly,
        replacing the dependency on the legacy matcher.
        """
        # High-reliability delimiters (always trigger splitting with simple logic)
        high_reliability_delimiters = [" w/ ", " w/", " with "]
        # Handle-primary delimiters (first part is handle)
        handle_primary_delimiters = [" in "]

        # Always check for ' w/ ' and ' with ' first to avoid misinterpreting 'w/' as '/'
        # These delimiters use smart splitting to determine handle vs knot based on content
        for delimiter in high_reliability_delimiters:
            if delimiter in value:
                handle, knot = self._split_by_delimiter_smart(value, delimiter)
                if handle and knot:
                    return self._create_split_result(handle, knot, value, "high")

        # Check handle-primary delimiters (first part is knot, second part is handle)
        for delimiter in handle_primary_delimiters:
            if delimiter in value:
                handle, knot = self._split_by_delimiter_positional(value, delimiter)
                if handle and knot:
                    return self._create_split_result(handle, knot, value, "high")

        return None

    def _match_medium_priority_automated_split(self, value: str) -> Optional[MatchResult]:
        """
        Match using medium priority automated split logic.

        This method implements the medium priority split logic directly,
        replacing the dependency on the legacy matcher.
        """
        # Medium-reliability delimiters (need smart analysis)
        medium_reliability_delimiters = [" - ", " + "]

        # Check medium-reliability delimiters (use smart analysis)
        for delimiter in medium_reliability_delimiters:
            if delimiter in value:
                handle, knot = self._split_by_delimiter_smart(value, delimiter)
                if handle and knot:
                    return self._create_split_result(handle, knot, value, "medium")

        return None

    def _split_by_delimiter_smart(
        self, text: str, delimiter: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Split text using smart analysis to determine handle vs knot."""
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if part1 and part2:
                # Simple heuristic: assume first part is handle, second is knot
                # This can be enhanced with more sophisticated logic later
                return part1, part2
        return None, None

    def _split_by_delimiter_positional(
        self, text: str, delimiter: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Positional splitting for delimiters."""
        parts = text.split(delimiter, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if part1 and part2:
                if delimiter == " in ":
                    # For "in" delimiter: first part = knot, second part = handle
                    return part2, part1  # handle, knot
                else:
                    # For other delimiters: first part = handle, second part = knot
                    return part1, part2  # handle, knot
        return None, None

    def _create_split_result(
        self, handle: str, knot: str, original_value: str, priority: str
    ) -> MatchResult:
        """Create a MatchResult for a split brush."""
        # Use the handle and knot matchers to match the split parts
        handle_result = self.handle_matcher.match(handle)
        knot_result = self.knot_matcher.match(knot)

        # Create a basic match result structure
        result = MatchResult(
            original=original_value,
            normalized=original_value.lower().strip(),
            matched={
                "handle_text": handle,
                "knot_text": knot,
                "split_priority": priority,
                "_delimiter_priority": priority,
                "high_priority_delimiter": priority == "high",
                "handle": {
                    "brand": (
                        handle_result.matched.get("handle_maker") if handle_result.matched else None
                    ),
                    "model": (
                        handle_result.matched.get("handle_model") if handle_result.matched else None
                    ),
                    "source_text": handle,
                    "_matched_by": "automated_split",
                    "_pattern": "unknown",
                    "priority": getattr(handle_result, "priority", None),
                },
                "knot": {
                    "brand": (knot_result.matched.get("brand") if knot_result.matched else None),
                    "model": (knot_result.matched.get("model") if knot_result.matched else None),
                    "fiber": knot_result.matched.get("fiber") if knot_result.matched else None,
                    "knot_size_mm": (
                        knot_result.matched.get("knot_size_mm") if knot_result.matched else None
                    ),
                    "source_text": knot,
                    "_matched_by": "automated_split",
                    "_pattern": "unknown",
                    "priority": getattr(knot_result, "priority", None),
                },
            },
            match_type="split_brush",
            strategy="automated_split",
        )

        return result

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
