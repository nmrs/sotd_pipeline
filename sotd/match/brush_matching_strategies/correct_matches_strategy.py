"""
Strategy for matching brushes against correct_matches.yaml.

This strategy uses CorrectMatchesChecker internally to avoid duplication
of search logic while maintaining the strategy pattern interface.
"""

from typing import Optional
from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult
from sotd.match.correct_matches import CorrectMatchesChecker


class CorrectMatchesStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for matching against correct_matches.yaml.

    Uses CorrectMatchesChecker internally to avoid duplication of search logic.
    """

    def __init__(self, correct_matches_data: dict):
        """
        Initialize with correct matches data.

        Args:
            correct_matches_data: The loaded correct_matches.yaml data
        """
        self.checker = CorrectMatchesChecker(correct_matches_data)

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match the input value against correct_matches.yaml.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if found, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        # Use the utility class to check for matches
        match_data = self.checker.check(value)
        if match_data:
            # Convert CorrectMatchData to MatchResult format
            return self._convert_to_match_result(value, match_data)

        return None

    def _convert_to_match_result(self, value: str, match_data) -> MatchResult:
        """
        Convert CorrectMatchData to MatchResult format.

        Args:
            value: Original input string
            match_data: Result from CorrectMatchesChecker

        Returns:
            MatchResult in the expected format
        """
        if match_data.match_type == "brush_section":
            # Simple brush match
            matched_data = {
                "brand": match_data.brand,
                "model": match_data.model,
                "fiber": None,  # Not available in correct_matches structure
                "knot_size_mm": None,  # Not available in correct_matches structure
                "handle_maker": None,  # Not available in correct_matches structure
                "source_text": value,
                "_matched_by": "CorrectMatchesStrategy",
                "_pattern": "exact_match",
                "strategy": "correct_matches",
            }
        elif match_data.match_type == "handle_knot_section":
            # Handle/knot match
            matched_data = {
                "brand": match_data.knot_info.get("brand") if match_data.knot_info else None,
                "model": match_data.knot_info.get("model") if match_data.knot_info else None,
                "fiber": match_data.knot_info.get("fiber") if match_data.knot_info else None,
                "knot_size_mm": (
                    match_data.knot_info.get("knot_size_mm") if match_data.knot_info else None
                ),
                "handle_maker": match_data.handle_maker,
                "source_text": value,
                "_matched_by": "CorrectMatchesStrategy",
                "_pattern": "exact_match",
                "strategy": "correct_matches",
            }
        else:
            # Fallback for unknown match types
            matched_data = {
                "brand": None,
                "model": None,
                "fiber": None,
                "knot_size_mm": None,
                "handle_maker": None,
                "source_text": value,
                "_matched_by": "CorrectMatchesStrategy",
                "_pattern": "exact_match",
                "strategy": "correct_matches",
            }

        return MatchResult(
            original=value,
            matched=matched_data,
            match_type="exact",
            pattern="exact_match",
        )
