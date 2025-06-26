#!/usr/bin/env python3
"""Mismatch detection logic for analyzing potential regex mismatches."""

from typing import Dict, List

from rich.console import Console

from sotd.match.tools.correct_matches_manager import CorrectMatchesManager
from sotd.match.tools.pattern_manager import PatternManager


class MismatchDetector:
    """Detects potential mismatches in matched data."""

    def __init__(self, console: Console):
        self.console = console
        self.pattern_manager = PatternManager(console)
        self.correct_matches_manager = CorrectMatchesManager(console)

    def identify_mismatches(self, data: Dict, field: str, args) -> Dict[str, List[Dict]]:
        """Identify potential mismatches in the data for a given field."""
        mismatches = {
            "multiple_patterns": [],
            "levenshtein_distance": [],
            "low_confidence": [],
            "exact_matches": [],
        }

        # Extract the actual records from the data structure
        records = data.get("data", [])
        if not records:
            self.console.print("[yellow]No records found in data[/yellow]")
            return mismatches

        # Pre-load catalog patterns to avoid repeated loading
        catalog_patterns = self.pattern_manager.load_catalog_patterns(field)

        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue

            original = field_data.get("original", "")
            matched = field_data.get("matched", {})
            pattern = field_data.get("pattern", "")
            match_type = field_data.get("match_type", "")
            confidence = field_data.get("confidence", 1.0)

            if not original or not matched:
                continue

            # Skip exact matches (from correct_matches.yaml) - these are already confirmed correct
            if match_type == "exact":
                mismatches["exact_matches"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": self.correct_matches_manager.create_match_key(
                            field, original, matched
                        ),
                        "reason": "Exact match from correct_matches.yaml",
                    }
                )
                continue  # Skip further analysis for exact matches

            # Create a unique key for this match
            match_key = self.correct_matches_manager.create_match_key(field, original, matched)

            # Skip if this match was previously marked as correct (unless showing correct matches)
            if self.correct_matches_manager.is_match_correct(match_key) and not args.show_correct:
                continue

            # Check for multiple regex patterns (only if we have catalog patterns)
            if catalog_patterns:
                multiple_patterns = self.pattern_manager.find_multiple_pattern_matches(
                    original, field, pattern, catalog_patterns
                )
                if multiple_patterns:
                    pattern_list = ", ".join(multiple_patterns[:3])
                    mismatches["multiple_patterns"].append(
                        {
                            "record": record,
                            "field_data": field_data,
                            "match_key": match_key,
                            "reason": f"Matches {len(multiple_patterns)} patterns: {pattern_list}",
                        }
                    )

            # Check Levenshtein distance (for non-exact matches only)
            matched_text = self._get_matched_text(field, matched)
            if self._levenshtein_distance_exceeds_threshold(original, matched_text, args.threshold):
                mismatches["levenshtein_distance"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": match_key,
                        "reason": "High Levenshtein distance",
                    }
                )

            # Check confidence scores (if confidence field exists)
            if hasattr(args, "confidence_threshold") and confidence < args.confidence_threshold:
                mismatches["low_confidence"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": match_key,
                        "reason": f"Low confidence: {confidence:.2f}",
                    }
                )

        return mismatches

    def _levenshtein_distance_exceeds_threshold(
        self, original: str, matched: str, threshold: int
    ) -> bool:
        """Check if Levenshtein distance exceeds threshold."""
        distance = self._levenshtein_distance(original, matched)
        return distance > threshold

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

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

    def group_duplicate_mismatches(
        self, mismatches: Dict[str, List[Dict]], field: str
    ) -> List[Dict]:
        """Group duplicate mismatches by their match key."""
        grouped = {}

        for mismatch_type, mismatch_list in mismatches.items():
            for mismatch in mismatch_list:
                match_key = mismatch["match_key"]
                if match_key not in grouped:
                    grouped[match_key] = {
                        "record": mismatch["record"],
                        "field_data": mismatch["field_data"],
                        "reasons": [],
                        "match_key": match_key,
                    }
                grouped[match_key]["reasons"].append(mismatch["reason"])

        # Convert to list and sort by number of reasons (most problematic first)
        result = list(grouped.values())
        result.sort(key=lambda x: len(x["reasons"]), reverse=True)

        return result
