#!/usr/bin/env python3
"""Wrapper strategies that reuse legacy system's composite brush methods."""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.types import MatchResult


class LegacyDualComponentWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper strategy that uses legacy system's _match_dual_component method."""

    def __init__(self, legacy_matcher):
        """
        Initialize wrapper strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str, cached_results: Optional[dict] = None) -> Optional[MatchResult]:
        """
        Use legacy system's dual component matching logic.

        Args:
            value: The brush string to match
            cached_results: Optional cached results from HandleMatcher and KnotMatcher

        Returns:
            MatchResult or None
        """
        if cached_results and "handle_result" in cached_results and "knot_result" in cached_results:
            # Use cached results to create dual component result
            return self._create_dual_component_from_cached_results(
                value, cached_results["handle_result"], cached_results["knot_result"]
            )
        else:
            # Fall back to legacy method if no cached results
            result = self.legacy_matcher._match_dual_component(value)
            if result and result.matched:
                result.strategy = "dual_component"
                result.match_type = "composite"  # Correct behavior for composite brushes
                return result
            return None

    def _create_dual_component_from_cached_results(
        self, value: str, handle_result: Optional[dict], knot_result: Optional[MatchResult]
    ) -> Optional[MatchResult]:
        """
        Create dual component result from cached HandleMatcher and KnotMatcher results.

        Args:
            value: The brush string to match
            handle_result: Cached HandleMatcher result
            knot_result: Cached KnotMatcher result

        Returns:
            MatchResult or None
        """
        if not handle_result or not knot_result:
            return None

        # Validate that we have both handle and knot matches
        if not self.legacy_matcher._validate_dual_component_match(handle_result, knot_result):
            return None

        # Detect user intent based on component order in original string
        handle_text = handle_result.get("handle_maker", "") if handle_result else ""
        knot_text = (
            knot_result.matched.get("model", "") if knot_result and knot_result.matched else ""
        )
        user_intent = self.legacy_matcher.detect_user_intent(value, handle_text, knot_text)

        # Create dual component result using legacy method
        result = self.legacy_matcher.create_dual_component_result(
            handle_result, knot_result, value, user_intent
        )

        if result:
            result.strategy = "dual_component"
            result.match_type = "composite"

        return result


class LegacySingleComponentFallbackWrapperStrategy(BaseBrushMatchingStrategy):
    """Wrapper strategy that uses legacy system's _match_single_component_fallback method."""

    def __init__(self, legacy_matcher):
        """
        Initialize wrapper strategy with legacy matcher.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher

    def match(self, value: str, cached_results: Optional[dict] = None) -> Optional[MatchResult]:
        """
        Use legacy system's single component fallback logic.

        Args:
            value: The brush string to match
            cached_results: Optional cached results from HandleMatcher and KnotMatcher

        Returns:
            MatchResult or None
        """
        if cached_results and (
            "handle_result" in cached_results or "knot_result" in cached_results
        ):
            # Use cached results to create single component result
            return self._create_single_component_from_cached_results(
                value,
                cached_results.get("handle_result") if cached_results else None,
                cached_results.get("knot_result") if cached_results else None,
            )
        else:
            # Fall back to legacy method if no cached results
            result = self.legacy_matcher._match_single_component_fallback(value)
            if result and result.matched:
                result.strategy = "single_component_fallback"
                result.match_type = "single_component"
                return result
            return None

    def _create_single_component_from_cached_results(
        self, value: str, handle_result: Optional[dict], knot_result: Optional[MatchResult]
    ) -> Optional[MatchResult]:
        """
        Create single component result from cached HandleMatcher and KnotMatcher results.

        Args:
            value: The brush string to match
            handle_result: Cached HandleMatcher result
            knot_result: Cached KnotMatcher result

        Returns:
            MatchResult or None
        """
        from sotd.match.brush_matching_strategies.utils.pattern_utils import score_match_type

        best_match = None
        best_score = -1
        best_match_type = None

        # Score knot result if available
        if knot_result and hasattr(knot_result, "matched") and knot_result.matched:
            knot_score = score_match_type(
                value,
                "knot",
                5,
                knot_matcher=self.legacy_matcher.knot_matcher,
                handle_matcher=self.legacy_matcher.handle_matcher,
            )
            if knot_score > best_score:
                best_score = knot_score
                best_match = knot_result
                best_match_type = "knot"

        # Score handle result if available
        if handle_result and handle_result.get("handle_maker"):
            handle_score = score_match_type(
                value,
                "handle",
                5,
                knot_matcher=self.legacy_matcher.knot_matcher,
                handle_matcher=self.legacy_matcher.handle_matcher,
            )
            if handle_score > best_score:
                best_score = handle_score
                # Create a proper MatchResult-like object for handle match
                from sotd.match.types import create_match_result

                # Get the actual pattern used for handle matching
                handle_pattern = handle_result.get("_pattern_used", "unknown")

                best_match = create_match_result(
                    original=value,
                    matched={
                        "brand": handle_result["handle_maker"],
                        "model": handle_result.get("handle_model"),
                        "source_text": value,
                        "_matched_by": "HandleMatcher",
                        "_pattern": handle_pattern,
                    },
                    match_type="regex",
                    pattern=handle_pattern,
                )
                best_match_type = "handle"

        if best_match:
            # Process the best match using legacy logic
            if best_match_type == "handle":
                # Handle-only match - create composite structure
                matched = {
                    "brand": None,  # Composite brush
                    "model": None,  # Composite brush
                    "handle": {
                        "brand": best_match.matched["brand"],
                        "model": None,
                        "source_text": value,
                        "_matched_by": "HandleMatcher",
                        "_pattern": best_match.pattern,
                    },
                    "knot": {
                        "brand": None,
                        "model": None,
                        "source_text": value,
                        "_matched_by": None,
                        "_pattern": None,
                    },
                }
            else:
                # Knot-only match - create composite structure
                matched = {
                    "brand": None,  # Composite brush
                    "model": None,  # Composite brush
                    "handle": {
                        "brand": None,
                        "model": None,
                        "source_text": value,
                        "_matched_by": None,
                        "_pattern": None,
                    },
                    "knot": {
                        "brand": best_match.matched.get("brand") if best_match.matched else None,
                        "model": best_match.matched.get("model") if best_match.matched else None,
                        "fiber": best_match.matched.get("fiber") if best_match.matched else None,
                        "knot_size_mm": (
                            best_match.matched.get("knot_size_mm") if best_match.matched else None
                        ),
                        "source_text": value,
                        "_matched_by": "KnotMatcher",
                        "_pattern": best_match.pattern,
                    },
                }

            # Create final result
            from sotd.match.types import create_match_result

            result = create_match_result(
                original=value,
                matched=matched,
                match_type="single_component",
                pattern=best_match.pattern,
            )
            result.strategy = "single_component_fallback"
            return result

        return None
