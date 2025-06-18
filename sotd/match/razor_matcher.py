import re
from pathlib import Path

from sotd.match.base_matcher import BaseMatcher


class RazorMatcher(BaseMatcher):
    def __init__(self, catalog_path: Path = Path("data/razors.yaml")):
        super().__init__(catalog_path)
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        compiled = []
        for brand, models in self.catalog.items():
            for model, entry in models.items():
                patterns = entry.get("patterns", [])
                fmt = entry.get("format", "DE")
                for pattern in patterns:
                    compiled.append(
                        (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE), entry)
                    )
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def match(self, value: str) -> dict:
        original = value
        if not isinstance(value, str):
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,
            }

        normalized = value.strip()

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(normalized):
                # Start with basic match data
                matched_data = {
                    "brand": brand,
                    "model": model,
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
                    "match_type": "exact",
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }
