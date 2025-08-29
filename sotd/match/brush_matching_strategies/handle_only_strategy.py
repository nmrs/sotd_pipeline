from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.handle_matcher import HandleMatcher
from sotd.match.types import MatchResult, create_match_result


class HandleOnlyStrategy(BaseBrushMatchingStrategy):
    """
    Strategy for matching handle-only input (e.g., "Chisel and Hound Padauk Wood handle").

    This strategy extracts handle component from unified strategy result and creates
    handle-only structure without re-running matching logic.
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
                    # Create structure compatible with existing system
                    matched_data = {
                        "brand": None,
                        "model": None,
                        "handle": {
                            "brand": handle_data.get("brand"),
                            "model": handle_data.get("model"),
                            "source_text": value,
                            "_matched_by": "HandleOnlyStrategy",
                            "_pattern": handle_data.get("_pattern", "handle_only"),
                        },
                        "knot": {
                            "brand": None,
                            "model": None,
                            "fiber": None,
                            "knot_size_mm": None,
                            "source_text": value,
                            "_matched_by": "HandleOnlyStrategy",
                            "_pattern": "handle_only",
                        },
                        "_matched_by_strategy": "handle_only",
                        "_pattern_used": handle_data.get("_pattern", "handle_only"),
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
            # Create structure compatible with existing system
            matched_data = {
                "brand": None,
                "model": None,
                "handle": {
                    "brand": handle_match.get("handle_maker"),
                    "model": handle_match.get("handle_model"),
                    "source_text": value,
                    "_matched_by": "HandleOnlyStrategy",
                    "_pattern": handle_match.get("_pattern_used", "handle_only"),
                },
                "knot": {
                    "brand": None,
                    "model": None,
                    "fiber": None,
                    "knot_size_mm": None,
                    "source_text": value,
                    "_matched_by": "HandleOnlyStrategy",
                    "_pattern": "handle_only",
                },
                "_matched_by_strategy": "handle_only",
                "_pattern_used": handle_match.get("_pattern_used", "handle_only"),
            }

            return create_match_result(
                original=value,
                matched=matched_data,
                match_type="handle_only",
                pattern=handle_match.get("_pattern_used", "handle_only"),
                strategy="handle_only",
            )

        return None
