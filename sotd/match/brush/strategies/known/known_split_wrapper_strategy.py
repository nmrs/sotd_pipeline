"""
Known Split Wrapper Strategy.

This strategy implements known split functionality directly
to integrate with the scoring system architecture.
"""

import re
from typing import Optional

# ComponentScoreCalculator no longer needed - scoring is handled externally
from sotd.match.types import MatchResult

from ..base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)


class KnownSplitWrapperStrategy(BaseBrushMatchingStrategy):
    """Strategy for matching known split brush patterns."""

    def __init__(self, known_splits_data: dict, handle_matcher=None, knot_matcher=None):
        """
        Initialize the strategy with known splits data and standard matchers.

        Args:
            known_splits_data: Dictionary containing known split brush patterns
            handle_matcher: HandleMatcher instance for handle matching
            knot_matcher: KnotMatcher instance for knot matching
        """
        super().__init__()
        self.known_splits_data = known_splits_data or {}
        self.handle_matcher = handle_matcher
        self.knot_matcher = knot_matcher
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> list:
        """Compile patterns for known splits from brush_splits.yaml structure."""
        compiled = []
        # brush_splits.yaml has brush names as top-level keys
        for brush_name, split_data in self.known_splits_data.items():
            if isinstance(split_data, dict):
                # Create a simple pattern that matches the exact brush name
                # Use word boundaries only at the start/end, not around the entire pattern
                pattern = re.escape(brush_name)
                try:
                    compiled.append(
                        {
                            "pattern": pattern,
                            "regex": re.compile(rf"^{pattern}$", re.IGNORECASE),
                            "brush_name": brush_name,
                            "data": split_data,
                        }
                    )
                except re.error:
                    # Skip invalid patterns
                    continue
        return compiled

    def match(self, value: str, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """
        Match using known split logic.

        Args:
            value: The brush string to match

        Returns:
            MatchResult or None
        """
        if not value or not isinstance(value, str):
            return None

        # Try to match against compiled patterns
        for pattern_info in self.compiled_patterns:
            if pattern_info["regex"].search(value):
                split_data = pattern_info["data"]

                # Check if this brush should not be split (from brush_splits.yaml)
                if split_data.get("should_not_split", False):
                    # Skip all split strategies if should_not_split is True
                    return None

                # Extract handle and knot from the split data
                handle = split_data.get("handle", "")
                knot = split_data.get("knot", "")

                # Use standard matchers to get rich data from handle and knot components
                handle_result = None
                knot_result = None

                if self.handle_matcher and handle:
                    try:
                        handle_result = self.handle_matcher.match(handle)
                    except Exception:
                        # Handle matcher failed, continue with None
                        pass

                if self.knot_matcher and knot:
                    try:
                        knot_result = self.knot_matcher.match(knot)
                    except Exception:
                        # Knot matcher failed, continue with None
                        pass

                # Extract data from matcher results or fall back to simple parsing
                if handle_result and hasattr(handle_result, "matched") and handle_result.matched:
                    handle_data = handle_result.matched
                    handle_maker = handle_data.get("handle_maker")
                    handle_model = handle_data.get("handle_model")
                else:
                    # Fallback to simple parsing if matcher failed
                    handle_parts = (
                        handle.replace("(", "").replace(")", "").split() if handle else []
                    )
                    handle_maker = handle_parts[0] if handle_parts else None
                    handle_model = " ".join(handle_parts[1:]) if len(handle_parts) > 1 else None

                if knot_result and hasattr(knot_result, "matched") and knot_result.matched:
                    knot_data = knot_result.matched
                    brand = knot_data.get("brand")
                    model = knot_data.get("model")
                    fiber = knot_data.get("fiber")
                    knot_size_mm = knot_data.get("knot_size_mm")
                else:
                    # Fallback to simple parsing if matcher failed
                    knot_parts = knot.split() if knot else []
                    brand = knot_parts[0] if knot_parts else None
                    model = " ".join(knot_parts[1:]) if len(knot_parts) > 1 else None
                    fiber = None
                    knot_size_mm = None

                # Determine if handle and knot are from the same brand
                same_brand = handle_maker and brand and handle_maker.lower() == brand.lower()

                # Create match result with nested handle/knot structure for modifier functions
                matched_data = {
                    # Only set top-level brand if handle and knot are from the same brand
                    "brand": brand if same_brand else None,
                    # Never set top-level model for known_split brushes
                    "source_text": value,
                    "_matched_by": "KnownSplitWrapperStrategy",
                    "_pattern": pattern_info["pattern"],
                    "_brush_name": pattern_info["brush_name"],
                    # Add nested handle and knot sections for modifier functions
                    "handle": {
                        "brand": handle_maker,
                        "model": handle_model,
                        "source_text": handle,
                        "_matched_by": (
                            "HandleMatcher" if handle_result else "KnownSplitWrapperStrategy"
                        ),
                        "_pattern": (
                            handle_result.pattern if handle_result else pattern_info["pattern"]
                        ),
                    },
                    "knot": {
                        "brand": brand,
                        "model": model,
                        "fiber": fiber,
                        "knot_size_mm": knot_size_mm,
                        "source_text": knot,
                        "_matched_by": (
                            "KnotMatcher" if knot_result else "KnownSplitWrapperStrategy"
                        ),
                        "_pattern": knot_result.pattern if knot_result else pattern_info["pattern"],
                    },
                }

                # Component scores are now calculated externally by the scoring engine
                # No need to pre-calculate scores here

                return MatchResult(
                    original=value,
                    matched=matched_data,
                    match_type="known_split",
                    pattern=pattern_info["pattern"],
                    strategy="known_split",  # Set the strategy name
                )

        return None
