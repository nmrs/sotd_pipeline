import re
from pathlib import Path
from typing import Any, Dict

from .base_matcher import BaseMatcher, MatchType


class BladeMatcher(BaseMatcher):
    def __init__(self, catalog_path: Path = Path("data/blades.yaml")):
        # catalog_path = base_path / "blades.yaml"
        super().__init__(catalog_path, "blade")
        self.patterns = self._compile_patterns()

    def _compile_patterns(self):
        compiled = []
        for format_name, brands in self.catalog.items():
            for brand, models in brands.items():
                for model, entry in models.items():
                    patterns = entry.get("patterns", [])
                    # Use the format from the catalog structure, not from the entry
                    fmt = format_name
                    for pattern in patterns:
                        compiled.append(
                            (brand, model, fmt, pattern, re.compile(pattern, re.IGNORECASE), entry)
                        )
        return sorted(compiled, key=lambda x: len(x[3]), reverse=True)

    def _match_with_regex(self, value: str) -> Dict[str, Any]:
        """Match using regex patterns with REGEX match type."""
        original = value
        normalized = self.normalize(value)
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,  # Keep None for backward compatibility
            }

        blade_text = normalized

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(blade_text):
                # Start with basic match data
                matched_data = {
                    "brand": brand,
                    "model": str(model),  # Ensure model is always a string
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
                    "match_type": MatchType.REGEX,
                }

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,  # Keep None for backward compatibility
        }

    def match_with_context(self, value: str, razor_format: str) -> Dict[str, Any]:
        """Match blade with context-aware format prioritization."""
        original = value
        normalized = self.normalize(value)
        if not normalized:
            return {
                "original": original,
                "matched": None,
                "pattern": None,
                "match_type": None,
            }

        blade_text = normalized

        # Map razor formats to blade formats
        format_mapping = {
            "SHAVETTE (HAIR SHAPER)": "HAIR SHAPER",
            "SHAVETTE (AC)": "AC",
            "SHAVETTE (DE)": "DE",
            "SHAVETTE (HALF DE)": "DE",
            "SHAVETTE (A77)": "A77",
            "SHAVETTE (DISPOSABLE)": "DISPOSABLE",
            "CARTRIDGE": "CARTRIDGE",
            "STRAIGHT": "STRAIGHT",
            "DE": "DE",
            "AC": "AC",
            "GEM": "GEM",
            "INJECTOR": "INJECTOR",
        }

        target_blade_format = format_mapping.get(razor_format, razor_format)

        # First, try to find matches with format that matches target blade format
        format_matches = []
        other_matches = []

        for brand, model, fmt, raw_pattern, compiled, entry in self.patterns:
            if compiled.search(blade_text):
                match_data = {
                    "brand": brand,
                    "model": str(model),
                    "format": fmt,
                }

                # Preserve all additional specifications from the catalog entry
                for key, value in entry.items():
                    if key not in ["patterns", "format"]:
                        match_data[key] = value

                match_result = {
                    "original": original,
                    "matched": match_data,
                    "pattern": raw_pattern,
                    "match_type": MatchType.REGEX,
                }

                # Prioritize format matches
                if fmt.upper() == target_blade_format:
                    format_matches.append(match_result)
                else:
                    other_matches.append(match_result)

        # Return format match if found, otherwise fall back to other matches
        if format_matches:
            return format_matches[0]  # Return first format match
        elif other_matches:
            return other_matches[0]  # Return first other match

        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,
        }
