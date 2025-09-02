"""
Knot size fallback strategy for brush matching.

This strategy attempts to match unknown knots by extracting size information
using the knot_size_utils module. It's used as a fallback when other
strategies fail to match and no fiber is detected.
"""

from typing import Optional

from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from ..utils.knot_size_utils import parse_knot_size
from sotd.match.types import MatchResult, create_match_result


class KnotSizeFallbackStrategy(BaseBrushMatchingStrategy):
    """
    Fallback strategy that matches unknown knots by extracting size information.

    This strategy uses knot_size_utils.parse_knot_size() to extract size
    information from unknown knot text. If a size is detected, it returns
    a MatchResult with brand="Unspecified" and model="{size}mm".
    """

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Attempt to match the given string by extracting size information.

        Args:
            value: The knot text to match

        Returns:
            MatchResult if size is detected, None otherwise
        """
        if not value or not value.strip():
            return None

        # Use knot_size_utils to extract size
        detected_size = parse_knot_size(value)

        if not detected_size:
            return None

        # Create match result with detected size
        # Format size to remove decimal for whole numbers (e.g., 26.0 -> 26)
        formatted_size = int(detected_size) if detected_size.is_integer() else detected_size
        matched_data = {
            "brand": None,
            "model": f"{formatted_size}mm",
            "fiber": None,
            "knot_size_mm": detected_size,
            "_matched_by_strategy": "KnotSizeFallbackStrategy",
            "_pattern_used": "size_detection",
        }

        return create_match_result(
            original=value,
            matched=matched_data,
            match_type="size_fallback",
            pattern="size_detection",
        )
