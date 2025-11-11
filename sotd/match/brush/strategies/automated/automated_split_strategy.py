#!/usr/bin/env python3
"""AutomatedSplitStrategy for unified high/medium priority split handling.

This strategy merges the functionality of HighPriorityAutomatedSplitStrategy
and MediumPriorityAutomatedSplitStrategy into a single strategy that uses
scoring modifiers to differentiate between high and medium priority delimiters.
"""

import re
from pathlib import Path
from typing import Optional

# ComponentScoreCalculator no longer needed - scoring is handled externally
from sotd.match.types import MatchResult

from ...comparison.splits_loader import BrushSplitsLoader
from ...delimiter_patterns import BrushDelimiterPatterns
from ..base_brush_matching_strategy import (
    BaseMultiResultBrushMatchingStrategy,
)


class AutomatedSplitStrategy(BaseMultiResultBrushMatchingStrategy):
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

        # Initialize BrushSplitsLoader to check should_not_split flag
        self.splits_loader = BrushSplitsLoader(Path("data/brush_splits.yaml"))

        # Define delimiter priorities based on BrushSplitter logic
        self.high_priority_delimiters = BrushDelimiterPatterns.get_high_priority_delimiters()
        self.medium_priority_delimiters = BrushDelimiterPatterns.get_medium_priority_delimiters()

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

        # Check if this brush should not be split (from brush_splits.yaml)
        if self.splits_loader.should_not_split(value):
            # Skip all split strategies if should_not_split is True
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
            raise ValueError(f"Automated split matching failed for '{value}': {e}") from e

    def match_all(self, value: str) -> list[MatchResult]:
        """
        Try to match using all possible automated split combinations.

        Args:
            value: The brush string to match

        Returns:
            List of MatchResult objects for all possible splits, empty list if no splits found
        """
        if not value or not isinstance(value, str):
            return []

        # Check if this brush should not be split (from brush_splits.yaml)
        if self.splits_loader.should_not_split(value):
            # Skip all split strategies if should_not_split is True
            return []

        try:
            all_results = []

            # Get all possible splits regardless of priority
            all_splits = self._get_all_possible_splits(value)

            for split_info in all_splits:
                result = self._create_split_result(
                    split_info["handle"], split_info["knot"], value, split_info["priority"]
                )
                result.strategy = "automated_split"
                all_results.append(result)

            return all_results

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Automated split matching failed for '{value}': {e}") from e

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
        high_reliability_delimiters = BrushDelimiterPatterns.get_smart_splitting_delimiters()
        # Handle-primary delimiters (first part is handle)
        handle_primary_delimiters = BrushDelimiterPatterns.get_positional_splitting_delimiters()

        # Always check for ' w/ ' and ' with ' first to avoid misinterpreting 'w/' as '/'
        # These delimiters use smart splitting to determine handle vs knot based on content
        # Use case-insensitive matching per @match-phase.mdc rules
        for delimiter in high_reliability_delimiters:
            if delimiter.lower() in value.lower():
                handle, knot = self._split_by_delimiter_positional(value, delimiter)
                if handle and knot:
                    return self._create_split_result(handle, knot, value, "high")

        # Check handle-primary delimiters (first part is knot, second part is handle)
        # Use case-insensitive matching per @match-phase.mdc rules
        for delimiter in handle_primary_delimiters:
            if delimiter.lower() in value.lower():
                # Check if the delimiter is preceded by "made" or followed by Reddit references
                delimiter_index = value.find(delimiter)
                before_delimiter = value[:delimiter_index].strip()
                after_delimiter = value[delimiter_index + len(delimiter) :].strip()

                # Skip if before delimiter ends with "made" or after delimiter starts with r/, u/
                if before_delimiter.lower().endswith("made") or after_delimiter.lower().startswith(
                    ("r/", "u/")
                ):
                    continue

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
        medium_reliability_delimiters = [
            d for d in BrushDelimiterPatterns.get_medium_priority_delimiters() if d != "/"
        ]

        # Check medium-reliability delimiters (use smart analysis)
        # Use case-insensitive matching per @match-phase.mdc rules
        for delimiter in medium_reliability_delimiters:
            if delimiter.lower() in value.lower():
                handle, knot = self._split_by_delimiter_positional(value, delimiter)
                if handle and knot:
                    return self._create_split_result(handle, knot, value, "medium")

        # Special handling for "/" as medium-priority delimiter (any spaces, not part of 'w/')
        # But first check if "/" is part of a specification rather than a delimiter
        # Also exclude Reddit references: r/ and u/ (e.g., r/wetshaving, u/username)
        if "/" in value and "w/" not in value.lower():
            # Use regex to split on "/" but avoid splitting "w/" patterns and Reddit references
            # Pattern: (.+?)(?<!w)(?<!r)(?<!u)\s*/\s*(.+)
            # This excludes splitting when "/" follows "w", "r", or "u"
            slash_match = re.search(r"(.+?)(?<!w)(?<!r)(?<!u)\s*/\s*(.+)", value)
            if slash_match:
                part1 = slash_match.group(1).strip()
                part2 = slash_match.group(2).strip()
                if part1 and part2:
                    # Score both parts to determine which is handle vs knot
                    part1_handle_score = self._score_as_handle(part1)
                    part2_handle_score = self._score_as_handle(part2)
                    if part1_handle_score >= part2_handle_score:
                        return self._create_split_result(part1, part2, value, "medium")
                    else:
                        return self._create_split_result(part2, part1, value, "medium")

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
                # Use scoring to determine which part is handle vs knot
                part1_handle_score = self._score_as_handle(part1)
                part2_handle_score = self._score_as_handle(part2)

                if part1_handle_score >= part2_handle_score:
                    return part1, part2  # part1 is handle, part2 is knot
                else:
                    return part2, part1  # part2 is handle, part1 is knot
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
                        handle_result.matched.get("handle_maker")
                        if handle_result and handle_result.matched
                        else None
                    ),
                    "model": (
                        handle_result.matched.get("handle_model")
                        if handle_result and handle_result.matched
                        else None
                    ),
                    "source_text": handle,
                    "_matched_by": "automated_split",
                    "_pattern": (handle_result.pattern if handle_result else "unknown"),
                    "priority": getattr(handle_result, "priority", None),
                },
                "knot": {
                    "brand": (
                        knot_result.matched.get("brand")
                        if knot_result and knot_result.matched
                        else None
                    ),
                    "model": (
                        knot_result.matched.get("model")
                        if knot_result and knot_result.matched
                        else None
                    ),
                    "fiber": (
                        knot_result.matched.get("fiber")
                        if knot_result and knot_result.matched
                        else None
                    ),
                    "knot_size_mm": (
                        knot_result.matched.get("knot_size_mm")
                        if knot_result and knot_result.matched
                        else None
                    ),
                    "source_text": knot,
                    "_matched_by": "automated_split",
                    "_pattern": (knot_result.pattern if knot_result else "unknown"),
                    "priority": getattr(knot_result, "priority", None),
                },
            },
            match_type="split_brush",
            pattern=f"split_on_{priority}_priority_delimiter",
            strategy="automated_split",
        )

        # Component scores are now calculated externally by the scoring engine
        # No need to pre-calculate scores here

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

    def _score_as_handle(self, text: str) -> int:
        """
        Score text as likely being a handle component.

        Higher scores indicate the text is more likely to be a handle.
        Lower scores indicate the text is more likely to be a knot.

        Args:
            text: Text to score

        Returns:
            Score (positive = handle likely, negative = knot likely)
        """
        if not text:
            return 0

        text_lower = text.lower()
        score = 0

        # Strong handle indicators
        if "handle" in text_lower:
            score += 10
        if any(
            word in text_lower for word in ["stock", "custom", "artisan", "turned", "wood", "resin"]
        ):
            score += 2

        # Strong knot indicators (negative score)
        if any(word in text_lower for word in ["badger", "boar", "synthetic", "syn", "nylon"]):
            score -= 8
        if re.search(r"\d+\s*mm", text_lower):
            score -= 6
        if re.search(r"[vV]\d+|[bB]\d+", text_lower):
            score -= 6

        return score

    def _score_as_knot(self, text: str) -> int:
        """
        Score text as likely being a knot component.

        Higher scores indicate the text is more likely to be a knot.
        Lower scores indicate the text is more likely to be a handle.

        Args:
            text: Text to score

        Returns:
            Score (positive = knot likely, negative = handle likely)
        """
        if not text:
            return 0

        text_lower = text.lower()
        score = 0

        # Strong knot indicators (positive score)
        if any(
            word in text_lower for word in ["badger", "boar", "synthetic", "syn", "nylon", "shoat"]
        ):
            score += 8
        if re.search(r"\d+\s*mm", text_lower):
            score += 6
        if re.search(r"[vV]\d+|[bB]\d+", text_lower):
            score += 6

        # Strong handle indicators (negative score)
        if "handle" in text_lower:
            score -= 10
        if any(
            word in text_lower for word in ["stock", "custom", "artisan", "turned", "wood", "resin"]
        ):
            score -= 2

        return score

    def _get_all_possible_splits(self, value: str) -> list[dict]:
        """
        Get all possible split combinations for a given string.

        Args:
            value: The brush string to split

        Returns:
            List of dictionaries containing handle, knot, and priority information
        """
        all_splits = []

        # Find all delimiter positions
        delimiter_positions = []

        # High priority delimiters - use case-insensitive matching per @match-phase.mdc rules
        for delimiter in self.high_priority_delimiters:
            pos = 0
            while True:
                pos = value.lower().find(delimiter.lower(), pos)
                if pos == -1:
                    break
                delimiter_positions.append(
                    {"delimiter": delimiter, "position": pos, "priority": "high"}
                )
                pos += len(delimiter)

        # Medium priority delimiters - use case-insensitive matching per @match-phase.mdc rules
        for delimiter in self.medium_priority_delimiters:
            pos = 0
            while True:
                pos = value.lower().find(delimiter.lower(), pos)
                if pos == -1:
                    break
                delimiter_positions.append(
                    {"delimiter": delimiter, "position": pos, "priority": "medium"}
                )
                pos += len(delimiter)

        # Sort by position to process left to right
        delimiter_positions.sort(key=lambda x: x["position"])

        # Generate all possible splits
        seen_splits = set()  # Track seen splits to avoid duplicates
        for delim_info in delimiter_positions:
            delimiter = delim_info["delimiter"]
            priority = delim_info["priority"]

            # Skip if this delimiter is part of a Reddit reference or "made" context
            if self._should_skip_delimiter(value, delimiter, delim_info["position"]):
                continue

            # Split based on delimiter type
            if BrushDelimiterPatterns.is_smart_splitting_delimiter(delimiter):
                # Smart splitting for these delimiters
                handle, knot = self._split_by_delimiter_smart(value, delimiter)
            elif BrushDelimiterPatterns.is_positional_splitting_delimiter(delimiter):
                # Positional splitting for "in" (knot in handle)
                handle, knot = self._split_by_delimiter_positional(value, delimiter)
            elif delimiter == "/":
                # Special handling for "/" to avoid Reddit references
                handle, knot = self._split_by_slash_delimiter(
                    value, delimiter, delim_info["position"]
                )
            elif delimiter == " (":
                # Special handling for parentheses with content-based scoring
                handle, knot = self._split_by_parentheses(value, delimiter)
            else:
                # Default smart splitting
                handle, knot = self._split_by_delimiter_positional(value, delimiter)

            if handle and knot:
                # Create a unique key for this split to avoid duplicates
                split_key = (handle, knot)
                if split_key not in seen_splits:
                    seen_splits.add(split_key)
                    all_splits.append(
                        {
                            "handle": handle,
                            "knot": knot,
                            "priority": priority,
                            "delimiter": delimiter,
                            "position": delim_info["position"],
                        }
                    )

        return all_splits

    def _should_skip_delimiter(self, value: str, delimiter: str, position: int) -> bool:
        """
        Check if a delimiter should be skipped due to context.

        Args:
            value: The full string
            delimiter: The delimiter to check
            position: Position of the delimiter

        Returns:
            True if delimiter should be skipped, False otherwise
        """
        if delimiter == " in ":
            # Check if preceded by "made" or followed by Reddit references
            before_delimiter = value[:position].strip()
            after_delimiter = value[position + len(delimiter) :].strip()

            if before_delimiter.lower().endswith("made") or after_delimiter.lower().startswith(
                ("r/", "u/")
            ):
                return True

        elif delimiter == "/":
            # Check if it's part of "w/" or Reddit references
            before_delimiter = value[:position].strip()
            if (
                before_delimiter.lower().endswith("w")
                or before_delimiter.lower().endswith("r")
                or before_delimiter.lower().endswith("u")
            ):
                return True

        return False

    def _split_by_slash_delimiter(
        self, value: str, delimiter: str, position: int
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Split by "/" delimiter with special handling for Reddit references.

        Args:
            value: The string to split
            delimiter: The "/" delimiter
            position: Position of the delimiter

        Returns:
            Tuple of (handle, knot) or (None, None) if split is invalid
        """
        part1 = value[:position].strip()
        part2 = value[position + len(delimiter) :].strip()

        if part1 and part2:
            # Score both parts to determine which is handle vs knot
            part1_handle_score = self._score_as_handle(part1)
            part2_handle_score = self._score_as_handle(part2)

            if part1_handle_score >= part2_handle_score:
                return part1, part2  # handle, knot
            else:
                return part2, part1  # handle, knot

        return None, None

    def _split_by_parentheses(
        self, value: str, delimiter: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Split by parentheses delimiter with content-based scoring.

        Args:
            value: The string to split
            delimiter: The " (" delimiter

        Returns:
            Tuple of (handle, knot) or (None, None) if split is invalid
        """
        import re

        # Match pattern: text before '(' and text between '(' and ')'
        match = re.search(r"^(.+?)\s+\(([^)]+)\)", value)
        if not match:
            return None, None

        part1 = match.group(1).strip()  # Outside parentheses
        part2 = match.group(2).strip()  # Inside parentheses

        if not part1 or not part2:
            return None, None

        # Use content-based scoring to determine handle vs knot
        part1_handle_score = self._score_as_handle(part1)
        part1_knot_score = self._score_as_knot(part1)
        part2_handle_score = self._score_as_handle(part2)
        part2_knot_score = self._score_as_knot(part2)

        # Determine best assignment based on scores
        if part1_handle_score > part2_handle_score and part2_knot_score > part1_knot_score:
            return part1, part2  # part1=handle, part2=knot
        elif part2_handle_score > part1_handle_score and part1_knot_score > part2_knot_score:
            return part2, part1  # part2=handle, part1=knot
        else:
            # Tie-breaking: prioritize knot scores
            if part2_knot_score > part1_knot_score:
                return part1, part2
            else:
                return part2, part1
