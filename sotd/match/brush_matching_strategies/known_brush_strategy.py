from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    compile_catalog_patterns,
    validate_string_input,
)
from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)
from sotd.match.types import MatchResult, create_match_result


class KnownBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def __init__(self, catalog_data, handle_matcher=None):
        super().__init__(catalog_data)
        self.patterns = self._compile_known_brush_patterns()
        self.handle_matcher = handle_matcher

    def _compile_known_brush_patterns(self) -> list[dict]:
        """Compile patterns using the unified pattern utilities."""
        return compile_catalog_patterns(
            self.catalog,
            pattern_field="patterns",
            metadata_fields=["fiber", "knot_size_mm", "handle_maker"],
        )

    def match(self, value: str) -> MatchResult:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return create_match_result(original=value, matched=None, pattern=None, match_type=None)

        # Use unified pattern matching
        for entry in self.patterns:
            if entry["compiled"].search(normalized_text):
                entry_result = {
                    "brand": entry.get("brand"),
                    "model": entry.get("model"),
                    "fiber": entry.get("fiber"),
                    "knot_size_mm": entry.get("knot_size_mm"),
                    "handle_maker": entry.get("handle_maker"),
                    "source_text": value,
                }

                # Add knot-specific information if available
                if entry.get("knot_model"):
                    entry_result["knot_model"] = entry.get("knot_model")
                if entry.get("knot_fiber"):
                    entry_result["knot_fiber"] = entry.get("knot_fiber")
                if entry.get("knot_brand"):
                    entry_result["knot_brand"] = entry.get("knot_brand")

                # Add handle-specific information if available
                if entry.get("handle_model"):
                    entry_result["handle_model"] = entry.get("handle_model")
                if entry.get("handle_brand"):
                    entry_result["handle_brand"] = entry.get("handle_brand")

                # Apply complete brush handle matching if enabled and HandleMatcher is available
                if self.handle_matcher:
                    self._apply_handle_matching(entry_result, value)

                return create_match_result(
                    original=value,
                    matched=entry_result,
                    pattern=entry["pattern"],
                    match_type="regex",
                    strategy="known_brush",
                )

        return create_match_result(original=value, matched=None, pattern=None, match_type=None)

    def _apply_handle_matching(self, entry_result: dict, value: str) -> None:
        """
        Apply handle matching to enhance brush match with handle information.

        This method checks if handle matching is enabled for the brush and attempts
        to match the handle on the full brush text using the HandleMatcher.

        Args:
            entry_result: The brush match result dictionary to enhance
            value: The original brush text being matched
        """
        if not self.handle_matcher:
            return

        # Get the brush brand and model
        brand = entry_result.get("brand")
        model = entry_result.get("model")

        if not brand or not model:
            return

        # Check if handle_matching is enabled for this brush
        # This is a simplified check - in the full implementation, we'd need to check the catalog
        # For now, we'll assume handle matching is enabled for Declaration Grooming
        if brand.lower() == "declaration grooming":
            try:
                handle_match = self.handle_matcher.match_handle_maker(value)
                if handle_match and handle_match.get("handle_maker"):
                    # Update the handle_model with the HandleMatcher result
                    entry_result["handle_model"] = handle_match.get("handle_model")
                    entry_result["handle_brand"] = handle_match.get("handle_maker")
            except Exception:
                # Handle matcher failed, continue without handle information
                pass
