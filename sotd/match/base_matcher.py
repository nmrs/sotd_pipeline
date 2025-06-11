from pathlib import Path
from typing import Optional

from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc


class BaseMatcher:
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> dict:
        return load_yaml_with_nfc(self.catalog_path, loader_cls=UniqueKeyLoader)

    def normalize(self, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else None
