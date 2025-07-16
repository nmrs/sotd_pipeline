from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    compile_catalog_patterns,
    validate_string_input,
)
from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)
from sotd.match.types import MatchResult, create_match_result


class KnownBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def __init__(self, catalog_data):
        super().__init__(catalog_data)
        self.patterns = self._compile_known_brush_patterns()

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
                return create_match_result(
                    original=value,
                    matched=entry_result,
                    pattern=entry["pattern"],
                    match_type="exact",
                )

        return create_match_result(original=value, matched=None, pattern=None, match_type=None)
