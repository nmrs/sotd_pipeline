from .base_matcher import BaseMatcher
from pathlib import Path
import re


class BladeMatcher(BaseMatcher):
    def __init__(self, catalog_path: Path = Path("data/blades.yaml")):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.patterns = []
        for brand, models in self.catalog.items():
            if not isinstance(models, dict):
                continue
            for model, data in models.items():
                label = f"{brand} {model}"
                fmt = data.get("format", "DE")
                for raw_pattern in data.get("patterns", []):
                    pattern = re.compile(raw_pattern, re.IGNORECASE)
                    self.patterns.append((label, raw_pattern, pattern, fmt))

    def extract_use_count(self, text: str) -> tuple[str, int | None]:
        match = re.match(r"^(.*?)(?:\s*[\(\[\{](?:x)?(\d+)[\)\]\}])?$", text)
        if match:
            return match.group(1), int(match.group(2)) if match.group(2) else None
        return text, None

    def match(self, value: str) -> dict[str, str | dict | None]:
        original = value
        normalized = self.normalize(value)
        if not normalized:
            return {"original": original, "matched": None, "pattern": None}

        blade_text, use_count = self.extract_use_count(normalized)

        for label, raw_pattern, pattern, fmt in self.patterns:
            if pattern.search(blade_text):
                matched = {
                    "blade": label,
                    "format": fmt,
                    "use": use_count,
                }
                return {
                    "original": original,
                    "matched": matched,
                    "pattern": raw_pattern,
                }

        return {"original": original, "matched": None, "pattern": None}
