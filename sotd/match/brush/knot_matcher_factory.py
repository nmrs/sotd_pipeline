"""KnotMatcherFactory for creating knot strategies with explicit priority order.

This factory encapsulates the creation of knot matching strategies, making the
priority order explicit and testable. It reduces complexity in BrushMatcher
by extracting knot strategy creation logic.
"""

from typing import List

from .strategies.fallback.fiber_fallback_strategy import (
    FiberFallbackStrategy,
)
from .strategies.fallback.knot_size_fallback_strategy import (
    KnotSizeFallbackStrategy,
)
from .strategies.known.known_knot_strategy import (
    KnownKnotMatchingStrategy,
)
from .strategies.other_knot_strategy import (
    OtherKnotMatchingStrategy,
)


class KnotMatcherFactory:
    """Factory for creating knot matching strategies with explicit priority order."""

    @staticmethod
    def create_knot_strategies(catalogs: dict) -> List:
        """
        Create knot strategies with explicit priority order.

        Priority order (highest to lowest):
        1. KnownKnotMatchingStrategy - Matches against known knot catalog
        2. OtherKnotMatchingStrategy - Matches against other knot catalog
        3. FiberFallbackStrategy - Fallback for fiber-only matching
        4. KnotSizeFallbackStrategy - Fallback for size-only matching

        Args:
            catalogs: Dictionary containing catalog data, including knots data

        Returns:
            List of knot matching strategies in priority order
        """
        # Safely access knots catalog data with default empty dictionaries
        knots_data = catalogs.get("knots", {})
        known_knots = knots_data.get("known_knots", {})
        other_knots = knots_data.get("other_knots", {})

        return [
            KnownKnotMatchingStrategy(known_knots),
            OtherKnotMatchingStrategy(other_knots),
            FiberFallbackStrategy(),
            KnotSizeFallbackStrategy(),
        ]

    @staticmethod
    def get_strategy_priority_order() -> List[str]:
        """
        Get the explicit priority order of knot strategies.

        Returns:
            List of strategy class names in priority order
        """
        return [
            "KnownKnotMatchingStrategy",
            "OtherKnotMatchingStrategy",
            "FiberFallbackStrategy",
            "KnotSizeFallbackStrategy",
        ]
