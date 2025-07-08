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


class CorrectMatchesManager:
    """Manages loading, saving, and querying of correct matches."""

    def __init__(self, console: Console, correct_matches_file: Path | None = None):
        self.console = console
        self._correct_matches_file = correct_matches_file or Path("data/correct_matches.yaml")
        self._correct_matches: Set[str] = set()
        self._correct_matches_data = {}

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
                        for brand, brand_data in field_data.items():
                            if isinstance(brand_data, dict):
                                for model, strings in brand_data.items():
                                    if isinstance(strings, list):
                                        for original in strings:
                                            match_key = (
                                                f"{field}:{original.lower().strip()}|"
                                                f"{(brand + ' ' + model).lower().strip()}"
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
                original, matched = rest.split("|", 1)

                if field not in field_data:
                    field_data[field] = {}

                if field == "soap":
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
                else:
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

            # Save to file
            with self._correct_matches_file.open("w", encoding="utf-8") as f:
                yaml.dump(field_data, f, default_flow_style=False, sort_keys=False)

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
        return f"{field}:{original_normalized}|{matched_normalized}"

    def _get_matched_text(self, field: str, matched: Dict) -> str:
        """Extract matched text from matched data."""
        if field == "soap":
            maker = matched.get("maker", "")
            scent = matched.get("scent", "")
            return f"{maker} {scent}".strip()
        else:
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            return f"{brand} {model}".strip()
