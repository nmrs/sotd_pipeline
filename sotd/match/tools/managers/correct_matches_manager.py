#!/usr/bin/env python3
"""Correct matches management utilities for mismatch analysis."""

from pathlib import Path
from typing import Dict, Set

import yaml
from rich.console import Console

from sotd.utils.match_filter_utils import (
    load_competition_tags,
    normalize_for_matching,
    strip_competition_tags,
)

# Delimiter for item keys to avoid conflicts with characters in original text
# Simplified key format - no longer need delimiter


class CorrectMatchesManager:
    """Manages loading, saving, and querying of correct matches."""

    def __init__(self, console: Console, correct_matches_file: Path | None = None):
        self.console = console
        self._correct_matches_file = correct_matches_file or Path("data/correct_matches.yaml")
        self._correct_matches: Set[str] = set()
        self._correct_matches_data = {}
        # Load existing data if file exists
        self.load_correct_matches()

    def _load_competition_tags(self) -> Dict[str, list]:
        """Load competition tags configuration."""
        return load_competition_tags()

    def _strip_competition_tags(self, value: str, competition_tags: Dict[str, list]) -> str:
        """
        Strip competition tags from a string while preserving useful ones.

        Args:
            value: Input string that may contain competition tags
            competition_tags: Configuration of tags to strip/preserve

        Returns:
            String with unwanted competition tags removed
        """
        return strip_competition_tags(value, competition_tags)

    def _normalize_for_matching(self, value: str, field: str) -> str:
        """
        Normalize a string for storage in correct_matches.yaml.

        This strips competition tags and normalizes whitespace to prevent
        bloat and duplicates in the file.
        """
        return normalize_for_matching(value, None, field)

    def load_correct_matches(self) -> None:
        """Load previously marked correct matches from file."""
        self._correct_matches = set()
        self._correct_matches_data = {}
        if not self._correct_matches_file.exists():
            return

        try:
            with self._correct_matches_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return
                for field, field_data in data.items():
                    if isinstance(field_data, dict):
                        if field == "blade":
                            # Handle format-aware structure for blade field
                            for format_name, format_data in field_data.items():
                                if isinstance(format_data, dict):
                                    for brand, brand_data in format_data.items():
                                        if isinstance(brand_data, dict):
                                            for model, strings in brand_data.items():
                                                if isinstance(strings, list):
                                                    for original in strings:
                                                        # Use simplified key format
                                                        match_key = (
                                                            f"{field}:{original.lower().strip()}"
                                                        )
                                                        self._correct_matches.add(match_key)
                                                        self._correct_matches_data[match_key] = {
                                                            "original": original,
                                                            "matched": {
                                                                "brand": brand,
                                                                "model": model,
                                                                "format": format_name,
                                                            },
                                                            "field": field,
                                                        }
                        elif field in ["handle", "knot"]:
                            # Handle handle and knot sections
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for original in strings:
                                                # Use simplified key format
                                                match_key = f"{field}:{original.lower().strip()}"
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
                                                    "field": field,
                                                }
                        elif field == "brush":
                            # Handle brush field - support both strings and dictionaries
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, patterns in brand_data.items():
                                        if isinstance(patterns, list):
                                            for pattern in patterns:
                                                if isinstance(pattern, dict):
                                                    # Dictionary with handle_match flag
                                                    # YAML format: {key: {handle_match: true}}
                                                    original_text = list(pattern.keys())[0]
                                                    handle_match_enabled = pattern[
                                                        original_text
                                                    ].get("handle_match", False)
                                                else:
                                                    # Simple string pattern
                                                    original_text = pattern
                                                    handle_match_enabled = False

                                                # Use simplified key format
                                                match_key = (
                                                    f"{field}:{original_text.lower().strip()}"
                                                )
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original_text,
                                                    "matched": {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
                                                    "field": field,
                                                    "handle_match_enabled": handle_match_enabled,
                                                }
                        elif field == "split_brush":
                            # Handle split_brush section
                            for original, components in field_data.items():
                                if isinstance(components, dict):
                                    handle_component = components.get("handle", "")
                                    knot_component = components.get("knot", "")

                                    # Create a combined key for split brush
                                    combined_components = (
                                        f"{handle_component} || {knot_component}".lower().strip()
                                    )
                                    match_key = f"brush:{original.lower().strip()}"
                                    self._correct_matches.add(match_key)
                                    self._correct_matches_data[match_key] = {
                                        "original": original,
                                        "matched": {
                                            "brand": None,
                                            "model": None,
                                            "handle": {
                                                "brand": (
                                                    handle_component.split(" ", 1)[0]
                                                    if handle_component
                                                    else ""
                                                ),
                                                "model": (
                                                    handle_component.split(" ", 1)[1]
                                                    if handle_component and " " in handle_component
                                                    else handle_component
                                                ),
                                            },
                                            "knot": {
                                                "brand": (
                                                    knot_component.split(" ", 1)[0]
                                                    if knot_component
                                                    else ""
                                                ),
                                                "model": (
                                                    knot_component.split(" ", 1)[1]
                                                    if knot_component and " " in knot_component
                                                    else knot_component
                                                ),
                                            },
                                        },
                                        "field": "brush",
                                    }
                        else:
                            # Handle flat structure for other fields
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for original in strings:
                                                brand_model = (brand + " " + model).lower().strip()
                                                match_key = f"{field}:{original.lower().strip()}"
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": {
                                                        "brand": (
                                                            brand
                                                            if field in ("razor", "blade", "brush")
                                                            else None
                                                        ),
                                                        "model": (
                                                            model
                                                            if field in ("razor", "blade", "brush")
                                                            else None
                                                        ),
                                                        "maker": brand if field == "soap" else None,
                                                        "scent": model if field == "soap" else None,
                                                    },
                                                    "field": field,
                                                }
        except Exception as e:
            self.console.print(f"[red]Error loading correct matches: {e}[/red]")

    def save_correct_matches(self) -> None:
        """Save correct matches to file."""
        try:
            # Group by field
            field_data = {}
            for match_key, match_data in self._correct_matches_data.items():
                field, original = match_key.split(":", 1)

                if field not in field_data:
                    field_data[field] = {}

                if field == "blade":
                    # Handle format-aware structure for blade field
                    brand = match_data["matched"]["brand"]
                    model = match_data["matched"]["model"]
                    format_name = match_data["matched"].get(
                        "format", "DE"
                    )  # Default to DE if not specified

                    if format_name not in field_data[field]:
                        field_data[field][format_name] = {}
                    if brand not in field_data[field][format_name]:
                        field_data[field][format_name][brand] = {}
                    if model not in field_data[field][format_name][brand]:
                        field_data[field][format_name][brand][model] = []

                    # Normalize the original string before storing to prevent bloat
                    normalized_original = self._normalize_for_matching(original, field)
                    if (
                        normalized_original
                        and normalized_original not in field_data[field][format_name][brand][model]
                    ):
                        field_data[field][format_name][brand][model].append(normalized_original)

                elif field == "soap":
                    maker = match_data["matched"]["maker"]
                    scent = match_data["matched"]["scent"]
                    if maker not in field_data[field]:
                        field_data[field][maker] = {}
                    if scent not in field_data[field][maker]:
                        field_data[field][maker][scent] = []
                    # Normalize the original string before storing to prevent bloat
                    normalized_original = self._normalize_for_matching(original, field)
                    if (
                        normalized_original
                        and normalized_original not in field_data[field][maker][scent]
                    ):
                        field_data[field][maker][scent].append(normalized_original)
                elif field == "brush":
                    # Handle brush field - check for split brush structure
                    matched = match_data["matched"]

                    if self._is_split_brush(matched):
                        # Split brush - save to new structure
                        handle_component, knot_component, handle_brand, knot_brand = (
                            self._extract_split_brush_components(matched)
                        )

                        # Initialize split_brush section if not exists
                        if "split_brush" not in field_data:
                            field_data["split_brush"] = {}

                        # Save split brush mapping - store in lowercase for consistency with lookup
                        normalized_original = original.lower().strip()
                        field_data["split_brush"][normalized_original] = {
                            "handle": (
                                handle_component.lower().strip() if handle_component else ""
                            ),
                            "knot": (knot_component.lower().strip() if knot_component else ""),
                        }

                        # Save handle component to handle section
                        if handle_component and handle_brand:
                            if "handle" not in field_data:
                                field_data["handle"] = {}

                            # Use the proper brand and model names from the matched data
                            # The brand and model should come directly from the catalog, not be split
                            # For handle components, we need to get the actual brand and model from
                            # the matched data
                            handle = match_data["matched"].get("handle", {})
                            if isinstance(handle, dict):
                                actual_brand = handle.get("brand", handle_brand)
                                actual_model = handle.get("model", "")
                                if not actual_model and actual_brand != handle_component:
                                    # If no model specified, use the component as model
                                    actual_model = handle_component
                            else:
                                actual_brand = handle_brand
                                actual_model = handle_component

                            if actual_brand not in field_data["handle"]:
                                field_data["handle"][actual_brand] = {}
                            if actual_model not in field_data["handle"][actual_brand]:
                                field_data["handle"][actual_brand][actual_model] = []

                            # Store the original component (not lowercase) for consistency
                            if (
                                handle_component
                                not in field_data["handle"][actual_brand][actual_model]
                            ):
                                field_data["handle"][actual_brand][actual_model].append(
                                    handle_component
                                )

                        # Save knot component to knot section
                        if knot_component and knot_brand:
                            if "knot" not in field_data:
                                field_data["knot"] = {}

                            # Use the proper brand and model names from the matched data
                            # The brand and model should come directly from the catalog, not be split
                            # For knot components, we need to get the actual brand and model from
                            # the matched data
                            knot = match_data["matched"].get("knot", {})
                            if isinstance(knot, dict):
                                actual_brand = knot.get("brand", knot_brand)
                                actual_model = knot.get("model", "")
                                if not actual_model and actual_brand != knot_component:
                                    # If no model specified, use the component as model
                                    actual_model = knot_component
                            else:
                                actual_brand = knot_brand
                                actual_model = knot_component

                            if actual_brand not in field_data["knot"]:
                                field_data["knot"][actual_brand] = {}
                            if actual_model not in field_data["knot"][actual_brand]:
                                field_data["knot"][actual_brand][actual_model] = []

                            # Store the original component (not lowercase) for consistency
                            if knot_component not in field_data["knot"][actual_brand][actual_model]:
                                field_data["knot"][actual_brand][actual_model].append(
                                    knot_component
                                )
                    else:
                        # Regular brush - check if it has handle information
                        brand = match_data["matched"]["brand"]
                        model = match_data["matched"]["model"]
                        handle = match_data["matched"].get("handle")

                        if handle and isinstance(handle, dict):
                            # Complete brush with handle information - save with handle_match flag
                            if brand not in field_data[field]:
                                field_data[field][brand] = {}
                            if model not in field_data[field][brand]:
                                field_data[field][brand][model] = []

                            # Normalize the original string before storing to prevent bloat
                            normalized_original = self._normalize_for_matching(original, field)
                            if (
                                normalized_original
                                and normalized_original not in field_data[field][brand][model]
                            ):
                                # Save as a dictionary with handle_match flag
                                field_data[field][brand][model].append(
                                    {normalized_original: {"handle_match": True}}
                                )

                            # Also save the handle to the handle section
                            handle_brand = handle.get("brand", "")
                            handle_model = handle.get("model", "")
                            if handle_brand and handle_model:
                                if "handle" not in field_data:
                                    field_data["handle"] = {}
                                if handle_brand not in field_data["handle"]:
                                    field_data["handle"][handle_brand] = {}
                                if handle_model not in field_data["handle"][handle_brand]:
                                    field_data["handle"][handle_brand][handle_model] = []

                                # Store the original text that matched this handle
                                if (
                                    normalized_original
                                    and normalized_original
                                    not in field_data["handle"][handle_brand][handle_model]
                                ):
                                    field_data["handle"][handle_brand][handle_model].append(
                                        normalized_original
                                    )
                        else:
                            # Regular brush without handle information
                            if brand not in field_data[field]:
                                field_data[field][brand] = {}
                            if model not in field_data[field][brand]:
                                field_data[field][brand][model] = []
                            # Normalize the original string before storing to prevent bloat
                            normalized_original = self._normalize_for_matching(original, field)
                            if (
                                normalized_original
                                and normalized_original not in field_data[field][brand][model]
                            ):
                                field_data[field][brand][model].append(normalized_original)
                elif field == "handle":
                    # Handle handle field - support both old and new structures
                    if (
                        "handle_maker" in match_data["matched"]
                        and "handle_model" in match_data["matched"]
                    ):
                        # New structure
                        handle_maker = match_data["matched"]["handle_maker"]
                        handle_model = match_data["matched"]["handle_model"]
                    else:
                        # Old structure - extract from brand/model fields
                        handle_maker = match_data["matched"].get("brand", "")
                        handle_model = match_data["matched"].get("model", "")

                    if handle_maker not in field_data[field]:
                        field_data[field][handle_maker] = {}
                    if handle_model not in field_data[field][handle_maker]:
                        field_data[field][handle_maker][handle_model] = []
                    # Normalize the original string before storing to prevent bloat
                    normalized_original = self._normalize_for_matching(original, field)
                    if (
                        normalized_original
                        and normalized_original not in field_data[field][handle_maker][handle_model]
                    ):
                        field_data[field][handle_maker][handle_model].append(normalized_original)
                else:
                    # Handle flat structure for other fields
                    brand = match_data["matched"]["brand"]
                    model = match_data["matched"]["model"]
                    if brand not in field_data[field]:
                        field_data[field][brand] = {}
                    if model not in field_data[field][brand]:
                        field_data[field][brand][model] = []
                    # Normalize the original string before storing to prevent bloat
                    normalized_original = self._normalize_for_matching(original, field)
                    if (
                        normalized_original
                        and normalized_original not in field_data[field][brand][model]
                    ):
                        field_data[field][brand][model].append(normalized_original)

            # Alphabetize entries within each field/brand/model (or field/format/brand/model)
            for field_name, field_section in field_data.items():
                if isinstance(field_section, dict):
                    if field_name == "blade":
                        # For blade field, sort by format -> brand -> model
                        for format_name, format_data in field_section.items():
                            if isinstance(format_data, dict):
                                for brand, brand_data in format_data.items():
                                    if isinstance(brand_data, dict):
                                        for model, entries in brand_data.items():
                                            if isinstance(entries, list):
                                                # Sort entries alphabetically (case-insensitive)
                                                entries.sort(key=str.lower)
                    elif field_name in ["handle", "knot"]:
                        # For handle and knot sections, sort by brand -> model
                        for brand, brand_data in field_section.items():
                            if isinstance(brand_data, dict):
                                for model, entries in brand_data.items():
                                    if isinstance(entries, list):
                                        # Sort entries alphabetically (case-insensitive)
                                        entries.sort(key=str.lower)
                    else:
                        # For other fields, sort by brand -> model
                        for brand, brand_data in field_section.items():
                            if isinstance(brand_data, dict):
                                for model, entries in brand_data.items():
                                    if isinstance(entries, list):
                                        # Sort entries alphabetically (case-insensitive)
                                        # Handle both strings and dictionaries
                                        def sort_key(item):
                                            if isinstance(item, dict):
                                                # For dictionaries, use the first key
                                                return list(item.keys())[0].lower()
                                            else:
                                                return str(item).lower()

                                        entries.sort(key=sort_key)

            # Save to file
            with self._correct_matches_file.open("w", encoding="utf-8") as f:
                yaml.dump(
                    field_data, f, default_flow_style=False, sort_keys=True, allow_unicode=True
                )

            self.console.print(
                f"[green]Correct matches saved to {self._correct_matches_file}[/green]"
            )
        except Exception as e:
            self.console.print(f"[red]Error saving correct matches: {e}[/red]")

    def get_correct_matches_by_field(self, field: str) -> Set[str]:
        """Get correct matches for a specific field."""
        return {key for key in self._correct_matches if key.startswith(f"{field}:")}

    def display_correct_matches_summary(self) -> None:
        """Display summary of correct matches by field."""
        if not self._correct_matches:
            self.console.print("[yellow]No correct matches found[/yellow]")
            return

        self.console.print("\n[bold]Correct Matches Summary:[/bold]")
        for field in ["razor", "blade", "brush", "soap"]:
            field_matches = self.get_correct_matches_by_field(field)
            if field_matches:
                self.console.print(f"  • {field.capitalize()}: [green]{len(field_matches)}[/green]")
            else:
                self.console.print(f"  • {field.capitalize()}: [yellow]0[/yellow]")

    def clear_correct_matches(self) -> None:
        """Clear all correct matches."""
        self._correct_matches.clear()
        self._correct_matches_data.clear()
        if self._correct_matches_file.exists():
            self._correct_matches_file.unlink()
        self.console.print("[green]All correct matches cleared[/green]")

    def clear_correct_matches_by_field(self, field: str) -> None:
        """Clear correct matches for a specific field."""
        field_matches = self.get_correct_matches_by_field(field)
        for match_key in field_matches:
            self._correct_matches.discard(match_key)
            self._correct_matches_data.pop(match_key, None)

        # Re-save to update the file
        self.save_correct_matches()
        self.console.print(f"[green]Correct matches for {field} cleared[/green]")

    def is_match_correct(self, match_key: str) -> bool:
        """Check if a match is marked as correct."""
        return match_key in self._correct_matches

    def mark_match_as_correct(self, match_key: str, match_data: Dict) -> None:
        """Mark a match as correct."""
        self._correct_matches.add(match_key)
        self._correct_matches_data[match_key] = match_data

    def create_match_key(self, field: str, original: str, matched: Dict) -> str:
        """Create a unique key for a match based on field and original text."""
        # Normalize for consistent key generation
        original_normalized = self._normalize_for_matching(original, field).lower().strip()
        # Use just the normalized original text as the key
        key = f"{field}:{original_normalized}"
        return key

    # _get_matched_text method removed - no longer needed with simplified keys

    def _is_split_brush(self, matched: Dict) -> bool:
        """Check if a brush match is a split brush."""
        # A brush is a split brush if the top-level model is None
        # This means it wasn't matched as a complete brush, so it should be treated as split
        # Known brushes can have handle/knot components but still have a top-level model
        return matched.get("model") is None

    def _extract_split_brush_components(self, matched: Dict) -> tuple[str, str, str, str]:
        """
        Extract handle and knot components from split brush data.

        Returns:
            tuple: (handle_source_text, knot_source_text, handle_brand, knot_brand)
        """
        handle_component = ""
        knot_component = ""
        handle_brand = ""
        knot_brand = ""

        # Extract handle component
        handle = matched.get("handle")
        if handle:
            if isinstance(handle, dict):
                # Use canonical brand/model from matcher, not source_text
                handle_brand = handle.get("brand", "")
                handle_model = handle.get("model", "")
                # Construct canonical component from brand/model
                if handle_brand and handle_model:
                    handle_component = f"{handle_brand} {handle_model}".strip()
                elif handle_brand:
                    handle_component = handle_brand
                else:
                    # Fallback to source_text only if no canonical data available
                    handle_component = handle.get("source_text", "")
            elif isinstance(handle, str):
                handle_component = handle

        # Extract knot component
        knot = matched.get("knot")
        if knot:
            if isinstance(knot, dict):
                # Use canonical brand/model from matcher, not source_text
                knot_brand = knot.get("brand", "")
                knot_model = knot.get("model", "")
                # Construct canonical component from brand/model
                if knot_brand and knot_model:
                    knot_component = f"{knot_brand} {knot_model}".strip()
                elif knot_brand:
                    knot_component = knot_brand
                else:
                    # Fallback to source_text only if no canonical data available
                    knot_component = knot.get("source_text", "")
            elif isinstance(knot, str):
                knot_component = knot

        # Return source_text (for split_brush section) and brand names (for handle/knot sections)
        handle_result = handle_component.strip() if handle_component else ""
        knot_result = knot_component.strip() if knot_component else ""
        return handle_result, knot_result, handle_brand, knot_brand
