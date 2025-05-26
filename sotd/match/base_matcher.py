import re
import yaml
from pathlib import Path
from typing import Optional

class BaseMatcher:
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.patterns = self._compile_patterns()

    def _load_catalog(self) -> dict:
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _compile_patterns(self) -> list[tuple[str, str, re.Pattern]]:
        compiled = []
        for label, data in self.catalog.items():
            raw_patterns = data.get("patterns", [])
            for raw in raw_patterns:
                try:
                    compiled.append((label, raw, re.compile(raw, re.IGNORECASE)))
                except re.error:
                    pass  # Skip invalid regex patterns
        # Sort patterns by raw regex string length, descending
        return sorted(compiled, key=lambda x: len(x[1]), reverse=True)

    def normalize(self, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else None
