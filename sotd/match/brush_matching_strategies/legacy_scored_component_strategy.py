#!/usr/bin/env python3
"""LegacyScoredComponentStrategy for Phase 3.3 dual component breakdown.

This strategy uses the legacy system's single_component_fallback logic with
configurable scoring weights from brush_scoring_config.yaml.
"""

from typing import Optional

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.pattern_utils import score_match_type
from sotd.match.types import MatchResult, create_match_result


class LegacyScoredComponentStrategy(BaseBrushMatchingStrategy):
    """Strategy that uses legacy single_component_fallback logic with configurable scoring."""

    def __init__(self, legacy_matcher, scoring_config, component_type: str):
        """
        Initialize legacy scored component strategy.

        Args:
            legacy_matcher: Legacy BrushMatcher instance
            scoring_config: BrushScoringConfig instance
            component_type: Either "handle" or "knot"
        """
        super().__init__()
        self.legacy_matcher = legacy_matcher
        self.scoring_config = scoring_config
        self.component_type = component_type

        # Get scoring weights from config
        self.base_pattern_score = scoring_config.get_component_scoring_weight("base_pattern_score")
        self.indicator_bonus = scoring_config.get_component_scoring_weight("indicator_bonus")
        self.actual_match_bonus = scoring_config.get_component_scoring_weight("actual_match_bonus")
        self.handle_only_bonus = scoring_config.get_component_scoring_weight("handle_only_bonus")
        self.minimum_score_threshold = scoring_config.get_component_scoring_weight(
            "minimum_score_threshold"
        )

    def match(self, value: str) -> Optional[MatchResult]:
        """
        Try to match component using legacy scoring logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult if score meets threshold, None otherwise
        """
        if not value or not isinstance(value, str):
            return None

        try:
            # Use legacy scoring logic
            score = score_match_type(
                value,
                self.component_type,
                self.base_pattern_score,
                knot_matcher=self.legacy_matcher.knot_matcher,
                handle_matcher=self.legacy_matcher.handle_matcher,
            )

            # Check if score meets minimum threshold
            if score < self.minimum_score_threshold:
                return None

            # Get the actual match using legacy logic
            if self.component_type == "handle":
                return self._match_handle_component(value)
            else:
                return self._match_knot_component(value)

        except Exception as e:
            # Fail fast for debugging
            raise ValueError(f"Legacy scored component matching failed for '{value}': {e}")

    def _match_handle_component(self, value: str) -> Optional[MatchResult]:
        """Match handle component using legacy logic."""
        handle_match = self.legacy_matcher.handle_matcher.match_handle_maker(value)
        if handle_match and handle_match.get("handle_maker"):
            # Create composite structure like legacy system
            matched_data = {
                "brand": None,  # Composite brush
                "model": None,  # Composite brush
                "handle": {
                    "brand": handle_match.get("handle_maker"),
                    "model": handle_match.get("handle_model"),
                    "source_text": value,
                    "_matched_by": "HandleMatcher",
                    "_pattern": handle_match.get("_pattern_used", "unknown"),
                },
                "knot": {
                    "brand": None,  # No knot information
                    "model": None,
                    "fiber": None,
                    "knot_size_mm": None,
                    "source_text": value,
                    "_matched_by": "HandleMatcher",
                    "_pattern": "handle_only",
                },
            }

            return create_match_result(
                original=value,
                matched=matched_data,
                match_type="regex",  # Like legacy system
                pattern=handle_match.get("_pattern_used", "unknown"),
                strategy="handle_component",
            )

        return None

    def _match_knot_component(self, value: str) -> Optional[MatchResult]:
        """Match knot component using legacy logic."""
        # Try knot matching with legacy strategies
        best_match = None
        best_score = -1

        for strategy in self.legacy_matcher.strategies:
            try:
                result = strategy.match(value)
                if result and hasattr(result, "matched") and result.matched:
                    score = score_match_type(
                        value,
                        "knot",
                        self.base_pattern_score,
                        knot_matcher=self.legacy_matcher.knot_matcher,
                        handle_matcher=self.legacy_matcher.handle_matcher,
                    )
                    if score > best_score:
                        best_score = score
                        best_match = result
            except Exception:
                continue

        if best_match:
            # Create composite structure like legacy system
            matched_data = {
                "brand": None,  # Composite brush
                "model": None,  # Composite brush
                "handle": {
                    "brand": None,  # No handle information
                    "model": None,
                    "source_text": value,
                    "_matched_by": "KnotMatcher",
                    "_pattern": "knot_only",
                },
                "knot": {
                    "brand": best_match.matched.get("brand"),
                    "model": best_match.matched.get("model"),
                    "fiber": best_match.matched.get("fiber"),
                    "knot_size_mm": best_match.matched.get("knot_size_mm"),
                    "source_text": value,
                    "_matched_by": "KnotMatcher",
                    "_pattern": best_match.pattern or "unknown",
                },
            }

            return create_match_result(
                original=value,
                matched=matched_data,
                match_type="regex",  # Like legacy system
                pattern=best_match.pattern or "unknown",
                strategy="knot_component",
            )

        return None
