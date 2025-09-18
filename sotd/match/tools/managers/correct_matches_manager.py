#!/usr/bin/env python3
"""Correct matches management utilities for mismatch analysis."""

from pathlib import Path
from typing import Dict, Set

import yaml
from rich.console import Console

from sotd.utils.competition_tags import load_competition_tags, strip_competition_tags
from sotd.utils.extract_normalization import normalize_for_matching

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
                                                        # Normalize for consistent key generation
                                                        match_key = self.create_match_key(
                                                            field,
                                                            original,
                                                            {
                                                                "brand": brand,
                                                                "model": model,
                                                                # PRESERVE FORMAT!
                                                                "format": format_name,
                                                            },
                                                        )
                                                        self._correct_matches.add(match_key)
                                                        self._correct_matches_data[match_key] = {
                                                            "original": original,
                                                            "matched": {
                                                                "brand": brand,
                                                                "model": model,
                                                                # PRESERVE FORMAT!
                                                                "format": format_name,
                                                            },
                                                            "field": field,
                                                        }
                        elif field in ["handle", "knot"]:
                            # Handle handle and knot sections - preserve source_text for composite brushes
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for original in strings:
                                                # Use consistent normalization for key generation
                                                match_key = self.create_match_key(
                                                    field,
                                                    original,
                                                    {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
                                                )
                                                self._correct_matches.add(match_key)

                                                # For composite brushes, preserve the source_text field
                                                # The source_text should be the full original text from the composite brush
                                                matched_data = {
                                                    "brand": brand,
                                                    "model": model,
                                                    "source_text": original,  # Preserve source_text
                                                }

                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": matched_data,
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

                                                # Use consistent normalization for key generation
                                                match_key = self.create_match_key(
                                                    field,
                                                    original_text,
                                                    {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
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

                        else:
                            # Handle flat structure for other fields
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for original in strings:
                                                # Use consistent normalization for key generation
                                                match_key = self.create_match_key(
                                                    field,
                                                    original,
                                                    {
                                                        "brand": brand,
                                                        "model": model,
                                                    },
                                                )
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": {
                                                        "brand": (
                                                            brand
                                                            if field
                                                            in ("razor", "blade", "brush", "soap")
                                                            else None
                                                        ),
                                                        "model": (
                                                            model
                                                            if field in ("razor", "blade", "brush")
                                                            else None
                                                        ),
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
                    brand = match_data["matched"]["brand"]
                    scent = match_data["matched"]["scent"]
                    if brand not in field_data[field]:
                        field_data[field][brand] = {}
                    if scent not in field_data[field][brand]:
                        field_data[field][brand][scent] = []
                    # Normalize the original string before storing to prevent bloat
                    normalized_original = self._normalize_for_matching(original, field)
                    if (
                        normalized_original
                        and normalized_original not in field_data[field][brand][scent]
                    ):
                        field_data[field][brand][scent].append(normalized_original)
                elif field == "brush":
                    # Check if this is a split brush (composite brush with handle/knot components)
                    handle = match_data["matched"].get("handle")
                    knot = match_data["matched"].get("knot")

                    if handle or knot:
                        # This is a split brush - save to handle and knot sections
                        if handle:
                            handle_brand = handle.get("brand")
                            handle_model = handle.get("model")

                            # Use _no_brand and _no_model when brand/model is missing
                            if not handle_brand:
                                handle_brand = "_no_brand"
                            if not handle_model:
                                handle_model = "_no_model"

                            # Save to handle section
                            if "handle" not in field_data:
                                field_data["handle"] = {}
                            if handle_brand not in field_data["handle"]:
                                field_data["handle"][handle_brand] = {}
                            if handle_model not in field_data["handle"][handle_brand]:
                                field_data["handle"][handle_brand][handle_model] = []

                            # Always use the full normalized text for handle/knot sections
                            # This ensures the CorrectMatchesStrategy can find the full string
                            normalized_handle_text = self._normalize_for_matching(
                                original, "handle"
                            )
                            if (
                                normalized_handle_text
                                and normalized_handle_text
                                not in field_data["handle"][handle_brand][handle_model]
                            ):
                                field_data["handle"][handle_brand][handle_model].append(
                                    normalized_handle_text
                                )

                        if knot:
                            knot_brand = knot.get("brand")
                            knot_model = knot.get("model")

                            # Use _no_brand when brand is missing, keep actual model or use _no_model
                            if not knot_brand:
                                knot_brand = "_no_brand"
                            if not knot_model:
                                knot_model = "_no_model"

                            # Save to knot section
                            if "knot" not in field_data:
                                field_data["knot"] = {}
                            if knot_brand not in field_data["knot"]:
                                field_data["knot"][knot_brand] = {}
                            if knot_model not in field_data["knot"][knot_brand]:
                                field_data["knot"][knot_brand][knot_model] = []

                            # Always use the full normalized text for handle/knot sections
                            # This ensures the CorrectMatchesStrategy can find the full string
                            normalized_knot_text = self._normalize_for_matching(original, "knot")
                            if (
                                normalized_knot_text
                                and normalized_knot_text
                                not in field_data["knot"][knot_brand][knot_model]
                            ):
                                field_data["knot"][knot_brand][knot_model].append(
                                    normalized_knot_text
                                )
                    else:
                        # This is a regular brush - save to brush section
                        brand = match_data["matched"]["brand"]
                        model = match_data["matched"]["model"]

                        # Initialize brand and model dictionaries if they don't exist
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
        # First check if it's directly in the correct matches set
        if match_key in self._correct_matches:
            return True

        # For brush field, also check if it can be found by the CorrectMatchesChecker
        # This handles cases where automated splits are saved to handle/knot sections
        if match_key.startswith("brush:"):
            try:
                from sotd.match.correct_matches import CorrectMatchesChecker
                import yaml

                # Load the YAML data structure for the checker
                if self._correct_matches_file.exists():
                    with self._correct_matches_file.open("r", encoding="utf-8") as f:
                        yaml_data = yaml.safe_load(f)

                    checker = CorrectMatchesChecker(yaml_data)
                    original_text = match_key.split(":", 1)[1]  # Extract original text from key
                    result = checker.check(original_text)
                    return result is not None
            except Exception:
                # If there's an error with the checker, fall back to the original behavior
                return False

        return False

    def mark_match_as_correct(self, match_key: str, match_data: Dict) -> None:
        """Mark a match as correct."""
        self._correct_matches.add(match_key)
        self._correct_matches_data[match_key] = match_data

    def remove_match(self, field: str, original: str, matched: Dict) -> bool:
        """
        Remove a match from correct matches.

        Args:
            field: The field name (e.g., 'brush', 'razor')
            original: The original text that was matched
            matched: The matched data dictionary

        Returns:
            True if the match was found and removed, False otherwise
        """
        match_key = self.create_match_key(field, original, matched)

        if match_key in self._correct_matches:
            self._correct_matches.discard(match_key)
            self._correct_matches_data.pop(match_key, None)
            return True
        return False

    def remove_match_by_key(self, match_key: str) -> bool:
        """
        Remove a match from correct matches by its key.

        Args:
            match_key: The match key to remove

        Returns:
            True if the match was found and removed, False otherwise
        """
        if match_key in self._correct_matches:
            self._correct_matches.discard(match_key)
            self._correct_matches_data.pop(match_key, None)
            return True
        return False

    def create_match_key(self, field: str, original: str, matched: Dict) -> str:
        """Create a unique key for a match based on field and original text."""
        # Normalize for consistent key generation
        original_normalized = self._normalize_for_matching(original, field).lower().strip()
        # Use just the normalized original text as the key
        key = f"{field}:{original_normalized}"
        return key

    # _get_matched_text method removed - no longer needed with simplified keys
