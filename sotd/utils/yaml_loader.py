import unicodedata
from pathlib import Path
from typing import Any

import yaml


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


def normalize_nfc(value: Any) -> Any:
    if isinstance(value, dict):
        return {normalize_nfc(k): normalize_nfc(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [normalize_nfc(item) for item in value]
    elif isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    return value


def load_yaml_with_nfc(path: Path, loader_cls=yaml.SafeLoader) -> Any:
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.load(f, Loader=loader_cls)
    return normalize_nfc(raw)
