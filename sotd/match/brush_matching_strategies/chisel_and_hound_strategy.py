import re

from .base_brush_matching_strategy import BaseBrushMatchingStrategy


class ChiselAndHoundBrushMatchingStrategy(BaseBrushMatchingStrategy):
    def __init__(self):
        self.patterns = self._build_patterns()

    def _build_patterns(self):
        patterns = []
        for v in range(27, 9, -1):
            for pattern in [
                r"chis.*[fh]ou",
                r"\bc(?:\s*\&\s*|\s+and\s+|\s*\+\s*)h\b",
            ]:
                regex = rf"{pattern}.*\bv\s*{v}\b"
                compiled = re.compile(regex, re.IGNORECASE)
                patterns.append(
                    {
                        "compiled": compiled,
                        "pattern": regex,
                        "brand": "Chisel & Hound",
                        "model": f"V{v}",
                        "fiber": "badger",
                        "knot_size_mm": 26.0,
                    }
                )
        return sorted(patterns, key=lambda x: len(x["pattern"]), reverse=True)

    def match(self, value: str) -> dict | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
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
