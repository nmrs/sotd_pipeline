#!/usr/bin/env python3
"""Correct matches management utilities for mismatch analysis."""

import re
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
ITEM_KEY_DELIMITER = "|||"


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
                                                        brand_model = (
                                                            (brand + " " + model).lower().strip()
                                                        )
                                                        match_key = (
                                                            f"{field}:{original.lower().strip()}"
                                                            f"{ITEM_KEY_DELIMITER}"
                                                            f"{brand_model}"
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
                                                brand_model = (brand + " " + model).lower().strip()
                                                match_key = (
                                                    f"{field}:{original.lower().strip()}"
                                                    f"{ITEM_KEY_DELIMITER}{brand_model}"
                                                )
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
                                                    "field": field,
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
                                    match_key = (
                                        f"brush:{original.lower().strip()}"
                                        f"{ITEM_KEY_DELIMITER}{combined_components}"
                                    )
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
                                                match_key = (
                                                    f"{field}:{original.lower().strip()}"
                                                    f"{ITEM_KEY_DELIMITER}{brand_model}"
                                                )
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
                field, rest = match_key.split(":", 1)
                original, matched = rest.split(ITEM_KEY_DELIMITER, 1)

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

                        # Save split brush mapping - store in lowercase for consistency with lookup strings
                        normalized_original = original.lower().strip()
                        field_data["split_brush"][normalized_original] = {
                            "handle": handle_component.lower().strip() if handle_component else "",
                            "knot": knot_component.lower().strip() if knot_component else "",
                        }

                        # Save handle component to handle section
                        if handle_component and handle_brand:
                            if "handle" not in field_data:
                                field_data["handle"] = {}

                            # Use the proper brand name from the matched data
                            # For the model, extract just the model part (remove brand name)
                            handle_model = handle_component
                            if handle_brand.lower() in handle_component.lower():
                                # Remove brand name from the beginning of source_text
                                # Use case-insensitive replacement to handle multi-word brands
                                handle_model = re.sub(
                                    f"^{re.escape(handle_brand)}", 
                                    "", 
                                    handle_component, 
                                    flags=re.IGNORECASE
                                ).strip()
                                if not handle_model:
                                    handle_model = handle_component  # Fallback to full text

                            if handle_brand not in field_data["handle"]:
                                field_data["handle"][handle_brand] = {}
                            if handle_model not in field_data["handle"][handle_brand]:
                                field_data["handle"][handle_brand][handle_model] = []

                            # Store in lowercase for consistency
                            normalized_component = handle_component.lower().strip()
                            if (
                                normalized_component
                                not in field_data["handle"][handle_brand][handle_model]
                            ):
                                field_data["handle"][handle_brand][handle_model].append(
                                    normalized_component
                                )

                        # Save knot component to knot section
                        if knot_component and knot_brand:
                            if "knot" not in field_data:
                                field_data["knot"] = {}

                            # Use the proper brand name from the matched data
                            # For the model, extract just the model part (remove brand name)
                            knot_model = knot_component
                            if knot_brand.lower() in knot_component.lower():
                                # Remove brand name from the beginning of source_text
                                # Use case-insensitive replacement to handle multi-word brands
                                knot_model = re.sub(
                                    f"^{re.escape(knot_brand)}", 
                                    "", 
                                    knot_component, 
                                    flags=re.IGNORECASE
                                ).strip()
                                if not knot_model:
                                    knot_model = knot_component  # Fallback to full text

                            if knot_brand not in field_data["knot"]:
                                field_data["knot"][knot_brand] = {}
                            if knot_model not in field_data["knot"][knot_brand]:
                                field_data["knot"][knot_brand][knot_model] = []

                            # Store in lowercase for consistency
                            normalized_component = knot_component.lower().strip()
                            if (
                                normalized_component
                                not in field_data["knot"][knot_brand][knot_model]
                            ):
                                field_data["knot"][knot_brand][knot_model].append(
                                    normalized_component
                                )
                    else:
                        # Regular brush - save to brush section
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
                                        entries.sort(key=str.lower)

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
        """Create a unique key for a match based on field, original text, and matched data."""
        matched_text = self._get_matched_text(field, matched)
        # Normalize for consistent key generation
        original_normalized = original.lower().strip()
        matched_normalized = matched_text.lower().strip()
        # Use ITEM_KEY_DELIMITER to avoid conflicts with | in original text
        key = f"{field}:{original_normalized}{ITEM_KEY_DELIMITER}{matched_normalized}"
        return key

    def _get_matched_text(self, field: str, matched: Dict) -> str:
        """Extract matched text from matched data."""
        if field == "soap":
            maker = matched.get("maker", "")
            scent = matched.get("scent", "")
            return f"{maker} {scent}".strip()
        elif field == "brush":
            # Handle split brush structure
            if "handle" in matched and "knot" in matched:
                # Split brush - extract handle and knot components
                handle = matched.get("handle", {})
                knot = matched.get("knot", {})

                handle_brand = handle.get("brand", "")
                handle_model = handle.get("model", "")
                knot_brand = knot.get("brand", "")
                knot_model = knot.get("model", "")

                # For split brushes, we need to handle handle and knot separately
                # This method is used for key generation, so we'll return a combined string
                # The actual saving will be handled in save_correct_matches
                return f"{handle_brand} {handle_model} || {knot_brand} {knot_model}".strip()
            else:
                # Simple brush structure
                brand = matched.get("brand", "")
                model = matched.get("model", "")
                return f"{brand} {model}".strip()
        else:
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            # Don't include format in key generation since YAML structure doesn't support it
            return f"{brand} {model}".strip()

    def _is_split_brush(self, matched: Dict) -> bool:
        """Check if a brush match is a split brush."""
        return (
            matched.get("brand") is None
            and matched.get("model") is None
            and ("handle" in matched or "knot" in matched)
        )

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
                # Use source_text if available (actual split text), otherwise construct from brand/model
                source_text = handle.get("source_text")
                if source_text:
                    handle_component = source_text
                else:
                    handle_brand = handle.get("brand", "")
                    handle_model = handle.get("model", "")
                    handle_component = f"{handle_brand} {handle_model}".strip()
                # Always preserve the brand name for proper casing
                handle_brand = handle.get("brand", "")
            elif isinstance(handle, str):
                handle_component = handle

        # Extract knot component
        knot = matched.get("knot")
        if knot:
            if isinstance(knot, dict):
                # Use source_text if available (actual split text), otherwise construct from brand/model
                source_text = knot.get("source_text")
                if source_text:
                    knot_component = source_text
                else:
                    knot_brand = knot.get("brand", "")
                    knot_model = knot.get("model", "")
                    knot_component = f"{knot_brand} {knot_model}".strip()
                # Always preserve the brand name for proper casing
                knot_brand = knot.get("brand", "")
            elif isinstance(knot, str):
                knot_component = knot

        # Return source_text (for split_brush section) and brand names (for handle/knot sections)
        handle_result = handle_component.strip() if handle_component else ""
        knot_result = knot_component.strip() if knot_component else ""
        return handle_result, knot_result, handle_brand, knot_brand
