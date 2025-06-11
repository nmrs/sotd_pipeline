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
                    "handle maker": details.get("handle maker"),
                    "knot maker": details.get("knot maker"),
                }
                patterns = details["patterns"]
                patterns = sorted(patterns, key=len, reverse=True)
                for pattern in patterns:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    all_patterns.append({"compiled": compiled, "pattern": pattern, **entry})
        return all_patterns

    def match(self, value: str) -> dict:
        if not isinstance(value, str):
            return {"original": value, "matched": None, "pattern": None, "strategy": "KnownBrush"}

        lowered = value.strip().lower()

        for entry in self.patterns:
            if entry["compiled"].search(lowered):
                return {
                    "original": value,
                    "matched": {
                        "brand": entry["brand"],
                        "model": entry["model"],
                        "fiber": entry.get("fiber"),
                        "knot_size_mm": (
                            float(entry["knot_size_mm"]) if entry.get("knot_size_mm") else None
                        ),
                        "handle maker": entry.get("handle maker"),
                        "knot maker": entry.get("knot maker"),
                        "source_text": value,
                    },
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
