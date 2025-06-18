import re

from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)


class KnownBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def __init__(self, catalog_data):
        super().__init__(catalog_data)
        self.patterns = self._compile_known_brush_patterns()

    def _compile_known_brush_patterns(self) -> list[dict]:
        raw = self.catalog

        all_patterns = []
        for brand, models in raw.items():
            if not isinstance(models, dict):
                continue  # Skip invalid entries
            for model, details in models.items():
                if not details or "patterns" not in details:
                    continue
                entry = {
                    "brand": brand,
                    "model": model if model else None,
                    "fiber": details.get("fiber"),
                    "knot_size_mm": details.get("knot_size_mm"),
                    "handle_maker": details.get("handle_maker"),
                }
                patterns = details["patterns"]
                patterns = sorted(patterns, key=len, reverse=True)
                for pattern in patterns:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    all_patterns.append({"compiled": compiled, "pattern": pattern, **entry})
        return sorted(all_patterns, key=lambda x: len(x["pattern"]), reverse=True)

    def match(self, value: str) -> dict:
        if not isinstance(value, str):
            return {"original": value, "matched": None, "pattern": None, "strategy": "KnownBrush"}

        text = value.strip()
        for entry in self.patterns:
            if entry["compiled"].search(text):
                entry_result = {
                    "brand": entry.get("brand"),
                    "model": entry.get("model"),
                    "fiber": entry.get("fiber"),
                    "knot_size_mm": entry.get("knot_size_mm"),
                    "handle_maker": entry.get("handle_maker"),
                    "source_text": value,
                }
                return {
                    "original": value,
                    "matched": entry_result,
                    "match_type": "exact",
                    "pattern": entry["pattern"],
                    "strategy": "KnownBrush",
                }

        return {
            "original": value,
            "matched": None,
            "match_type": None,
            "pattern": None,
            "strategy": "KnownBrush",
        }
