import re
from typing import Optional

from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)


class DeclarationGroomingBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def __init__(self, catalog_data: dict):
        super().__init__(catalog_data)
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        compiled = []
        for brand, models in self.catalog.items():
            for model, entry in models.items():
                for pattern in entry.get("patterns", []):
                    compiled.append(
                        {
                            "brand": brand,
                            "model": model,
                            "pattern": pattern,
                            "compiled": re.compile(pattern, re.IGNORECASE),
                            "fiber": entry.get("fiber"),
                            "knot_size_mm": entry.get("knot_size_mm"),
                        }
                    )
        return sorted(compiled, key=lambda x: len(x["pattern"]), reverse=True)

    def _extract_knot_size(self, text: str) -> Optional[float]:
        match = re.search(r"(\d{2}(\.\d+)?)\s*-?\s*mm", text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def _get_default_match(self) -> dict:
        return {
            "brand": "Declaration Grooming",
            "model": None,
            "fiber": None,
            "knot_size_mm": None,
            "handle_maker": None,
            "source_text": None,
            "source_type": None,
        }

    def match(self, value: str) -> dict:
        if not isinstance(value, str):
            return {
                "original": value,
                "matched": None,
                "pattern": None,
                "strategy": "DeclarationGrooming",
            }

        normalized = value.strip()
        lowered = normalized.lower()
        default_fiber = "Badger"
        default_knot_size_mm = 28.0

        # Check for explicit non-DG brand context that should prevent DG matching
        non_dg_brand_patterns = [
            r"\bzenith\b",
            r"\bomega\b",
            r"\bsimpson\b",
            r"\bwald\b",
            r"\bmaggard\b",
            r"\bchisel\s*&?\s*hound\b",
            r"\bc&h\b",
        ]

        has_non_dg_context = any(re.search(pattern, lowered) for pattern in non_dg_brand_patterns)

        if has_non_dg_context:
            return {
                "original": value,
                "matched": None,
                "pattern": None,
                "strategy": "DeclarationGrooming",
            }

        # Now check model patterns if we have DG context
        for entry in self.patterns:
            if entry["compiled"].search(lowered):
                knot_size = (
                    self._extract_knot_size(normalized)
                    or entry.get("knot_size_mm")
                    or default_knot_size_mm
                )
                fiber = entry.get("fiber") or default_fiber

                return {
                    "original": value,
                    "matched": {
                        "brand": entry["brand"],
                        "model": entry["model"],
                        "fiber": fiber,
                        "knot_size_mm": knot_size,
                        "handle_maker": None,
                        "source_text": value,
                        "source_type": "exact",
                    },
                    "pattern": entry["pattern"],
                    "strategy": "DeclarationGrooming",
                }

        return {
            "original": value,
            "matched": None,
            "pattern": None,
            "strategy": "DeclarationGrooming",
        }
