#!/usr/bin/env python3
"""Pattern management utilities for mismatch analysis."""

import hashlib
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

from sotd.utils.yaml_loader import load_yaml_with_nfc


class PatternManager:
    """Manages catalog pattern loading, caching, and compilation."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._catalog_patterns = {}  # Cache for catalog patterns
        self._catalog_cache_info = {}  # Cache metadata (timestamps, hashes)
        self._compiled_patterns = {}  # Cache for compiled regex patterns

    def clear_cache(self) -> None:
        """Clear all pattern caches."""
        self._catalog_patterns.clear()
        self._catalog_cache_info.clear()
        self._compiled_patterns.clear()
        self.console.print("[green]Pattern cache cleared[/green]")

    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file contents."""
        try:
            with file_path.open("rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _is_cache_valid(self, field: str, catalog_path: Path) -> bool:
        """Check if cached patterns are still valid for a field."""
        if field not in self._catalog_cache_info:
            return False

        cache_info = self._catalog_cache_info[field]

        # Check if file still exists
        if not catalog_path.exists():
            return False

        # Check modification time
        current_mtime = catalog_path.stat().st_mtime
        if current_mtime != cache_info.get("mtime"):
            return False

        # Check file hash
        current_hash = self._get_file_hash(catalog_path)
        if current_hash != cache_info.get("hash"):
            return False

        return True

    def _update_cache_info(self, field: str, catalog_path: Path) -> None:
        """Update cache metadata for a field."""
        try:
            mtime = catalog_path.stat().st_mtime
            file_hash = self._get_file_hash(catalog_path)

            self._catalog_cache_info[field] = {
                "mtime": mtime,
                "hash": file_hash,
                "last_updated": time.time(),
            }
        except Exception as e:
            self.console.print(
                f"[yellow]Warning: Could not update cache info for {field}: {e}[/yellow]"
            )

    def get_compiled_pattern(self, pattern_text: str):
        """Get or compile a regex pattern."""
        if pattern_text not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern_text] = re.compile(pattern_text, re.IGNORECASE)
            except re.error as e:
                self.console.print(
                    f"[yellow]Warning: Invalid regex pattern '{pattern_text}': {e}[/yellow]"
                )
                return None
        return self._compiled_patterns[pattern_text]

    def _get_product_key(self, pattern_info: Dict, field: str) -> str:
        """Create a product key from pattern info."""
        brand = pattern_info.get("brand", "")
        model = pattern_info.get("model", "")

        if field == "soap":
            return f"{brand}|{model}"  # maker|scent for soap
        else:
            return f"{brand}|{model}"  # brand|model for others

    def load_catalog_patterns(self, field: str) -> List[Dict]:
        """Load and cache catalog patterns for a field."""
        # Check cache first
        if field in self._catalog_patterns:
            catalog_path = Path(f"data/{field}s.yaml")
            if self._is_cache_valid(field, catalog_path):
                return self._catalog_patterns[field]

        # Load from file
        catalog_path = Path(f"data/{field}s.yaml")
        if not catalog_path.exists():
            self.console.print(f"[yellow]Warning: No catalog file found for {field}s[/yellow]")
            return []

        try:
            catalog_data = load_yaml_with_nfc(catalog_path)
            patterns = self._extract_patterns_from_catalog(catalog_data, field)

            # Cache the patterns
            self._catalog_patterns[field] = patterns
            self._update_cache_info(field, catalog_path)

            return patterns
        except Exception as e:
            self.console.print(f"[red]Error loading catalog patterns for {field}: {e}[/red]")
            return []

    def _extract_patterns_from_catalog(self, catalog_data: Dict, field: str) -> List[Dict]:
        """Extract patterns from catalog data."""
        patterns = []

        for brand, brand_data in catalog_data.items():
            if not isinstance(brand_data, dict):
                continue

            for model, model_data in brand_data.items():
                if not isinstance(model_data, dict):
                    continue

                model_patterns = model_data.get("patterns", [])
                if not isinstance(model_patterns, list):
                    continue

                for pattern in model_patterns:
                    patterns.append(
                        {
                            "brand": brand,
                            "model": model,
                            "pattern": pattern,
                            "product_key": self._get_product_key(
                                {"brand": brand, "model": model}, field
                            ),
                        }
                    )

        return patterns

    def find_multiple_pattern_matches(
        self, original: str, field: str, current_pattern: str, catalog_patterns: List[Dict]
    ) -> List[str]:
        """Find all patterns that match the original text."""
        matching_patterns = []

        for pattern_info in catalog_patterns:
            pattern_text = pattern_info["pattern"]

            # Skip the current pattern (already matched)
            if pattern_text == current_pattern:
                continue

            compiled_pattern = self.get_compiled_pattern(pattern_text)
            if compiled_pattern and compiled_pattern.search(original):
                matching_patterns.append(pattern_info["product_key"])

        return matching_patterns
