"""
Complete Brush Wrapper Strategy.

This strategy implements complete brush functionality directly
to integrate with the scoring system architecture.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class CompleteBrushWrapperStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching complete brush patterns."""

    def __init__(self, catalog_data: dict):
        """
        Initialize the strategy with catalog data.

        Args:
            catalog_data: Dictionary containing brush catalog data
        """
        super().__init__()
        self.catalog_data = catalog_data or {}

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Match using complete brush logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # This strategy is now handled by individual brush strategies
        # (KnownBrushMatchingStrategy, OmegaSemogueBrushMatchingStrategy, etc.)
        # So we return None to let those strategies handle the matching
        return None
