from sotd.match.brush_matching_strategies.utils.pattern_utils import (
    compile_patterns_with_metadata,
    validate_string_input,
)

from .base_brush_matching_strategy import BaseBrushMatchingStrategy


class ChiselAndHoundBrushMatchingStrategy(BaseBrushMatchingStrategy):
    def __init__(self):
        self.patterns = self._build_patterns()

    def _build_patterns(self):
        """Build patterns using the unified pattern utilities."""
        patterns_data = []
        for v in range(27, 9, -1):
            for pattern in [
                r"chis.*[fh]ou",
                r"\bc(?:\s*\&\s*|\s+and\s+|\s*\+\s*)h\b",
            ]:
                regex = rf"{pattern}.*\bv\s*{v}\b"
                patterns_data.append(
                    {
                        "pattern": regex,
                        "brand": "Chisel & Hound",
                        "model": f"V{v}",
                        "fiber": "badger",
                        "knot_size_mm": 26.0,
                    }
                )

        return compile_patterns_with_metadata(patterns_data)

    def match(self, value: str) -> dict | None:
        # Use unified string validation
        normalized_text = validate_string_input(value)
        if normalized_text is None:
            return None

        normalized = normalized_text.lower()
        for entry in self.patterns:
            if entry["compiled"].search(normalized):
                return {
                    "brand": entry["brand"],
                    "model": entry["model"],
                    "fiber": entry["fiber"],
                    "knot_size_mm": entry["knot_size_mm"],
                    "handle_maker": None,
                    "source_text": value,
                    "source_type": "exact",
                }
        return None

    def _get_default_match(self) -> dict:
        return {
            "brand": "Chisel & Hound",
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
            "source_text": None,
            "source_type": None,
        }
