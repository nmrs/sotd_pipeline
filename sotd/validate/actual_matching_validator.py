"""
Actual Matching Validator for Catalog Validation.

This module provides validation that runs each entry in correct_matches directory through
the actual matching systems (razor, blade, brush, soap) and validates that the results
match what's stored. This provides more comprehensive validation than pattern-only validation.
"""

import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher

logger = logging.getLogger(__name__)


class ValidationIssue:
    """Represents a validation issue found during actual matching validation."""

    def __init__(
        self,
        issue_type: str,
        severity: str,
        correct_match: str,
        expected_brand: Optional[str] = None,
        expected_model: Optional[str] = None,
        actual_brand: Optional[str] = None,
        actual_model: Optional[str] = None,
        expected_handle_brand: Optional[str] = None,
        expected_handle_model: Optional[str] = None,
        actual_handle_brand: Optional[str] = None,
        actual_handle_model: Optional[str] = None,
        expected_knot_brand: Optional[str] = None,
        expected_knot_model: Optional[str] = None,
        actual_knot_brand: Optional[str] = None,
        actual_knot_model: Optional[str] = None,
        expected_section: Optional[str] = None,
        actual_section: Optional[str] = None,
        details: str = "",
        suggested_action: str = "",
        line_numbers: Optional[Dict[str, List[int]]] = None,
        matched_pattern: Optional[str] = None,
        format: Optional[str] = None,
        catalog_format: Optional[str] = None,
        source_files: Optional[List[str]] = None,
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.correct_match = correct_match
        self.expected_brand = expected_brand
        self.expected_model = expected_model
        self.actual_brand = actual_brand
        self.actual_model = actual_model
        self.expected_handle_brand = expected_handle_brand
        self.expected_handle_model = expected_handle_model
        self.actual_handle_brand = actual_handle_brand
        self.actual_handle_model = actual_handle_model
        self.expected_knot_brand = expected_knot_brand
        self.expected_knot_model = expected_knot_model
        self.actual_knot_brand = actual_knot_brand
        self.actual_knot_model = actual_knot_model
        self.expected_section = expected_section
        self.actual_section = actual_section
        self.details = details
        self.suggested_action = suggested_action
        self.line_numbers = line_numbers or {}  # Dict mapping section/file to list of line numbers
        self.matched_pattern = matched_pattern
        self.format = format  # Expected format (from correct_matches structure)
        self.catalog_format = catalog_format  # Actual format (from matcher result)
        self.source_files = (
            source_files or []
        )  # List of file names where the issue originates (e.g., ["handle.yaml", "knot.yaml"])


class ValidationResult:
    """Represents the result of actual matching validation."""

    def __init__(
        self,
        field: str,
        total_entries: int,
        issues: List[ValidationIssue],
        processing_time: float,
        validation_mode: str = "actual_matching",
        strategy_stats: Optional[Dict[str, int]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
    ):
        self.field = field
        self.total_entries = total_entries
        self.issues = issues
        self.processing_time = processing_time
        self.validation_mode = validation_mode
        self.strategy_stats = strategy_stats or {}
        self.performance_metrics = performance_metrics or {}


class ActualMatchingValidator:
    """Validates correct_matches directory entries using actual matching systems."""

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize the actual matching validator.

        Args:
            data_path: Path to data directory containing catalogs
        """
        self.data_path = data_path or Path("data")
        self._matchers = {}
        self._correct_matches_checker = None
        self._performance_metrics = {}
        self._splits_loader = None

        # Clear caches on initialization to ensure fresh data
        self._clear_all_caches()

    def _clear_all_caches(self):
        """Clear all caches to ensure fresh data on every validation."""
        from sotd.match.base_matcher import clear_catalog_cache
        from sotd.match.brush.matcher import clear_brush_catalog_cache
        from sotd.match.loaders import clear_yaml_cache

        clear_catalog_cache()
        clear_yaml_cache()
        clear_brush_catalog_cache()

        # Clear any matcher-specific caches
        for matcher in self._matchers.values():
            if hasattr(matcher, "clear_cache"):
                matcher.clear_cache()

        # Clear internal caches
        self._matchers.clear()
        self._correct_matches_checker = None
        self._splits_loader = None

    def _get_matcher(self, field: str):
        """Get or create matcher for the specified field."""
        if field not in self._matchers:
            # Create matchers with bypass_correct_matches=True to test actual matching logic
            # rather than using the correct_matches cheat sheet
            # Note: BrushMatcher doesn't support bypass_correct_matches in __init__,
            # but it supports it in the match() method
            if field == "brush":
                self._matchers[field] = BrushMatcher()
            elif field == "razor":
                self._matchers[field] = RazorMatcher(bypass_correct_matches=True)
            elif field == "blade":
                self._matchers[field] = BladeMatcher(bypass_correct_matches=True)
            elif field == "soap":
                self._matchers[field] = SoapMatcher(bypass_correct_matches=True)
            else:
                raise ValueError(f"Unsupported field type: {field}")
        return self._matchers[field]

    def _get_correct_matches_checker(self):
        """Get or create correct matches checker."""
        if self._correct_matches_checker is None:
            import yaml

            correct_matches_dir = self.data_path / "correct_matches"
            correct_matches_data = {}

            # Load all field files from directory structure
            if correct_matches_dir.exists():
                for field_file in correct_matches_dir.glob("*.yaml"):
                    field_name = field_file.stem
                    # Skip backup and report files
                    if (
                        field_file.name.endswith((".backup", ".bk"))
                        or "duplicates_report" in field_file.name
                    ):
                        continue
                    try:
                        with field_file.open("r", encoding="utf-8") as f:
                            field_data = yaml.safe_load(f)
                            if field_data:
                                correct_matches_data[field_name] = field_data
                    except Exception as e:
                        logger.warning(f"Error loading {field_file}: {e}")

            # Note: CorrectMatchesChecker not used in current implementation
            self._correct_matches_checker = correct_matches_data
        return self._correct_matches_checker

    def _get_splits_loader(self):
        """Get or create brush splits loader."""
        if self._splits_loader is None:
            from sotd.match.brush.comparison.splits_loader import BrushSplitsLoader

            self._splits_loader = BrushSplitsLoader(self.data_path / "brush_splits.yaml")
        return self._splits_loader

    def _find_line_numbers(self, search_string: str, section_name: str) -> List[int]:
        """Find line numbers where a string appears in a YAML file."""
        line_numbers = []
        correct_matches_dir = self.data_path / "correct_matches"
        field_file = correct_matches_dir / f"{section_name}.yaml"

        if not field_file.exists():
            return line_numbers

        try:
            with field_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, start=1):
                    stripped = line.strip()
                    # Check if this line contains the search string as a list item
                    # YAML list items can have various formats:
                    #   - string_value
                    #   - "string_value"
                    #   - 'string_value'
                    #   - string_value: (if it's a key, but we're looking for values)

                    # Check for exact match as list item value
                    if stripped.startswith("-"):
                        # Extract the value after the dash
                        value_part = stripped[1:].strip()
                        # Remove quotes if present
                        if value_part.startswith('"') and value_part.endswith('"'):
                            value_part = value_part[1:-1]
                        elif value_part.startswith("'") and value_part.endswith("'"):
                            value_part = value_part[1:-1]

                        # Check if this matches our search string (case-insensitive)
                        if value_part.lower() == search_string.lower():
                            line_numbers.append(line_num)
        except Exception as e:
            logger.warning(f"Error finding line numbers in {field_file}: {e}")

        return line_numbers

    def _validate_data_structure(self, correct_matches: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate data structure rules for correct_matches directory."""
        issues = []
        within_section_duplicates = set()

        # Check for duplicate strings within same section
        for section_name, section_data in correct_matches.items():
            if not isinstance(section_data, dict):
                continue

            seen_strings = set()
            for brand, brand_data in section_data.items():
                if not isinstance(brand_data, dict):
                    continue
                for model, strings in brand_data.items():
                    if not isinstance(strings, list):
                        continue
                    for string in strings:
                        if string in seen_strings:
                            within_section_duplicates.add(string)
                            # Find line numbers for this duplicate
                            line_nums = self._find_line_numbers(string, section_name)
                            line_numbers = {section_name: line_nums} if line_nums else {}
                            issues.append(
                                ValidationIssue(
                                    issue_type="duplicate_string",
                                    severity="low",
                                    correct_match=string,
                                    details=(
                                        f"Duplicate string '{string}' found in "
                                        f"{section_name} section"
                                    ),
                                    suggested_action=(
                                        f"Remove duplicate entry for '{string}' in "
                                        f"{section_name} section"
                                    ),
                                    line_numbers=line_numbers,
                                )
                            )
                        seen_strings.add(string)

        # Check for cross-section conflicts
        brush_strings = set()
        handle_strings = set()
        knot_strings = set()

        # Collect brush strings
        brush_section = correct_matches.get("brush", {})
        if isinstance(brush_section, dict):
            for brand_data in brush_section.values():
                if isinstance(brand_data, dict):
                    for strings in brand_data.values():
                        if isinstance(strings, list):
                            brush_strings.update(strings)

        # Collect handle strings
        handle_section = correct_matches.get("handle", {})
        if isinstance(handle_section, dict):
            for brand_data in handle_section.values():
                if isinstance(brand_data, dict):
                    for strings in brand_data.values():
                        if isinstance(strings, list):
                            handle_strings.update(strings)

        # Collect knot strings
        knot_section = correct_matches.get("knot", {})
        if isinstance(knot_section, dict):
            for brand_data in knot_section.values():
                if isinstance(brand_data, dict):
                    for strings in brand_data.values():
                        if isinstance(strings, list):
                            knot_strings.update(strings)

        # Check for conflicts between brush and handle/knot
        # Note: handle AND knot is valid (composite brush), so we don't flag that as a conflict
        brush_handle_conflicts = brush_strings.intersection(handle_strings)
        brush_knot_conflicts = brush_strings.intersection(knot_strings)

        # Check for triple conflicts (brush AND handle AND knot)
        all_sections = brush_strings.union(handle_strings).union(knot_strings)
        triple_conflicts = set()
        for string in all_sections:
            in_brush = string in brush_strings
            in_handle = string in handle_strings
            in_knot = string in knot_strings
            if in_brush and in_handle and in_knot:
                triple_conflicts.add(string)

        # Report conflicts
        for conflict_string in brush_handle_conflicts:
            # Find line numbers in both sections
            line_numbers = {}
            line_nums_brush = self._find_line_numbers(conflict_string, "brush")
            line_nums_handle = self._find_line_numbers(conflict_string, "handle")
            if line_nums_brush:
                line_numbers["brush"] = line_nums_brush
            if line_nums_handle:
                line_numbers["handle"] = line_nums_handle

            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=(
                        f"String '{conflict_string}' appears in both brush and handle sections"
                    ),
                    suggested_action=(
                        f"Remove '{conflict_string}' from either brush or handle section"
                    ),
                    line_numbers=line_numbers,
                )
            )

        for conflict_string in brush_knot_conflicts:
            # Find line numbers in both sections
            line_numbers = {}
            line_nums_brush = self._find_line_numbers(conflict_string, "brush")
            line_nums_knot = self._find_line_numbers(conflict_string, "knot")
            if line_nums_brush:
                line_numbers["brush"] = line_nums_brush
            if line_nums_knot:
                line_numbers["knot"] = line_nums_knot

            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=(f"String '{conflict_string}' appears in both brush and knot sections"),
                    suggested_action=(
                        f"Remove '{conflict_string}' from either brush or knot section"
                    ),
                    line_numbers=line_numbers,
                )
            )

        for conflict_string in triple_conflicts:
            # Find line numbers in all three sections
            line_numbers = {}
            line_nums_brush = self._find_line_numbers(conflict_string, "brush")
            line_nums_handle = self._find_line_numbers(conflict_string, "handle")
            line_nums_knot = self._find_line_numbers(conflict_string, "knot")
            if line_nums_brush:
                line_numbers["brush"] = line_nums_brush
            if line_nums_handle:
                line_numbers["handle"] = line_nums_handle
            if line_nums_knot:
                line_numbers["knot"] = line_nums_knot

            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=(
                        f"String '{conflict_string}' appears in brush, handle, and knot sections"
                    ),
                    suggested_action=(
                        f"Remove '{conflict_string}' from brush section "
                        f"(keep in handle and knot for composite brush)"
                    ),
                    line_numbers=line_numbers,
                )
            )

        return issues

    def _validate_single_brush_entry(
        self,
        matcher: BrushMatcher,
        splits_loader: Any,
        brush_string: str,
        expected_data: Dict[str, Any],
        expected_section: str,
        source_files: Optional[List[str]] = None,
    ) -> List[ValidationIssue]:
        """Validate a single brush entry using provided matcher and splits_loader.

        This is a helper function that can be used in both sequential and parallel processing.

        Args:
            matcher: BrushMatcher instance to use for matching
            splits_loader: BrushSplitsLoader instance to check split rules
            brush_string: The brush string to validate
            expected_data: Expected data structure from correct_matches
            expected_section: Expected section (brush, handle, knot, handle_knot)
            source_files: Optional list of source file names

        Returns:
            List of ValidationIssue objects
        """
        issues = []

        try:
            # Check if this brush should not be split (from brush_splits.yaml)
            should_not_split = splits_loader.should_not_split(brush_string)

            # Run actual matching with bypass_correct_matches=True
            result = matcher.match(brush_string, bypass_correct_matches=True)

            if not result or not result.matched:
                # No match found
                issues.append(
                    ValidationIssue(
                        issue_type="no_match",
                        severity="high",
                        correct_match=brush_string,
                        expected_section=expected_section,
                        details=(f"Brush string '{brush_string}' no longer matches any strategy"),
                        suggested_action=(
                            f"Remove '{brush_string}' from correct_matches "
                            f"directory or update matching logic"
                        ),
                    )
                )
                return issues

            matched_data = result.matched

            # Determine actual section based on result structure
            # Check for complete brush (has top-level brand/model)
            if matched_data.get("brand") and matched_data.get("model"):
                actual_section = "brush"
            # Check for composite brush (has nested handle and knot sections,
            # regardless of brand content)
            # This matches the logic in structureBrushDataForAPI: if both
            # handle and knot exist, it's composite
            elif matched_data.get("handle") and matched_data.get("knot"):
                actual_section = "handle_knot"
            # Check for handle-only (has nested handle section, but no knot section)
            elif matched_data.get("handle") and not matched_data.get("knot"):
                actual_section = "handle"
            # Check for knot-only (has nested knot section, but no handle section)
            elif matched_data.get("knot") and not matched_data.get("handle"):
                actual_section = "knot"
            else:
                actual_section = "unknown"

            # Validate that should_not_split entries are NOT split
            if should_not_split and actual_section in ["handle_knot", "handle", "knot"]:
                issues.append(
                    ValidationIssue(
                        issue_type="structural_change",
                        severity="high",
                        correct_match=brush_string,
                        expected_section=expected_section,
                        actual_section=actual_section,
                        details=(
                            f"Brush string '{brush_string}' has "
                            f"should_not_split: true in brush_splits.yaml but "
                            f"matcher split it into {actual_section}"
                        ),
                        suggested_action=(
                            f"Fix matching logic to respect should_not_split "
                            f"flag for '{brush_string}'"
                        ),
                        matched_pattern=result.pattern if result else None,
                    )
                )
                # Return early since this is a critical issue
                return issues

            # Validate that explicit splits from brush_splits.yaml are being used
            curated_split = splits_loader.find_split(brush_string)
            if curated_split and not curated_split.should_not_split:
                # This brush has an explicit split in brush_splits.yaml
                # Check if the matcher used KnownSplitWrapperStrategy (known_split strategy)
                actual_strategy = result.strategy if result else None
                if actual_strategy != "known_split":
                    issues.append(
                        ValidationIssue(
                            issue_type="data_mismatch",
                            severity="medium",
                            correct_match=brush_string,
                            expected_section=expected_section,
                            actual_section=actual_section,
                            details=(
                                f"Brush string '{brush_string}' has explicit "
                                f"split in brush_splits.yaml but matcher used "
                                f"'{actual_strategy}' strategy instead of "
                                f"'known_split'. Expected handle: "
                                f"'{curated_split.handle}', knot: "
                                f"'{curated_split.knot}'"
                            ),
                            suggested_action=(
                                "Fix matching logic to use "
                                "KnownSplitWrapperStrategy for explicit splits "
                                "from brush_splits.yaml"
                            ),
                            matched_pattern=result.pattern if result else None,
                        )
                    )
                else:
                    # Strategy is correct, but also validate that handle/knot
                    # match the curated split
                    if actual_section in ["handle_knot", "handle", "knot"]:
                        handle_data = matched_data.get("handle", {})
                        knot_data = matched_data.get("knot", {})
                        actual_handle_text = (
                            handle_data.get("source_text", "") if handle_data else ""
                        )
                        actual_knot_text = knot_data.get("source_text", "") if knot_data else ""

                        # Check if handle/knot text matches curated split
                        # (allowing for case/whitespace differences)
                        expected_handle = curated_split.handle or ""
                        expected_knot = curated_split.knot or ""

                        if (
                            expected_handle
                            and actual_handle_text.lower().strip()
                            != expected_handle.lower().strip()
                        ):
                            issues.append(
                                ValidationIssue(
                                    issue_type="data_mismatch",
                                    severity="medium",
                                    correct_match=brush_string,
                                    expected_section=expected_section,
                                    actual_section=actual_section,
                                    details=(
                                        f"Brush string '{brush_string}' uses "
                                        f"known_split strategy but handle text "
                                        f"'{actual_handle_text}' doesn't match "
                                        f"brush_splits.yaml handle "
                                        f"'{expected_handle}'"
                                    ),
                                    suggested_action=(
                                        "Update brush_splits.yaml or fix "
                                        "KnownSplitWrapperStrategy to use "
                                        "correct handle text"
                                    ),
                                    matched_pattern=result.pattern if result else None,
                                )
                            )

                        if (
                            expected_knot
                            and actual_knot_text.lower().strip() != expected_knot.lower().strip()
                        ):
                            issues.append(
                                ValidationIssue(
                                    issue_type="data_mismatch",
                                    severity="medium",
                                    correct_match=brush_string,
                                    expected_section=expected_section,
                                    actual_section=actual_section,
                                    details=(
                                        f"Brush string '{brush_string}' uses "
                                        f"known_split strategy but knot text "
                                        f"'{actual_knot_text}' doesn't match "
                                        f"brush_splits.yaml knot "
                                        f"'{expected_knot}'"
                                    ),
                                    suggested_action=(
                                        "Update brush_splits.yaml or fix "
                                        "KnownSplitWrapperStrategy to use "
                                        "correct knot text"
                                    ),
                                    matched_pattern=result.pattern if result else None,
                                )
                            )

            # Check for structural changes
            if expected_section != actual_section:
                logger.debug(
                    f"Structural change detected: {brush_string} from "
                    f"{expected_section} to {actual_section}"
                )

                # Extract handle and knot details for structural changes
                actual_handle_brand = None
                actual_handle_model = None
                actual_knot_brand = None
                actual_knot_model = None
                actual_brand = None
                actual_model = None

                if actual_section == "handle_knot":
                    # Extract handle and knot details from matched_data
                    handle_data = matched_data.get("handle", {})
                    knot_data = matched_data.get("knot", {})

                    # Fail fast if handle/knot data is missing when it should be present
                    if not handle_data or not knot_data:
                        raise ValueError(
                            f"Structural change to handle_knot detected but missing data: "
                            f"handle={bool(handle_data)}, knot={bool(knot_data)}"
                        )

                    actual_handle_brand = handle_data.get("brand")
                    actual_handle_model = handle_data.get("model")
                    actual_knot_brand = knot_data.get("brand")
                    actual_knot_model = knot_data.get("model")
                elif actual_section == "brush":
                    # Extract brush brand and model from matched_data
                    actual_brand = matched_data.get("brand")
                    actual_model = matched_data.get("model")

                # Extract expected handle/knot brand/model from expected_data
                expected_handle_brand = None
                expected_handle_model = None
                expected_knot_brand = None
                expected_knot_model = None

                if expected_section == "handle_knot":
                    expected_handle_brand = expected_data.get("handle_maker")
                    expected_handle_model = expected_data.get("handle_model")
                    expected_knot_brand = expected_data.get("knot_brand")
                    expected_knot_model = expected_data.get("knot_model")
                elif expected_section == "handle":
                    expected_handle_brand = expected_data.get("handle_maker")
                    expected_handle_model = expected_data.get("handle_model")
                elif expected_section == "knot":
                    expected_knot_brand = expected_data.get("knot_brand")
                    expected_knot_model = expected_data.get("knot_model")

                issues.append(
                    ValidationIssue(
                        issue_type="structural_change",
                        severity="high",
                        correct_match=brush_string,
                        # Where it currently is (correct_matches directory)
                        expected_section=expected_section,
                        # Where it should be (current matching system)
                        actual_section=actual_section,
                        expected_brand=(
                            expected_data.get("brand") if expected_section == "brush" else None
                        ),
                        expected_model=(
                            expected_data.get("model") if expected_section == "brush" else None
                        ),
                        actual_brand=actual_brand,
                        actual_model=actual_model,
                        expected_handle_brand=expected_handle_brand,
                        expected_handle_model=expected_handle_model,
                        expected_knot_brand=expected_knot_brand,
                        expected_knot_model=expected_knot_model,
                        actual_handle_brand=actual_handle_brand,
                        actual_handle_model=actual_handle_model,
                        actual_knot_brand=actual_knot_brand,
                        actual_knot_model=actual_knot_model,
                        details=f"Brush type changed from {expected_section} to {actual_section}",
                        suggested_action=(
                            f"Move '{brush_string}' from {expected_section} "
                            f"section to {actual_section} section"
                        ),
                        matched_pattern=result.pattern if result else None,
                        source_files=source_files or [],
                    )
                )

            # Validate based on expected section
            if expected_section == "brush":
                # Complete brush validation
                expected_brand = expected_data.get("brand")
                expected_model = expected_data.get("model")
                actual_brand = matched_data.get("brand")
                actual_model = matched_data.get("model")

                if expected_brand != actual_brand or expected_model != actual_model:
                    issues.append(
                        ValidationIssue(
                            issue_type="data_mismatch",
                            severity="high",
                            correct_match=brush_string,
                            expected_brand=expected_brand,
                            expected_model=expected_model,
                            actual_brand=actual_brand,
                            actual_model=actual_model,
                            details=(
                                f"Brand/model mismatch: expected "
                                f"'{expected_brand} {expected_model}', got "
                                f"'{actual_brand} {actual_model}'"
                            ),
                            suggested_action=(
                                f"Update correct_matches directory to reflect "
                                f"new brand/model: '{actual_brand} "
                                f"{actual_model}'"
                            ),
                            matched_pattern=result.pattern if result else None,
                        )
                    )

            elif expected_section in ["handle", "knot"]:
                # Composite brush validation
                handle_data = matched_data.get("handle", {})
                knot_data = matched_data.get("knot", {})

                if expected_section == "handle":
                    expected_handle_brand = expected_data.get("handle_maker")
                    expected_handle_model = expected_data.get("handle_model")
                    actual_handle_brand = handle_data.get("brand")
                    actual_handle_model = handle_data.get("model")

                    if (
                        expected_handle_brand != actual_handle_brand
                        or expected_handle_model != actual_handle_model
                    ):
                        issues.append(
                            ValidationIssue(
                                issue_type="data_mismatch",
                                severity="high",
                                correct_match=brush_string,
                                expected_handle_brand=expected_handle_brand,
                                expected_handle_model=expected_handle_model,
                                actual_handle_brand=actual_handle_brand,
                                actual_handle_model=actual_handle_model,
                                details=(
                                    f"Handle brand/model mismatch: expected "
                                    f"'{expected_handle_brand} {expected_handle_model}', got "
                                    f"'{actual_handle_brand} {actual_handle_model}'"
                                ),
                                suggested_action=(
                                    f"Update correct_matches directory handle section to reflect "
                                    f"new brand/model: '{actual_handle_brand} "
                                    f"{actual_handle_model}'"
                                ),
                                matched_pattern=result.pattern if result else None,
                            )
                        )

                if expected_section == "knot":
                    expected_knot_brand = expected_data.get("knot_brand")
                    expected_knot_model = expected_data.get("knot_model")
                    actual_knot_brand = knot_data.get("brand")
                    actual_knot_model = knot_data.get("model")

                    if (
                        expected_knot_brand != actual_knot_brand
                        or expected_knot_model != actual_knot_model
                    ):
                        issues.append(
                            ValidationIssue(
                                issue_type="data_mismatch",
                                severity="high",
                                correct_match=brush_string,
                                expected_knot_brand=expected_knot_brand,
                                expected_knot_model=expected_knot_model,
                                actual_knot_brand=actual_knot_brand,
                                actual_knot_model=actual_knot_model,
                                details=(
                                    f"Knot brand/model mismatch: expected "
                                    f"'{expected_knot_brand} "
                                    f"{expected_knot_model}', got "
                                    f"'{actual_knot_brand} "
                                    f"{actual_knot_model}'"
                                ),
                                suggested_action=(
                                    f"Update correct_matches directory knot "
                                    f"section to reflect new brand/model: "
                                    f"'{actual_knot_brand} "
                                    f"{actual_knot_model}'"
                                ),
                                matched_pattern=result.pattern if result else None,
                            )
                        )

        except Exception as e:
            # Fail fast on internal errors
            logger.error("Error validating brush entry '%s': %s", brush_string, e)
            raise ValueError(f"Brush validation failed for '{brush_string}': {e}") from e

        return issues

    def _validate_brush_entry(
        self,
        brush_string: str,
        expected_data: Dict[str, Any],
        expected_section: str,
        source_files: Optional[List[str]] = None,
    ) -> List[ValidationIssue]:
        """Validate a single brush entry using actual matching.

        This is a wrapper that uses instance matcher and splits_loader.
        For parallel processing, use _validate_single_brush_entry directly.
        """
        splits_loader = self._get_splits_loader()
        matcher = self._get_matcher("brush")
        return self._validate_single_brush_entry(
            matcher, splits_loader, brush_string, expected_data, expected_section, source_files
        )

    def _validate_brush_entries_parallel(
        self,
        brush_string_locations: Dict[str, List[Dict[str, Any]]],
        max_workers: int = 8,
    ) -> List[ValidationIssue]:
        """Validate brush entries in parallel using ProcessPoolExecutor.

        Args:
            brush_string_locations: Dictionary mapping brush strings to their locations
            max_workers: Maximum number of parallel workers (default 8)

        Returns:
            List of all ValidationIssue objects from all workers
        """
        if not brush_string_locations:
            return []

        # Prepare batches for parallel processing
        # Each batch contains: (brush_string, locations, expected_data, expected_section, source_files)
        batches = []
        for brush_string, locations in brush_string_locations.items():
            expected_section = self._determine_expected_section(locations)
            expected_data = self._build_expected_data(brush_string, locations, expected_section)
            source_files = [f"{loc['section']}.yaml" for loc in locations]
            batches.append((brush_string, locations, expected_data, expected_section, source_files))

        # Split into worker batches (approximately equal distribution)
        batch_size = max(1, len(batches) // max_workers)
        worker_batches = []
        for i in range(0, len(batches), batch_size):
            worker_batches.append(batches[i : i + batch_size])

        # If we have fewer batches than workers, adjust
        if len(worker_batches) < max_workers:
            max_workers = len(worker_batches)

        if max_workers <= 1 or len(worker_batches) == 1:
            # Fall back to sequential processing for small datasets
            issues = []
            for batch in batches:
                brush_string, _, expected_data, expected_section, source_files = batch
                entry_issues = self._validate_brush_entry(
                    brush_string, expected_data, expected_section, source_files=source_files
                )
                issues.extend(entry_issues)
            return issues

        # Process batches in parallel
        all_issues = []
        data_path_str = str(self.data_path)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(_validate_brush_entry_worker, batch, data_path_str): batch
                for batch in worker_batches
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_issues = future.result()
                    all_issues.extend(batch_issues)
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
                    # Continue processing other batches even if one fails
                    # Log which entries were in the failed batch
                    brush_strings = [entry[0] for entry in batch]
                    logger.error(f"Failed batch contained {len(brush_strings)} entries")
                    raise

        return all_issues

    def _validate_simple_entry(
        self,
        field: str,
        entry_string: str,
        expected_brand: str,
        expected_model: str,
        expected_format: Optional[str] = None,
    ) -> List[ValidationIssue]:
        """Validate a simple entry (razor, blade, soap) using actual matching."""
        issues = []

        try:
            matcher = self._get_matcher(field)

            # For blades, use match_with_context() with the format from correct_matches section
            # This aligns with actual pipeline behavior where blades are matched with razor format context
            # The format sections represent usage context (which razor format the blade was used with)
            if field == "blade" and expected_format is not None:
                # Use match_with_context() to validate entry matches correctly in format context
                # Note: match_with_context doesn't have bypass_correct_matches parameter,
                # but since we're validating, we want to test the actual matching logic
                # The matcher was created with bypass_correct_matches=True, so correct_matches
                # won't be used in the matching process
                if hasattr(matcher, "match_with_context"):
                    result = matcher.match_with_context(entry_string, expected_format)
                else:
                    # Fallback if matcher doesn't support match_with_context
                    result = matcher.match(entry_string, bypass_correct_matches=True)
            else:
                # For other fields (razor, soap), use regular match()
                result = matcher.match(entry_string, bypass_correct_matches=True)

            if not result or not result.matched:
                # No match found
                issues.append(
                    ValidationIssue(
                        issue_type="no_match",
                        severity="high",
                        correct_match=entry_string,
                        format=expected_format if field == "blade" else None,
                        details=(
                            f"{field.title()} string '{entry_string}' no "
                            f"longer matches any strategy"
                            + (
                                f" in {expected_format} format context"
                                if field == "blade" and expected_format
                                else ""
                            )
                        ),
                        suggested_action=(
                            f"Remove '{entry_string}' from correct_matches "
                            f"directory or update matching logic"
                        ),
                    )
                )
                return issues

            matched_data = result.matched
            actual_brand = matched_data.get("brand")

            # Soap uses 'scent' instead of 'model'
            if field == "soap":
                actual_scent = matched_data.get("scent")
                # For soap, expected_model is actually the scent name from YAML
                # Use case-insensitive comparison since matching is case-insensitive
                if (expected_brand or "").lower() != (actual_brand or "").lower() or (
                    expected_model or ""
                ).lower() != (actual_scent or "").lower():
                    issues.append(
                        ValidationIssue(
                            issue_type="data_mismatch",
                            severity="high",
                            correct_match=entry_string,
                            expected_brand=expected_brand,
                            expected_model=expected_model,  # This is actually scent name
                            actual_brand=actual_brand,
                            actual_model=actual_scent,  # Store scent in actual_model for consistency
                            format=expected_format if field == "blade" else None,
                            details=(
                                f"Brand/scent mismatch: expected "
                                f"'{expected_brand} {expected_model}', got "
                                f"'{actual_brand} {actual_scent or 'None'}'"
                                + (
                                    f" in {expected_format} format context"
                                    if field == "blade" and expected_format
                                    else ""
                                )
                            ),
                            suggested_action=(
                                f"Update correct_matches directory to reflect "
                                f"new brand/scent: '{actual_brand} "
                                f"{actual_scent or 'None'}'"
                            ),
                            matched_pattern=result.pattern if result else None,
                        )
                    )
            else:
                # Existing logic for razor, blade (use model)
                actual_model = matched_data.get("model")

                # Check brand/model mismatch
                # For blades, this validates that the entry matches the expected brand/model
                # when used with the razor format from its section
                if expected_brand != actual_brand or expected_model != actual_model:
                    issues.append(
                        ValidationIssue(
                            issue_type="data_mismatch",
                            severity="high",
                            correct_match=entry_string,
                            expected_brand=expected_brand,
                            expected_model=expected_model,
                            actual_brand=actual_brand,
                            actual_model=actual_model,
                            format=expected_format if field == "blade" else None,
                            details=(
                                f"Brand/model mismatch: expected "
                                f"'{expected_brand} {expected_model}', got "
                                f"'{actual_brand} {actual_model}'"
                                + (
                                    f" in {expected_format} format context"
                                    if field == "blade" and expected_format
                                    else ""
                                )
                            ),
                            suggested_action=(
                                f"Update correct_matches directory to reflect "
                                f"new brand/model: '{actual_brand} "
                                f"{actual_model}'"
                            ),
                            matched_pattern=result.pattern if result else None,
                        )
                    )

        except Exception as e:
            # Fail fast on internal errors
            logger.error("Error validating %s entry '%s': %s", field, entry_string, e)
            raise ValueError(f"{field.title()} validation failed for '{entry_string}': {e}") from e

        return issues

    def _collect_brush_string_locations(
        self, correct_matches: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Collect all brush strings and their locations in correct_matches directory."""
        brush_string_locations = {}

        # Check brush section
        brush_section = correct_matches.get("brush", {})
        if isinstance(brush_section, dict):
            for brand, brand_data in brush_section.items():
                if isinstance(brand_data, dict):
                    for model, strings in brand_data.items():
                        if isinstance(strings, list):
                            for brush_string in strings:
                                if brush_string not in brush_string_locations:
                                    brush_string_locations[brush_string] = []
                                brush_string_locations[brush_string].append(
                                    {
                                        "section": "brush",
                                        "brand": brand,
                                        "model": model,
                                        "data": {"brand": brand, "model": model},
                                    }
                                )

        # Check handle section
        handle_section = correct_matches.get("handle", {})
        if isinstance(handle_section, dict):
            for handle_maker, handle_models in handle_section.items():
                if isinstance(handle_models, dict):
                    for handle_model, strings in handle_models.items():
                        if isinstance(strings, list):
                            for brush_string in strings:
                                if brush_string not in brush_string_locations:
                                    brush_string_locations[brush_string] = []
                                brush_string_locations[brush_string].append(
                                    {
                                        "section": "handle",
                                        "brand": handle_maker,
                                        "model": handle_model,
                                        "data": {
                                            "handle_maker": handle_maker,
                                            "handle_model": handle_model,
                                        },
                                    }
                                )

        # Check knot section
        knot_section = correct_matches.get("knot", {})
        if isinstance(knot_section, dict):
            for knot_brand, knot_models in knot_section.items():
                if isinstance(knot_models, dict):
                    for knot_model, strings in knot_models.items():
                        if isinstance(strings, list):
                            for brush_string in strings:
                                if brush_string not in brush_string_locations:
                                    brush_string_locations[brush_string] = []
                                brush_string_locations[brush_string].append(
                                    {
                                        "section": "knot",
                                        "brand": knot_brand,
                                        "model": knot_model,
                                        "data": {
                                            "knot_brand": knot_brand,
                                            "knot_model": knot_model,
                                        },
                                    }
                                )

        return brush_string_locations

    def _determine_expected_section(self, locations: List[Dict[str, Any]]) -> str:
        """Determine the expected section based on where the string appears."""
        sections = [loc["section"] for loc in locations]

        # If it appears in brush section, it's a complete brush
        if "brush" in sections:
            return "brush"

        # If it appears in both handle and knot, it's a composite brush
        if "handle" in sections and "knot" in sections:
            return "handle_knot"

        # If it appears in only handle, it's handle-only
        if "handle" in sections and "knot" not in sections:
            return "handle"

        # If it appears in only knot, it's knot-only
        if "knot" in sections and "handle" not in sections:
            return "knot"

        # Fallback
        return sections[0] if sections else "unknown"

    def _build_expected_data(
        self, brush_string: str, locations: List[Dict[str, Any]], expected_section: str
    ) -> Dict[str, Any]:
        """Build expected data based on the expected section and locations."""
        if expected_section == "brush":
            # Use the brush section data
            brush_location = next((loc for loc in locations if loc["section"] == "brush"), None)
            if brush_location:
                return brush_location["data"]

        elif expected_section == "handle_knot":
            # Combine handle and knot data
            handle_location = next((loc for loc in locations if loc["section"] == "handle"), None)
            knot_location = next((loc for loc in locations if loc["section"] == "knot"), None)

            expected_data = {}
            if handle_location:
                expected_data.update(handle_location["data"])
            if knot_location:
                expected_data.update(knot_location["data"])
            return expected_data

        elif expected_section == "handle":
            # Use handle section data
            handle_location = next((loc for loc in locations if loc["section"] == "handle"), None)
            if handle_location:
                return handle_location["data"]

        elif expected_section == "knot":
            # Use knot section data
            knot_location = next((loc for loc in locations if loc["section"] == "knot"), None)
            if knot_location:
                return knot_location["data"]

        # Fallback
        return locations[0]["data"] if locations else {}

    def validate(self, field: str) -> ValidationResult:
        """
        Validate correct_matches directory entries for the specified field using actual matching.

        Args:
            field: Field type to validate (razor, blade, brush, soap)

        Returns:
            ValidationResult containing validation issues and metrics
        """
        start_time = time.time()
        issues = []

        try:
            # Clear all caches before validation to ensure fresh data
            self._clear_all_caches()

            # Load correct_matches from directory structure
            import yaml

            correct_matches_dir = self.data_path / "correct_matches"
            correct_matches = {}

            # Load all field files from directory structure
            if correct_matches_dir.exists():
                for field_file in correct_matches_dir.glob("*.yaml"):
                    field_name = field_file.stem
                    # Skip backup and report files
                    if (
                        field_file.name.endswith((".backup", ".bk"))
                        or "duplicates_report" in field_file.name
                    ):
                        continue
                    try:
                        with field_file.open("r", encoding="utf-8") as f:
                            field_data = yaml.safe_load(f)
                            if field_data:
                                correct_matches[field_name] = field_data
                    except Exception as e:
                        logger.warning(f"Error loading {field_file}: {e}")

            # If directory doesn't exist or is empty, return empty result
            if not correct_matches:
                return ValidationResult(
                    field=field,
                    total_entries=0,
                    issues=[],
                    processing_time=time.time() - start_time,
                )

            # Validate data structure first
            structure_issues = self._validate_data_structure(correct_matches)
            issues.extend(structure_issues)

            # Validate field-specific entries
            # Track performance metrics for parallel processing
            performance_metrics = {}

            if field == "brush":
                # First, collect all brush strings and their locations
                brush_string_locations = self._collect_brush_string_locations(correct_matches)

                # Use parallel processing for large datasets
                # Threshold: use parallel for >100 entries to amortize overhead
                if len(brush_string_locations) > 100:
                    logger.info(
                        f"Using parallel processing for {len(brush_string_locations)} brush entries"
                    )
                    parallel_start = time.time()
                    max_workers = 8
                    brush_issues = self._validate_brush_entries_parallel(
                        brush_string_locations, max_workers=max_workers
                    )
                    parallel_time = time.time() - parallel_start
                    issues.extend(brush_issues)

                    # Calculate performance metrics
                    entries_per_worker = len(brush_string_locations) / max_workers
                    performance_metrics = {
                        "parallel_workers": max_workers,
                        "parallel_processing_time": parallel_time,
                        "entries_per_worker": entries_per_worker,
                        "total_entries": len(brush_string_locations),
                        "processing_mode": "parallel",
                    }
                    logger.info(f"Parallel validation completed in {parallel_time:.2f}s")
                else:
                    # Sequential processing for small datasets
                    logger.debug(
                        f"Using sequential processing for {len(brush_string_locations)} brush entries"
                    )
                    sequential_start = time.time()
                    for brush_string, locations in brush_string_locations.items():
                        # Determine expected structure based on locations
                        expected_section = self._determine_expected_section(locations)
                        expected_data = self._build_expected_data(
                            brush_string, locations, expected_section
                        )

                        # Extract source file names from locations
                        source_files = [f"{loc['section']}.yaml" for loc in locations]

                        # Validate the brush string
                        entry_issues = self._validate_brush_entry(
                            brush_string, expected_data, expected_section, source_files=source_files
                        )
                        issues.extend(entry_issues)
                    sequential_time = time.time() - sequential_start
                    performance_metrics = {
                        "parallel_workers": 1,
                        "sequential_processing_time": sequential_time,
                        "total_entries": len(brush_string_locations),
                        "processing_mode": "sequential",
                    }

            else:
                # Validate simple entries (razor, blade, soap)
                if field == "blade":
                    # Blades are organized by format first (DE, Half DE, AC, etc.)
                    blade_data = correct_matches.get(field, {})
                    # Check if structure is format-based (top-level values are dicts with brand data)
                    # Format-based structure: {format: {brand: {model: [strings]}}}
                    # Flat structure: {brand: {model: [strings]}}
                    # Check if at least one top-level value is a dict containing brand data
                    is_format_based = (
                        blade_data
                        and isinstance(blade_data, dict)
                        and any(
                            isinstance(v, dict)
                            and any(
                                isinstance(brand_data, dict)
                                and any(
                                    isinstance(model_data, list)
                                    for model_data in brand_data.values()
                                )
                                for brand_data in v.values()
                            )
                            for v in blade_data.values()
                        )
                    )

                    if is_format_based:
                        # Iterate through format sections
                        for format_name, format_data in blade_data.items():
                            if not isinstance(format_data, dict):
                                continue
                            for brand, brand_data in format_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for entry_string in strings:
                                                entry_issues = self._validate_simple_entry(
                                                    field,
                                                    entry_string,
                                                    brand,
                                                    model,
                                                    expected_format=format_name,
                                                )
                                                issues.extend(entry_issues)
                    else:
                        # Fallback to flat structure if format-based structure not detected
                        for brand, brand_data in blade_data.items():
                            if isinstance(brand_data, dict):
                                for model, strings in brand_data.items():
                                    if isinstance(strings, list):
                                        for entry_string in strings:
                                            entry_issues = self._validate_simple_entry(
                                                field, entry_string, brand, model
                                            )
                                            issues.extend(entry_issues)
                else:
                    # Other fields (razor, soap) use flat structure
                    field_section = correct_matches.get(field, {})
                    for brand, brand_data in field_section.items():
                        if isinstance(brand_data, dict):
                            for model, strings in brand_data.items():
                                if isinstance(strings, list):
                                    for entry_string in strings:
                                        entry_issues = self._validate_simple_entry(
                                            field, entry_string, brand, model
                                        )
                                        issues.extend(entry_issues)

            # Calculate total entries
            total_entries = 0
            if field == "brush":
                for section_name in ["brush", "handle", "knot"]:
                    section_data = correct_matches.get(section_name, {})
                    for brand_data in section_data.values():
                        if isinstance(brand_data, dict):
                            for strings in brand_data.values():
                                if isinstance(strings, list):
                                    total_entries += len(strings)
            elif field == "blade":
                # Blades are organized by format first (DE, Half DE, AC, etc.)
                blade_data = correct_matches.get(field, {})
                # Check if structure is format-based (top-level values are dicts with brand data)
                # Check if at least one top-level value is a dict containing brand data
                is_format_based = (
                    blade_data
                    and isinstance(blade_data, dict)
                    and any(
                        isinstance(v, dict)
                        and any(
                            isinstance(brand_data, dict)
                            and any(
                                isinstance(model_data, list) for model_data in brand_data.values()
                            )
                            for brand_data in v.values()
                        )
                        for v in blade_data.values()
                    )
                )

                if is_format_based:
                    # Iterate through format sections
                    for format_data in blade_data.values():
                        if isinstance(format_data, dict):
                            for brand_data in format_data.values():
                                if isinstance(brand_data, dict):
                                    for strings in brand_data.values():
                                        if isinstance(strings, list):
                                            total_entries += len(strings)
                else:
                    # Fallback to flat structure
                    for brand_data in blade_data.values():
                        if isinstance(brand_data, dict):
                            for strings in brand_data.values():
                                if isinstance(strings, list):
                                    total_entries += len(strings)
            else:
                field_section = correct_matches.get(field, {})
                for brand_data in field_section.values():
                    if isinstance(brand_data, dict):
                        for strings in brand_data.values():
                            if isinstance(strings, list):
                                total_entries += len(strings)

            processing_time = time.time() - start_time

            # Deduplicate structural_change issues - keep only first occurrence per unique string
            # Use a more comprehensive key that includes issue characteristics to catch exact duplicates
            seen_structural_changes = set()
            deduplicated_issues = []
            duplicate_count = 0
            for issue in issues:
                if issue.issue_type == "structural_change":
                    # Create a comprehensive key for deduplication:
                    # - correct_match (case-insensitive)
                    # - expected_section
                    # - actual_section
                    # This ensures we catch exact duplicates even if they have slightly different attributes
                    match_key = (
                        issue.correct_match.lower(),
                        issue.expected_section,
                        issue.actual_section,
                    )
                    if match_key not in seen_structural_changes:
                        seen_structural_changes.add(match_key)
                        deduplicated_issues.append(issue)
                    else:
                        # Skip duplicate structural_change issues
                        duplicate_count += 1
                        logger.debug(
                            f"Deduplicating structural_change issue for '{issue.correct_match}' "
                            f"(expected_section={issue.expected_section}, "
                            f"actual_section={issue.actual_section}, duplicate #{duplicate_count})"
                        )
                else:
                    deduplicated_issues.append(issue)

            if duplicate_count > 0:
                logger.info(f"Deduplicated {duplicate_count} duplicate structural_change issue(s)")

            # Suppress data_mismatch issues when structural_change exists for same entry
            structural_change_patterns = {
                issue.correct_match.lower()
                for issue in deduplicated_issues
                if issue.issue_type == "structural_change"
            }

            filtered_issues = [
                issue
                for issue in deduplicated_issues
                if not (
                    issue.issue_type == "data_mismatch"
                    and issue.correct_match.lower() in structural_change_patterns
                )
            ]

            # Update performance metrics
            field_metrics = {
                "processing_time": processing_time,
                "total_entries": total_entries,
                "issues_found": len(filtered_issues),
                "validation_mode": "actual_matching",
            }
            # Merge in parallel processing metrics if available
            if performance_metrics:
                field_metrics.update(performance_metrics)
            self._performance_metrics[field] = field_metrics

            return ValidationResult(
                field=field,
                total_entries=total_entries,
                issues=filtered_issues,
                processing_time=processing_time,
                validation_mode="actual_matching",
                strategy_stats={},  # TODO: Add strategy statistics
                performance_metrics=self._performance_metrics.get(field, {}),
            )

        except Exception as e:
            # Fail fast on internal errors
            logger.error("Error during %s validation: %s", field, e)
            raise ValueError(f"Validation failed for {field}: {e}") from e


def _validate_brush_entry_worker(
    batch: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any], str, List[str]]],
    data_path_str: str,
) -> List[Any]:
    """Worker function to validate a batch of brush entries in parallel.

    This is a module-level function that can be pickled for ProcessPoolExecutor.
    Each worker initializes its own matcher and splits_loader, then calls
    the helper method from ActualMatchingValidator.

    Args:
        batch: List of tuples containing (brush_string, locations, expected_data, expected_section, source_files)
        data_path_str: String path to data directory

    Returns:
        List of ValidationIssue objects
    """
    from pathlib import Path

    # Import here to avoid circular imports at module level
    from sotd.match.brush_matcher import BrushMatcher
    from sotd.match.brush.comparison.splits_loader import BrushSplitsLoader

    # Initialize matcher and splits_loader in worker process
    data_path = Path(data_path_str)
    matcher = BrushMatcher()
    splits_loader = BrushSplitsLoader(data_path / "brush_splits.yaml")

    # Create a temporary validator instance to use helper methods
    # Import here to avoid circular import (class is now defined above)
    from sotd.validate.actual_matching_validator import ActualMatchingValidator

    temp_validator = ActualMatchingValidator(data_path=data_path)

    issues = []
    for brush_string, locations, expected_data, expected_section, source_files in batch:
        # Use the helper method to validate each entry
        entry_issues = temp_validator._validate_single_brush_entry(
            matcher, splits_loader, brush_string, expected_data, expected_section, source_files
        )
        issues.extend(entry_issues)

    return issues
