import re
from pathlib import Path
from typing import Optional

import yaml

from sotd.match.types import MatchResult
from sotd.match.utils.regex_error_utils import compile_regex_with_context, create_context_dict


class HandleMatcher:
    """Handle matching functionality extracted from BrushMatcher."""

    def __init__(self, handles_path: Path = Path("data/handles.yaml")):
        self.handles_path = handles_path
        self.handles_data = self._load_catalog(handles_path)
        self.handle_patterns = self._compile_handle_patterns()

    def _load_catalog(self, catalog_path: Path) -> dict:
        """Load handle catalog from YAML file."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    def _compile_handle_patterns(self) -> list[dict]:
        """Compile handle patterns from the handles catalog in priority order."""
        patterns = []

        def _process_section(section_data: dict, section_name: str, priority: int):
            """Process a section of handle data efficiently."""
            for handle_maker, data in section_data.items():
                if not isinstance(data, dict):
                    continue

                # New structure: brand -> model -> patterns
                for model_name, model_data in data.items():
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        for pattern in model_data["patterns"]:
                            context = create_context_dict(
                                file_path=str(self.handles_path),
                                brand=handle_maker,
                                model=model_name,
                                section=section_name,
                            )
                            compiled_regex = compile_regex_with_context(pattern, context)
                            patterns.append(
                                {
                                    "maker": handle_maker,
                                    "model": model_name,
                                    "pattern": pattern,
                                    "regex": compiled_regex,
                                    "section": section_name,
                                    "priority": priority,
                                }
                            )

        # Process all sections
        _process_section(self.handles_data.get("artisan_handles", {}), "artisan_handles", 1)
        _process_section(
            self.handles_data.get("manufacturer_handles", {}), "manufacturer_handles", 2
        )
        _process_section(self.handles_data.get("other_handles", {}), "other_handles", 3)

        # Sort by priority (lower = higher), then by pattern length (longer = more specific)
        patterns.sort(key=lambda x: (x["priority"], -len(x["pattern"])))
        return patterns

    def match(self, text: str) -> Optional[MatchResult]:
        """
        Match handle maker from text using the handle patterns.
        Returns MatchResult with section/priority information or None if no match.
        """
        if not text:
            return None

        for pattern_info in self.handle_patterns:
            if pattern_info["regex"].search(text):
                matched_data = {
                    "handle_maker": pattern_info["maker"],
                    "handle_model": pattern_info["model"],
                    "_matched_by_section": pattern_info["section"],
                    "_pattern_used": pattern_info["pattern"],
                    "_source_text": text,
                }
                return MatchResult(
                    original=text,
                    matched=matched_data,
                    match_type="regex",
                    pattern=pattern_info["pattern"],
                    section=pattern_info["section"],
                    priority=pattern_info["priority"],
                    score=0.0,  # Handle matcher doesn't have scoring, explicitly set to 0
                )

        return None

    def match_handle_maker(self, text: str) -> Optional[dict]:
        """
        Match handle maker from text using the handle patterns.
        Returns dict with maker, model, and metadata or None if no match.
        """
        result = self.match(text)
        return result.matched if result else None

    def is_known_handle_maker(self, brand: str) -> bool:
        """Check if a brand is a known handle maker."""
        if not brand:
            return False

        # Check all sections of the handles catalog
        for section in ["artisan_handles", "manufacturer_handles", "other_handles"]:
            if brand.lower() in {
                maker.lower() for maker in self.handles_data.get(section, {}).keys()
            }:
                return True

        return False

    def resolve_handle_maker(self, updated: dict, value: str) -> None:
        """
        Resolve and set handle_maker and handle_model fields in the match result.
        This method handles the logic for determining the handle maker and model
        from the input text.
        """
        # If handle_maker is already set, don't override it
        if updated.get("handle_maker"):
            return

        # Try to match handle maker from the full text
        handle_result: Optional[dict] = self.match_handle_maker(value)
        if handle_result:
            updated["handle_maker"] = handle_result["handle_maker"]
            updated["handle_model"] = handle_result["handle_model"]
            # Preserve metadata if not already present
            if "_matched_by_section" not in updated:
                updated["_matched_by_section"] = handle_result["_matched_by_section"]
            if "_pattern_used" not in updated:
                updated["_pattern_used"] = handle_result["_pattern_used"]
            return

        # If no direct match, try to extract from brand field
        brand = updated.get("brand", "").strip()
        if brand and self.is_known_handle_maker(brand):
            updated["handle_maker"] = brand
            updated["handle_model"] = "Unspecified"
            return

        # If still no match, try to extract from model field
        model = updated.get("model", "").strip()
        if model:
            model_handle_result: Optional[dict] = self.match_handle_maker(model)
            if model_handle_result:
                updated["handle_maker"] = model_handle_result["handle_maker"]
                updated["handle_model"] = model_handle_result["handle_model"]
                if "_matched_by_section" not in updated:
                    updated["_matched_by_section"] = model_handle_result["_matched_by_section"]
                if "_pattern_used" not in updated:
                    updated["_pattern_used"] = model_handle_result["_pattern_used"]
                return

    def score_as_handle(self, text: str) -> int:
        """Score how likely a text is to be a handle (higher = more likely handle)."""
        score = 0
        text_lower = text.lower()

        # Strong handle indicators
        if "handle" in text_lower:
            score += 10

        # Test against actual handle patterns from handles.yaml
        handle_match = self.match_handle_maker(text)
        if handle_match:
            # Found a handle pattern match - strong indicator this is a handle
            section = handle_match.get("_matched_by_section", "")
            if section == "artisan_handles":
                score += 12  # Artisan handles are most specific
            elif section == "manufacturer_handles":
                score += 10
            elif section == "other_handles":
                score += 8
            else:
                score += 6

        # Handle-related terms
        handle_terms = ["stock", "custom", "artisan", "turned", "wood", "resin", "zebra", "burl"]
        for term in handle_terms:
            if term in text_lower:
                score += 2

        # Knot indicators (negative score for handle likelihood)
        knot_terms = ["badger", "boar", "synthetic", "syn", "mm", "knot"]
        for term in knot_terms:
            if term in text_lower:
                score -= 5

        # Fiber type patterns (strong knot indicators)
        if any(fiber in text_lower for fiber in ["badger", "boar", "synthetic"]):
            score -= 8

        # Size patterns (knot indicators)
        if re.search(r"\d{2}\s*mm", text_lower):
            score -= 6

        # Chisel & Hound versioning patterns (knot indicators)
        if re.search(r"\bv\d{2}\b", text_lower):
            score -= 6

        return score
