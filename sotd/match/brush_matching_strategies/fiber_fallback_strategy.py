"""
Fiber fallback strategy for brush matching.

This strategy attempts to match unknown knots by detecting fiber types
using the fiber_utils module. It's used as a fallback when other
strategies fail to match.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.types import MatchResult, create_match_result


class FiberFallbackStrategy(BaseBrushMatchingStrategy):
    """
    Fallback strategy that matches unknown knots by detecting fiber types.

    This strategy uses fiber_utils.match_fiber() to detect fiber types in
    unknown knot text. If a fiber is detected, it returns a MatchResult
    with brand="Unspecified" and model=fiber_type.
    """

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Attempt to match the given string by detecting fiber types.

        Args:
            value: The knot text to match

        Returns:
            MatchResult if fiber is detected, None otherwise
        """
        if not value or not value.strip():
            return None

        # Use fiber_utils to detect fiber type
        detected_fiber = match_fiber(value)

        if not detected_fiber:
            return None

        # Create match result with detected fiber
        matched_data = {
            "brand": "Unspecified",
            "model": detected_fiber,
            "fiber": detected_fiber,
            "fiber_strategy": "fiber_fallback",
            "_matched_by_strategy": "FiberFallbackStrategy",
            "_pattern_used": "fiber_detection",
        }

        return create_match_result(
            original=value,
            matched=matched_data,
            match_type="fiber_fallback",
            pattern="fiber_detection",
        )
