import re
from pathlib import Path

from .base_matcher import BaseMatcher


class BladeMatcher(BaseMatcher):
    def __init__(self, catalog_path: Path = Path("data/blades.yaml")):
        # catalog_path = base_path / "blades.yaml"
        super().__init__(catalog_path)
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
                        (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE))
                    )
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def extract_use_count(self, text: str) -> tuple[str, int | None]:
        match = re.match(r"^(.*?)(?:\s*[\(\[\{](?:x)?(\d+)(?:x)?[\)\]\}])?$", text, re.IGNORECASE)
        if match:
            return match.group(1), int(match.group(2)) if match.group(2) else None
        return text, None

    def match(self, value: str) -> dict[str, str | dict | None]:
        original = value
        normalized = self.normalize(value)
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,
            }

        blade_text, use_count = self.extract_use_count(normalized)

        for brand, model, fmt, raw_pattern, compiled in self.patterns:
            if compiled.search(blade_text):
                matched = {
                    "brand": brand,
                    "model": str(model),  # Ensure model is always a string
                    "format": fmt,
                    "use": use_count,
                }
                return {
                    "original": original,
                    "matched": matched,
                    "pattern": raw_pattern,
                    "match_type": "exact",
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }
