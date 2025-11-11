from typing import Optional

from sotd.match.types import MatchResult, create_match_result

from ...handle_matcher import HandleMatcher
from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)


class HandleComponentStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for extracting handle components from brush input.

    This strategy extracts handle component from unified strategy result and creates
    handle component data without re-running matching logic. Works with both
    handle-only input and composite brushes.
    """

    def __init__(self, handle_matcher: HandleMatcher):
        self.handle_matcher = handle_matcher

    def match(self, value: str, cached_results: Optional[dict] = None) -> Optional[MatchResult]:
        """
        Attempt to match the input as a handle-only component.

        Args:
            value: The input string to match
            cached_results: Optional cached results from other strategies

        Returns:
            MatchResult with handle populated, knot null, or None if no match
        """
        if not value or not value.strip():
            return None

        # Try to use cached unified result first
        if cached_results and "full_input_component_matching_result" in cached_results:
            unified_result = cached_results["full_input_component_matching_result"]
            if unified_result and unified_result.matched:
                # Extract handle component from unified result
                handle_data = unified_result.matched.get("handle", {})
                if handle_data and handle_data.get("brand"):
                    # Return only component-specific data, let parent strategies handle structure
                    matched_data = {
                        "handle_maker": handle_data.get("brand"),
                        "handle_model": handle_data.get("model"),
                        "source_text": value,
                        "_matched_by": "HandleComponentStrategy",
                        "_pattern": handle_data.get("_pattern", "handle_only"),
                    }

                    return create_match_result(
                        original=value,
                        matched=matched_data,
                        match_type="handle_only",
                        pattern=handle_data.get("_pattern", "handle_only"),
                        strategy="handle_only",
                    )

        # Fallback to original logic if no cached unified result
        # Try to match as a handle using HandleMatcher
        handle_match = self.handle_matcher.match_handle_maker(value)

        if handle_match and handle_match.get("handle_maker"):
            # Return only component-specific data, let parent strategies handle structure
            matched_data = {
                "handle_maker": handle_match.get("handle_maker"),
                "handle_model": handle_match.get("handle_model"),
                "source_text": value,
                "_matched_by": "HandleComponentStrategy",
                "_pattern": handle_match.get("_pattern_used", "handle_only"),
            }

            return create_match_result(
                original=value,
                matched=matched_data,
                match_type="handle_only",
                pattern=handle_match.get("_pattern_used", "handle_only"),
                strategy="handle_only",
            )

        return None
