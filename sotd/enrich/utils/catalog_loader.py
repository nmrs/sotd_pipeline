"""Catalog loading utilities for user intent detection."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class CatalogLoader:
    """Utility class for loading and caching catalog patterns."""

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize catalog loader.

        Args:
            data_path: Path to data directory containing catalogs
        """
        self.data_path = data_path or Path("data")
        self._pattern_cache = {}  # (catalog_type, brand, model) -> List[str]
        self._compiled_pattern_cache = {}  # (catalog_type, brand, model) -> List[re.Pattern]
        self._cache_hits = 0
        self._cache_misses = 0

    def load_handle_patterns(self, brand: str, model: str) -> List[str]:
        """
        Load handle patterns for given brand/model combination.

        Args:
            brand: Handle brand
            model: Handle model

        Returns:
            List[str]: List of patterns to search for
        """
        return self._get_cached_patterns("handles", brand, model)

    def load_compiled_handle_patterns(self, brand: str, model: str) -> List[re.Pattern]:
        """
        Load compiled handle patterns for given brand/model combination.

        Args:
            brand: Handle brand
            model: Handle model

        Returns:
            List[re.Pattern]: List of compiled patterns to search for
        """
        return self._get_cached_compiled_patterns("handles", brand, model)

    def load_knot_patterns(self, brand: str, model: str) -> List[str]:
        """
        Load knot patterns for given brand/model combination.

        Args:
            brand: Knot brand
            model: Knot model

        Returns:
            List[str]: List of patterns to search for
        """
        return self._get_cached_patterns("knots", brand, model)

    def load_compiled_knot_patterns(self, brand: str, model: str) -> List[re.Pattern]:
        """
        Load compiled knot patterns for given brand/model combination.

        Args:
            brand: Knot brand
            model: Knot model

        Returns:
            List[re.Pattern]: List of compiled patterns to search for
        """
        return self._get_cached_compiled_patterns("knots", brand, model)

    def _get_cached_patterns(self, catalog_type: str, brand: str, model: str) -> List[str]:
        """
        Get cached patterns or load from catalog if not cached.

        Args:
            catalog_type: Type of catalog ('handles' or 'knots')
            brand: Brand name
            model: Model name

        Returns:
            List[str]: List of patterns
        """
        cache_key = (catalog_type, brand, model)

        if cache_key in self._pattern_cache:
            self._cache_hits += 1
            return self._pattern_cache[cache_key]

        self._cache_misses += 1
        patterns = self._load_patterns_from_catalog(catalog_type, brand, model)
        self._pattern_cache[cache_key] = patterns
        return patterns

    def _get_cached_compiled_patterns(
        self, catalog_type: str, brand: str, model: str
    ) -> List[re.Pattern]:
        """
        Get cached compiled patterns or compile from catalog if not cached.

        Args:
            catalog_type: Type of catalog ('handles' or 'knots')
            brand: Brand name
            model: Model name

        Returns:
            List[re.Pattern]: List of compiled patterns
        """
        cache_key = (catalog_type, brand, model)

        if cache_key in self._compiled_pattern_cache:
            return self._compiled_pattern_cache[cache_key]

        # Get raw patterns and compile them
        raw_patterns = self._get_cached_patterns(catalog_type, brand, model)
        compiled_patterns = self.compile_patterns(raw_patterns)
        self._compiled_pattern_cache[cache_key] = compiled_patterns
        return compiled_patterns

    def _load_patterns_from_catalog(self, catalog_type: str, brand: str, model: str) -> List[str]:
        """
        Load patterns from catalog file.

        Args:
            catalog_type: Type of catalog ('handles' or 'knots')
            brand: Brand name
            model: Model name

        Returns:
            List[str]: List of patterns
        """
        if not brand:
            return []

        catalog_file = self.data_path / f"{catalog_type}.yaml"
        if not catalog_file.exists():
            return []

        try:
            with open(catalog_file, "r", encoding="utf-8") as f:
                catalog_data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError):
            return []

        if not catalog_data:
            return []

        # Navigate to the appropriate section based on catalog type
        if catalog_type == "handles":
            # Search all handle sections: artisan_handles, manufacturer_handles, other_handles
            catalog_sections = [
                catalog_data.get("artisan_handles", {}),
                catalog_data.get("manufacturer_handles", {}),
                catalog_data.get("other_handles", {}),
            ]
        elif catalog_type == "knots":
            catalog_sections = [catalog_data.get("known_knots", {})]
        else:
            return []

        patterns = []

        # Search through all catalog sections
        for catalog_section in catalog_sections:
            # Find brand in this catalog section
            brand_data = catalog_section.get(brand, {})
            if not brand_data:
                continue

            # Handle different catalog structures
            if catalog_type == "handles":
                # Handles catalog: brand -> model -> patterns
                if model and model in brand_data:
                    model_data = brand_data[model]
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        patterns.extend(model_data["patterns"])
                else:
                    # Check for "Unspecified" model
                    unspecified_data = brand_data.get("Unspecified", {})
                    if isinstance(unspecified_data, dict) and "patterns" in unspecified_data:
                        patterns.extend(unspecified_data["patterns"])

            elif catalog_type == "knots":
                # Knots catalog: brand -> model -> patterns (or brand -> patterns for some entries)
                if model and model in brand_data:
                    model_data = brand_data[model]
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        patterns.extend(model_data["patterns"])
                else:
                    # Check if brand has direct patterns (some knots have this structure)
                    if isinstance(brand_data, dict) and "patterns" in brand_data:
                        patterns.extend(brand_data["patterns"])

        return patterns

    def compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """
        Compile regex patterns for efficient matching.

        Args:
            patterns: List of pattern strings

        Returns:
            List[re.Pattern]: List of compiled patterns
        """
        compiled_patterns = []
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                # Skip invalid patterns
                continue
        return compiled_patterns

    def clear_pattern_cache(self):
        """Clear pattern cache."""
        self._pattern_cache.clear()
        self._compiled_pattern_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            dict: Cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": hit_rate,
            "cached_patterns": len(self._pattern_cache),
            "cached_compiled_patterns": len(self._compiled_pattern_cache),
        }
