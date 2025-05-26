import re
import yaml
from pathlib import Path


# Custom YAML loader that raises an error on duplicate keys
class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key}",
                    key_node.start_mark,
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class RazorMatcher:
    def __init__(self, catalog_path: Path = Path("data/razors.yaml")):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.patterns = self._compile_patterns()

    def _load_catalog(self):
        with self.catalog_path.open("r", encoding="utf-8") as f:
            return yaml.load(f, Loader=UniqueKeyLoader)

    def _compile_patterns(self):
        compiled = []
        for manufacturer, models in self.catalog.items():
            if not isinstance(models, dict):
                continue  # Skip malformed
            for model, entry in models.items():
                patterns = entry.get("patterns", [])
                fmt = entry.get("format", "DE")
                for pattern in patterns:
                    try:
                        compiled.append(
                            (manufacturer, model, fmt, pattern, re.compile(pattern, re.IGNORECASE))
                        )
                    except re.error:
                        pass
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def match(self, value: str) -> dict:
        original = value
        if not isinstance(value, str):
            return {"original": original, "matched": None, "pattern": None}

        normalized = value.strip()

        # Sort patterns by regex length descending
        sorted_patterns = sorted(self.patterns, key=lambda x: len(x[3]), reverse=True)

        for manufacturer, model, fmt, raw_pattern, compiled in sorted_patterns:
            if compiled.search(normalized):
                return {
                    "original": original,
                    "matched": {"manufacturer": manufacturer, "model": model, "format": fmt},
                    "pattern": raw_pattern,
                }

        return {"original": original, "matched": None, "pattern": None}
