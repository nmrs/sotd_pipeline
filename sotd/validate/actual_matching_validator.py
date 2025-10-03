"""
Actual Matching Validator for Catalog Validation.

This module provides validation that runs each entry in correct_matches.yaml through
the actual matching systems (razor, blade, brush, soap) and validates that the results
match what's stored. This provides more comprehensive validation than pattern-only validation.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.blade_matcher import BladeMatcher
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
    """Validates correct_matches.yaml entries using actual matching systems."""

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

    def _get_matcher(self, field: str):
        """Get or create matcher for the specified field."""
        if field not in self._matchers:
            if field == "brush":
                self._matchers[field] = BrushMatcher()
            elif field == "razor":
                self._matchers[field] = RazorMatcher()
            elif field == "blade":
                self._matchers[field] = BladeMatcher()
            elif field == "soap":
                self._matchers[field] = SoapMatcher()
            else:
                raise ValueError(f"Unsupported field type: {field}")
        return self._matchers[field]

    def _get_correct_matches_checker(self):
        """Get or create correct matches checker."""
        if self._correct_matches_checker is None:
            import yaml

            correct_matches_path = self.data_path / "correct_matches.yaml"
            with correct_matches_path.open("r", encoding="utf-8") as f:
                correct_matches_data = yaml.safe_load(f)

            # Note: CorrectMatchesChecker not used in current implementation
            self._correct_matches_checker = correct_matches_data
        return self._correct_matches_checker

    def _validate_data_structure(self, correct_matches: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate data structure rules for correct_matches.yaml."""
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
                            issues.append(
                                ValidationIssue(
                                    issue_type="duplicate_string",
                                    severity="low",
                                    correct_match=string,
                                    details=f"Duplicate string '{string}' found in {section_name} section",
                                    suggested_action=f"Remove duplicate entry for '{string}' in {section_name} section",
                                )
                            )
                        seen_strings.add(string)

        # Check for duplicate strings across different sections (excluding handle/knot which can share)
        all_strings = {}
        for section_name, section_data in correct_matches.items():
            if not isinstance(section_data, dict):
                continue
            for brand_data in section_data.values():
                if isinstance(brand_data, dict):
                    for strings in brand_data.values():
                        if isinstance(strings, list):
                            for string in strings:
                                if string in all_strings:
                                    # Handle/knot can share the same string, so only flag if it's not handle/knot
                                    # Also skip if already flagged as within-section duplicate
                                    if (
                                        section_name not in ["handle", "knot"]
                                        and all_strings[string] not in ["handle", "knot"]
                                        and string not in within_section_duplicates
                                    ):
                                        issues.append(
                                            ValidationIssue(
                                                issue_type="duplicate_string",
                                                severity="low",
                                                correct_match=string,
                                                details=f"Duplicate string '{string}' found across multiple sections",
                                                suggested_action=f"Remove duplicate entry for '{string}' from one of the sections",
                                            )
                                        )
                                else:
                                    all_strings[string] = section_name

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
            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=f"String '{conflict_string}' appears in both brush and handle sections",
                    suggested_action=f"Remove '{conflict_string}' from either brush or handle section",
                )
            )

        for conflict_string in brush_knot_conflicts:
            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=f"String '{conflict_string}' appears in both brush and knot sections",
                    suggested_action=f"Remove '{conflict_string}' from either brush or knot section",
                )
            )

        for conflict_string in triple_conflicts:
            issues.append(
                ValidationIssue(
                    issue_type="cross_section_conflict",
                    severity="high",
                    correct_match=conflict_string,
                    details=f"String '{conflict_string}' appears in brush, handle, and knot sections",
                    suggested_action=f"Remove '{conflict_string}' from brush section (keep in handle and knot for composite brush)",
                )
            )

        return issues

    def _validate_brush_entry(
        self, brush_string: str, expected_data: Dict[str, Any], expected_section: str
    ) -> List[ValidationIssue]:
        """Validate a single brush entry using actual matching."""
        issues = []

        try:
            matcher = self._get_matcher("brush")

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
                        details=f"Brush string '{brush_string}' no longer matches any strategy",
                        suggested_action=f"Remove '{brush_string}' from correct_matches.yaml or update matching logic",
                    )
                )
                return issues

            matched_data = result.matched

            # Determine actual section based on result structure
            # Check for complete brush (has top-level brand/model)
            if matched_data.get("brand") and matched_data.get("model"):
                actual_section = "brush"
            # Check for composite brush (has nested handle and knot with data)
            elif (
                matched_data.get("handle")
                and matched_data.get("knot")
                and matched_data["handle"].get("brand")
                and matched_data["knot"].get("brand")
            ):
                actual_section = "handle_knot"
            # Check for handle-only (has nested handle with data, but no knot data)
            elif (
                matched_data.get("handle")
                and matched_data["handle"].get("brand")
                and (not matched_data.get("knot") or not matched_data["knot"].get("brand"))
            ):
                actual_section = "handle"
            # Check for knot-only (has nested knot with data, but no handle data)
            elif (
                matched_data.get("knot")
                and matched_data["knot"].get("brand")
                and (not matched_data.get("handle") or not matched_data["handle"].get("brand"))
            ):
                actual_section = "knot"
            else:
                actual_section = "unknown"

            # Check for structural changes
            if expected_section != actual_section:
                logger.debug(
                    f"Structural change detected: {brush_string} from {expected_section} to {actual_section}"
                )
                issues.append(
                    ValidationIssue(
                        issue_type="structural_change",
                        severity="high",
                        correct_match=brush_string,
                        expected_section=actual_section,  # Where it should be (current matching system)
                        actual_section=expected_section,  # Where it currently is (correct_matches.yaml)
                        details=f"Brush type changed from {expected_section} to {actual_section}",
                        suggested_action=f"Move '{brush_string}' from {expected_section} section to {actual_section} section",
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
                            details=f"Brand/model mismatch: expected '{expected_brand} {expected_model}', got '{actual_brand} {actual_model}'",
                            suggested_action=f"Update correct_matches.yaml to reflect new brand/model: '{actual_brand} {actual_model}'",
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
                                details=f"Handle brand/model mismatch: expected '{expected_handle_brand} {expected_handle_model}', got '{actual_handle_brand} {actual_handle_model}'",
                                suggested_action=f"Update correct_matches.yaml handle section to reflect new brand/model: '{actual_handle_brand} {actual_handle_model}'",
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
                                details=f"Knot brand/model mismatch: expected '{expected_knot_brand} {expected_knot_model}', got '{actual_knot_brand} {actual_knot_model}'",
                                suggested_action=f"Update correct_matches.yaml knot section to reflect new brand/model: '{actual_knot_brand} {actual_knot_model}'",
                            )
                        )

        except Exception as e:
            # Fail fast on internal errors
            logger.error("Error validating brush entry '%s': %s", brush_string, e)
            raise ValueError(f"Brush validation failed for '{brush_string}': {e}") from e

        return issues

    def _validate_simple_entry(
        self, field: str, entry_string: str, expected_brand: str, expected_model: str
    ) -> List[ValidationIssue]:
        """Validate a simple entry (razor, blade, soap) using actual matching."""
        issues = []

        try:
            matcher = self._get_matcher(field)

            # Run actual matching with bypass_correct_matches=True
            result = matcher.match(entry_string, bypass_correct_matches=True)

            if not result or not result.matched:
                # No match found
                issues.append(
                    ValidationIssue(
                        issue_type="no_match",
                        severity="high",
                        correct_match=entry_string,
                        details=f"{field.title()} string '{entry_string}' no longer matches any strategy",
                        suggested_action=f"Remove '{entry_string}' from correct_matches.yaml or update matching logic",
                    )
                )
                return issues

            matched_data = result.matched
            actual_brand = matched_data.get("brand")
            actual_model = matched_data.get("model")

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
                        details=f"Brand/model mismatch: expected '{expected_brand} {expected_model}', got '{actual_brand} {actual_model}'",
                        suggested_action=f"Update correct_matches.yaml to reflect new brand/model: '{actual_brand} {actual_model}'",
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
        """Collect all brush strings and their locations in correct_matches.yaml."""
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
        Validate correct_matches.yaml entries for the specified field using actual matching.

        Args:
            field: Field type to validate (razor, blade, brush, soap)

        Returns:
            ValidationResult containing validation issues and metrics
        """
        start_time = time.time()
        issues = []

        try:
            # Load correct_matches.yaml
            import yaml

            correct_matches_path = self.data_path / "correct_matches.yaml"
            with correct_matches_path.open("r", encoding="utf-8") as f:
                correct_matches = yaml.safe_load(f)

            # Validate data structure first
            structure_issues = self._validate_data_structure(correct_matches)
            issues.extend(structure_issues)

            # Validate field-specific entries
            if field == "brush":
                # First, collect all brush strings and their locations
                brush_string_locations = self._collect_brush_string_locations(correct_matches)

                # Validate each unique brush string
                for brush_string, locations in brush_string_locations.items():
                    # Determine expected structure based on locations
                    expected_section = self._determine_expected_section(locations)
                    expected_data = self._build_expected_data(
                        brush_string, locations, expected_section
                    )

                    # Validate the brush string
                    entry_issues = self._validate_brush_entry(
                        brush_string, expected_data, expected_section
                    )
                    issues.extend(entry_issues)

            else:
                # Validate simple entries (razor, blade, soap)
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
            else:
                field_section = correct_matches.get(field, {})
                for brand_data in field_section.values():
                    if isinstance(brand_data, dict):
                        for strings in brand_data.values():
                            if isinstance(strings, list):
                                total_entries += len(strings)

            processing_time = time.time() - start_time

            # Update performance metrics
            self._performance_metrics[field] = {
                "processing_time": processing_time,
                "total_entries": total_entries,
                "issues_found": len(issues),
                "validation_mode": "actual_matching",
            }

            return ValidationResult(
                field=field,
                total_entries=total_entries,
                issues=issues,
                processing_time=processing_time,
                validation_mode="actual_matching",
                strategy_stats={},  # TODO: Add strategy statistics
                performance_metrics=self._performance_metrics.get(field, {}),
            )

        except Exception as e:
            # Fail fast on internal errors
            logger.error("Error during %s validation: %s", field, e)
            raise ValueError(f"Validation failed for {field}: {e}") from e
