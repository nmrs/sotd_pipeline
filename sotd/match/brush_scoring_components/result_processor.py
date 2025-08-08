"""
Result Processor Component.

This component processes final results to ensure consistency and format.
"""

from typing import Optional

from sotd.match.types import MatchResult


class ResultProcessor:
    """
    Processor for final brush matching results.

    This component ensures output format consistency and applies
    any final processing steps.
    """

    def __init__(self, knot_matcher=None):
        """Initialize the result processor."""
        self.knot_matcher = knot_matcher

    def process_result(self, result: Optional[MatchResult], value: str) -> Optional[MatchResult]:
        """
        Process a final result.

        Args:
            result: MatchResult to process, or None
            value: Original input string

        Returns:
            Processed MatchResult, or None
        """
        if result is None:
            return None

        # Ensure consistent structure
        self._ensure_consistent_structure(result)

        # Apply any final processing
        self._apply_final_processing(result, value)

        return result

    def _ensure_consistent_structure(self, result: MatchResult) -> None:
        """
        Ensure result has consistent structure matching legacy system.

        Args:
            result: MatchResult to process
        """
        # For Phase 3.1 (Black Box Alignment), preserve None for unmatched cases
        # Don't convert None to empty dict - this should match legacy behavior
        if result.matched is None:
            return  # Preserve None for unmatched cases

        # For Phase 3.1 (Black Box Alignment), don't add extra fields
        # that the legacy system doesn't have
        # TODO: Re-enable these fields in Phase 3.2+ when we break down individual strategies
        # if "source_text" not in result.matched:
        #     result.matched["source_text"] = result.original
        #
        # if "source_type" not in result.matched:
        #     result.matched["source_type"] = result.match_type or "unknown"

        # Create nested handle and knot sections to match legacy system structure
        # Only if they don't already exist (preserve composite brush structure)
        if "handle" not in result.matched or "knot" not in result.matched:
            self._create_handle_knot_sections(result)

    def _apply_final_processing(self, result: MatchResult, value: str) -> None:
        """
        Apply final processing steps.

        Args:
            result: MatchResult to process
            value: Original input string
        """
        # Set original field if not already set
        if not result.original:
            result.original = value

        # Ensure pattern field exists
        if not result.pattern:
            result.pattern = "unknown"

        # Ensure match_type field exists (preserve None to match legacy behavior)
        if not result.match_type:
            result.match_type = None

    def _create_handle_knot_sections(self, result: MatchResult) -> None:
        """
        Create nested handle and knot sections to match legacy system structure.

        Args:
            result: MatchResult to process
        """
        if result.matched is None:
            return  # Preserve None for unmatched cases

        # Extract fields from the flat structure
        brand = result.matched.get("brand")
        model = result.matched.get("model")
        fiber = result.matched.get("fiber")
        knot_size_mm = result.matched.get("knot_size_mm")

        # Extract specific handle and knot fields if they exist
        handle_brand = result.matched.get("handle_brand", brand)
        handle_model = result.matched.get("handle_model")  # Don't fall back to model
        knot_brand = result.matched.get("knot_brand", brand)
        knot_model = result.matched.get("knot_model", model)

        # For known_brush strategy, preserve None for handle_model when not defined
        # Legacy system correctly sets handle model to None when no specific handle model is defined

        # Create handle section
        result.matched["handle"] = {
            "brand": handle_brand,
            "model": handle_model,
            "source_text": result.matched.get("source_text", result.original),
            "_matched_by": result.strategy or "BrushScoringMatcher",
            "_pattern": result.pattern or "unknown",
        }

        # If no fiber found, try to get it from knot matcher
        if fiber is None and self.knot_matcher:
            # Use the knot matcher to find fiber information for this brand/model
            search_text = f"{knot_brand} {knot_model}" if knot_model else knot_brand
            knot_result = self.knot_matcher.match(search_text)
            if knot_result and knot_result.matched:
                fiber = knot_result.matched.get("fiber")

        # Create knot section
        result.matched["knot"] = {
            "brand": knot_brand,
            "model": knot_model,
            "fiber": fiber,
            "knot_size_mm": knot_size_mm,
            "source_text": result.matched.get("source_text", result.original),
            "_matched_by": result.strategy or "BrushScoringMatcher",
            "_pattern": result.pattern or "unknown",
        }

        # Remove flat fields that are now in nested sections
        # Keep brand and model at top level for compatibility
        result.matched.pop("fiber", None)
        result.matched.pop("knot_size_mm", None)
        result.matched.pop("handle_maker", None)
        result.matched.pop("source_type", None)
        result.matched.pop("handle_brand", None)
        result.matched.pop("handle_model", None)
        result.matched.pop("knot_brand", None)
        result.matched.pop("knot_model", None)
