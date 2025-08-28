"""
Correct Matches Wrapper Strategies.

These strategies implement correct matches functionality directly
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class CorrectCompleteBrushWrapperStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching correct complete brush patterns."""

    def __init__(self, correct_matches_data: dict):
        """
        Initialize the strategy with correct matches data.

        Args:
            correct_matches_data: Dictionary containing correct complete brush matches
        """
        super().__init__()
        self.correct_matches_data = correct_matches_data or {}

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using correct complete brush logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Check for exact match in correct matches (case-insensitive)
        normalized_value = value.lower().strip()
        exact_match = self.correct_matches_data.get(normalized_value)
        
        if exact_match:
            # Create match result
            matched_data = {
                "brand": exact_match.get("brand"),
                "model": exact_match.get("model"),
                "fiber": exact_match.get("fiber"),
                "knot_size_mm": exact_match.get("knot_size_mm"),
                "handle_maker": exact_match.get("handle_maker"),
                "source_text": value,
                "_matched_by": "CorrectCompleteBrushWrapperStrategy",
                "_pattern": "exact_match"
            }
            
            return MatchResult(
                original=value,
                matched=matched_data,
                match_type="exact",
                pattern="exact_match"
            )

        return None


class CorrectSplitBrushWrapperStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching correct split brush patterns."""

    def __init__(self, correct_matches_data: dict):
        """
        Initialize the strategy with correct matches data.

        Args:
            correct_matches_data: Dictionary containing correct split brush matches
        """
        super().__init__()
        self.correct_matches_data = correct_matches_data or {}

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using correct split brush logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Check for exact match in correct matches (case-insensitive)
        normalized_value = value.lower().strip()
        exact_match = self.correct_matches_data.get(normalized_value)
        
        if exact_match:
            # Create match result
            matched_data = {
                "brand": exact_match.get("brand"),
                "model": exact_match.get("model"),
                "fiber": exact_match.get("fiber"),
                "knot_size_mm": exact_match.get("knot_size_mm"),
                "handle_maker": exact_match.get("handle_maker"),
                "source_text": value,
                "_matched_by": "CorrectSplitBrushWrapperStrategy",
                "_pattern": "exact_match"
            }
            
            return MatchResult(
                original=value,
                matched=matched_data,
                match_type="exact",
                pattern="exact_match"
            )

        return None
