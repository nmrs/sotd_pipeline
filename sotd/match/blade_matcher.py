import re
from pathlib import Path
from typing import Any, Dict

from .base_matcher import BaseMatcher, MatchType


class BladeMatcher(BaseMatcher):
    def __init__(self, catalog_path: Path = Path("data/blades.yaml")):
        # catalog_path = base_path / "blades.yaml"
        super().__init__(catalog_path, "blade")
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        compiled = []
        for brand, models in self.catalog.items():
            for model, entry in models.items():
                # label = f"{brand} {model}"
                patterns = entry.get("patterns", [])
                fmt = entry.get("format", "DE")
                for pattern in patterns:
                    compiled.append(
                        (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE), entry)
                    )
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """Match using regex patterns with REGEX match type."""
        original = value
        normalized = self.normalize(value)
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,  # Keep None for backward compatibility
            }

        blade_text = normalized

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(blade_text):
                # Start with basic match data
                matched_data = {
                    "brand": brand,
                    "model": str(model),  # Ensure model is always a string
                    "format": fmt,
                }

                # Preserve all additional specifications from the catalog entry
                # (excluding patterns and format which are already handled)
                for key, value in entry.items():
                    if key not in ["patterns", "format"]:
                        matched_data[key] = value

                return {
                    "original": original,
                    "matched": matched_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,  # Keep None for backward compatibility
        }
