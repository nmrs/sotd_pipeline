import re
from pathlib import Path
from typing import Optional

import yaml


class HandleMakerEnricher:
    def __init__(self, yaml_path: Path = Path("data/brush_yaml/artisan_handles.yaml")):
        with yaml_path.open("r", encoding="utf-8") as f:
            self.patterns = yaml.safe_load(f)

        self.compiled = []
        for maker, val in self.patterns.items():
            for pat in val.get("patterns", []):
                self.compiled.append((maker, re.compile(pat, re.IGNORECASE)))

    def match(self, text: str) -> Optional[dict]:
        for maker, pat in self.compiled:
            if pat.search(text):
                return {
                    "handle_maker": maker,
                    "handle_strategy": "yaml_pattern",
                    "handle_pattern": pat.pattern,
                }
        return None


class HandleEnrichmentPipeline:
    def __init__(self):
        self.strategies = [
            HandleMakerEnricher(),
            # Add more strategies here, e.g., self._parse_from_by, self._parse_from_slash
        ]

    def enrich(self, original: str, matched: Optional[dict]) -> dict:
        for strategy in self.strategies:
            if callable(strategy):
                result = strategy(original, matched)
            else:
                result = strategy.match(original)

            if result:
                return result

        return {"handle_maker": None, "handle_strategy": None, "handle_pattern": None}
