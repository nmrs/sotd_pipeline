from typing import Optional

from sotd.match.types import MatchResult, create_match_result

from ...knot_matcher import KnotMatcher
from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)


class KnotComponentStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for extracting knot components from brush input.

    This strategy extracts knot component from unified strategy result and creates
    knot component data without re-running matching logic. Works with both
    knot-only input and composite brushes.
    """

    def __init__(self, knot_matcher: KnotMatcher):
        self.knot_matcher = knot_matcher

    def match(
        self,
        value: str,
        cached_results: Optional[dict] = None,
        unified_result: Optional[MatchResult] = None,
    ) -> Optional[MatchResult]:
        """
        Attempt to match the input as a knot-only component.

        Args:
            value: The input string to match
            cached_results: Optional cached results from other strategies
            unified_result: Result from unified strategy (if available) to reuse (legacy parameter)

        Returns:
            MatchResult with knot populated from unified result, handle null,
            or None if no match
        """
        if not value or not value.strip():
            return None

        # Try to use cached unified result first
        if cached_results and "full_input_component_matching_result" in cached_results:
            unified_result = cached_results["full_input_component_matching_result"]

        # If we have a unified result, extract knot component from it
        if unified_result and unified_result.matched:
            # Extract knot information from unified result
            knot_brand = unified_result.matched.get("knot", {}).get("brand")
            knot_model = unified_result.matched.get("knot", {}).get("model")
            knot_fiber = unified_result.matched.get("knot", {}).get("fiber")
            knot_size = unified_result.matched.get("knot", {}).get("knot_size_mm")
            knot_pattern = unified_result.matched.get("knot", {}).get("_pattern")

            if knot_brand and knot_model:
                # Return only component-specific data, let parent strategies handle structure
                matched_data = {
                    "brand": knot_brand,
                    "model": knot_model,
                    "fiber": knot_fiber,
                    "knot_size_mm": knot_size,
                    "source_text": value,
                    "_matched_by": "KnotComponentStrategy",
                    "_pattern": knot_pattern or "knot_only",
                }

                return create_match_result(
                    original=value,
                    matched=matched_data,
                    match_type="knot_only",
                    pattern=knot_pattern or "knot_only",
                    strategy="knot_only",
                )

        # Fallback: try to match as a knot using all knot strategies
        best_match = None

        for strategy in self.knot_matcher.strategies:
            try:
                result = strategy.match(value)
                if result and result.matched:
                    # Use the first valid match as fallback
                    best_match = result
                    break
            except Exception:
                # Continue to next strategy if one fails
                continue

        if best_match and best_match.matched:
            # Return only component-specific data, let parent strategies handle structure
            matched_data = {
                "brand": best_match.matched.get("brand"),
                "model": best_match.matched.get("model"),
                "fiber": best_match.matched.get("fiber"),
                "knot_size_mm": best_match.matched.get("knot_size_mm"),
                "source_text": value,
                "_matched_by": "KnotComponentStrategy",
                "_pattern": best_match.pattern or "knot_only",
            }

            return create_match_result(
                original=value,
                matched=matched_data,
                match_type="knot_only",
                pattern=best_match.pattern or "knot_only",
                strategy="knot_only",
            )

        return None
