#!/usr/bin/env python3
"""Correct matches validation tool.

This tool validates correct_matches.yaml against current catalog files to ensure
previously approved matches are still aligned with catalog updates.
"""

import sys
import unicodedata
from pathlib import Path

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse  # noqa: E402
from typing import Dict, List, Optional, Any  # noqa: E402

from rich.console import Console  # noqa: E402

# Import the actual matchers
from sotd.match.blade_matcher import BladeMatcher  # noqa: E402
from sotd.match.brush_matcher import BrushMatcher  # noqa: E402
from sotd.match.config import BrushMatcherConfig  # noqa: E402
from sotd.match.razor_matcher import RazorMatcher  # noqa: E402
from sotd.match.soap_matcher import SoapMatcher  # noqa: E402


class ValidateCorrectMatches:
    """Validate correct_matches.yaml against current catalog files."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the validator.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self._data_dir = Path("data")
        self.correct_matches = None
        self._matchers = {}  # Lazy-loaded matchers cache
        self._fresh_matchers = {}  # Cached fresh matchers for validation
        self.catalog_cache = {}  # Cache for loaded catalog data

        # Get project root directory for absolute paths
        project_root = Path(__file__).parent.parent.parent.parent.parent

        # Initialize matchers with bypass configuration for validation
        self.brush_matcher = BrushMatcher(
            config=BrushMatcherConfig(
                catalog_path=project_root / "data/brushes.yaml",
                handles_path=project_root / "data/handles.yaml",
                knots_path=project_root / "data/knots.yaml",
                correct_matches_path=project_root / "data/correct_matches.yaml",
                bypass_correct_matches=True,  # Skip correct matches for validation
            )
        )
        self.blade_matcher = BladeMatcher(
            catalog_path=project_root / "data/blades.yaml",
            correct_matches_path=project_root / "data/correct_matches.yaml",
        )
        self.razor_matcher = RazorMatcher(
            catalog_path=project_root / "data/razors.yaml",
            correct_matches_path=project_root / "data/razors.yaml",
        )
        self.soap_matcher = SoapMatcher(
            catalog_path=project_root / "data/soaps.yaml",
            correct_matches_path=project_root / "data/soaps.yaml",
        )

        # Pre-load catalogs for commonly used fields
        try:
            self._load_catalog("blade")  # Pre-load blade catalog
            self._load_catalog("razor")  # Pre-load razor catalog
        except Exception:
            # Continue without pre-loading if catalogs aren't available
            # This allows the validator to work even if some catalogs are missing
            pass

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode text to handle different character encodings.

        Args:
            text: Text to normalize

        Returns:
            Normalized text using NFC form
        """
        return unicodedata.normalize("NFC", text)

    def _load_catalog(self, field: str) -> dict:
        """Load catalog data for a specific field type.

        Args:
            field: Field type to load (razor, blade, brush, soap)

        Returns:
            Loaded catalog data

        Raises:
            ValueError: If field type is unknown
            RuntimeError: If catalog loading fails
        """
        # Use cached data if available
        if field in self.catalog_cache:
            return self.catalog_cache[field]

        # Determine catalog path based on field
        if field == "blade":
            catalog_path = self.blade_matcher.catalog_path
        elif field == "razor":
            catalog_path = self.razor_matcher.catalog_path
        elif field == "brush":
            catalog_path = self.brush_matcher.config.catalog_path
        elif field == "soap":
            catalog_path = self.soap_matcher.catalog_path
        else:
            raise ValueError(f"Unknown field type: {field}")

        # Load catalog using the same pattern as BaseMatcher
        try:
            from sotd.utils.yaml_loader import load_yaml_with_nfc, UniqueKeyLoader

            catalog_data = load_yaml_with_nfc(catalog_path, loader_cls=UniqueKeyLoader)
            self.catalog_cache[field] = catalog_data
            return catalog_data
        except Exception as e:
            raise RuntimeError(f"Failed to load catalog for {field}: {e}")

    def get_parser(self) -> argparse.ArgumentParser:
        """Get CLI argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Validate correct_matches.yaml against current catalog files"
        )

        # Field selection
        field_group = parser.add_mutually_exclusive_group()
        field_group.add_argument(
            "--field",
            choices=["razor", "blade", "brush", "soap"],
            help="Validate specific field type",
        )
        field_group.add_argument(
            "--all-fields", action="store_true", help="Validate all field types"
        )

        # Behavior options
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be validated without running validation",
        )
        parser.add_argument(
            "--catalog-validation",
            action="store_true",
            help="Validate correct_matches.yaml against current catalog patterns",
        )

        return parser

    def run(self, args) -> Dict[str, List[Dict]]:
        """
        Run validation based on CLI arguments.

        Args:
            args: Parsed CLI arguments

        Returns:
            Dictionary mapping field names to lists of validation issues
        """
        # Determine which fields to validate
        fields_to_validate = []

        if args.all_fields:
            fields_to_validate = ["razor", "blade", "brush", "soap"]
        elif args.field:
            fields_to_validate = [args.field]
        else:
            # Default: validate all fields
            fields_to_validate = ["razor", "blade", "brush", "soap"]

        # Run validation for each field
        all_issues = {}

        for field in fields_to_validate:
            try:
                if args.catalog_validation:
                    issues = self.validate_correct_matches_against_catalog(field, args.verbose)
                else:
                    issues = self._validate_field(field)
                all_issues[field] = issues

                if args.verbose:
                    print(f"Validated {field}: {len(issues)} issues found")

            except Exception as e:
                if args.verbose:
                    print(f"Error validating {field}: {e}")
                all_issues[field] = []

        # Display results
        self._display_results(all_issues, args.verbose)

        return all_issues

    def _display_results(self, all_issues: Dict[str, List[Dict]], verbose: bool) -> None:
        """Display validation results.

        Args:
            all_issues: Dictionary mapping field names to lists of validation issues
            verbose: Whether to show verbose output
        """
        total_issues = sum(len(issues) for issues in all_issues.values())

        if total_issues == 0:
            self.console.print("✅ No validation issues found!")
            return

        self.console.print(f"\n❌ Found {total_issues} validation issues:")
        self.console.print("=" * 60)

        for field, issues in all_issues.items():
            if not issues:
                continue

            self.console.print(f"\n{field.upper()} ({len(issues)} issues):")
            self.console.print("-" * 40)

            for issue in issues:
                # Handle both old and new issue formats
                issue_type = issue.get("issue_type") or issue.get("type", "unknown")
                severity = issue.get("severity", "medium")  # Default to medium for new format

                # Color coding based on severity
                if severity == "high":
                    severity_icon = "🔴"
                elif severity == "medium":
                    severity_icon = "🟡"
                else:
                    severity_icon = "🔵"

                # For new catalog validation issues, show the essential details
                if issue_type in ["missing_brand", "missing_model", "wrong_location"]:
                    string = issue.get("string", "unknown")
                    expected_location = issue.get("expected_location", "unknown")
                    actual_location = issue.get("actual_location", "unknown")
                    message = issue.get("message", "")

                    main_message = f"'{string}' should be at {expected_location}"
                    if actual_location != "not found":
                        main_message += f" (currently at {actual_location})"

                    self.console.print(f"{severity_icon} {issue_type}: {main_message}")
                    if message:
                        self.console.print(f"   {message}")

                # For old catalog validation issues, show the essential details in the main message
                elif issue_type in ["catalog_pattern_mismatch", "catalog_pattern_no_match"]:
                    correct_match = issue.get("correct_match", "unknown")
                    expected_brand = issue.get("expected_brand", "unknown")
                    expected_model = issue.get("expected_model", "unknown")

                    if issue_type == "catalog_pattern_mismatch":
                        actual_brand = issue.get("actual_brand", "unknown")
                        actual_model = issue.get("actual_model", "unknown")
                        main_message = (
                            f"'{correct_match}' expected: {expected_brand} "
                            f"{expected_model}, actual: {actual_brand} {actual_model}"
                        )
                    else:  # catalog_pattern_no_match
                        main_message = (
                            f"'{correct_match}' expected: {expected_brand} "
                            f"{expected_model}, actual: NO MATCH"
                        )

                    self.console.print(f"{severity_icon} {issue_type}: {main_message}")
                else:
                    # For other issue types, show the suggested action
                    suggested_action = issue.get("suggested_action", "")
                    self.console.print(f"{severity_icon} {issue_type}: {suggested_action}")

                if verbose and "details" in issue:
                    self.console.print(f"   Details: {issue['details']}")

    def _validate_field(self, field: str) -> List[Dict]:
        """Validate correct matches for specific field using actual matchers.

        Args:
            field: Field type to validate

        Returns:
            List of validation issues found
        """
        if self.correct_matches is None:
            try:
                self.correct_matches = self._load_correct_matches()
            except FileNotFoundError:
                # If correct_matches.yaml doesn't exist, there's nothing to validate
                return []

        issues = []

        # Check if field exists in correct matches
        if field not in self.correct_matches:
            return issues

        # Check for duplicate strings first (highest priority)
        duplicate_issues = self._check_duplicate_strings(field)
        issues.extend(duplicate_issues)

        # Check for format mismatches (blade field only)
        format_issues = self._check_format_mismatches(field)
        issues.extend(format_issues)

        # MOST IMPORTANT: Validate that every string still matches to the same categorization
        # This ensures catalog updates don't break previously approved matches
        catalog_validation_issues = self.validate_correct_matches_against_catalog(
            field, False
        )  # No verbose in this context
        issues.extend(catalog_validation_issues)

        return issues

    def validate_correct_matches_against_catalog(
        self, field: str, verbose: bool = False
    ) -> List[Dict]:
        """
        Validate that existing correct_matches.yaml entries would still match
        to the same categorization by generating a "what should be" version
        and diffing it against the current one.

        This ensures catalog updates don't break previously approved matches
        by reusing the existing matcher logic to determine where strings should be saved.

        Args:
            field: Field type to validate
            verbose: Whether to show verbose debug output

        Returns:
            List of validation issues found
        """
        if field != "brush":
            # Only brush field is supported for now
            return []

        # Ensure correct_matches is loaded
        if not self.correct_matches:
            self._load_correct_matches()

        issues = []

        # Get the brush matcher to determine where strings should be saved
        matcher = self._get_matcher(field)

        # Generate "what should be" correct_matches.yaml by running all strings through matchers
        expected_structure = self._generate_expected_correct_matches_structure(matcher, verbose)

        # Compare expected vs actual structure
        comparison_issues = self._compare_structures(
            expected_structure, self.correct_matches or {}, verbose
        )
        issues.extend(comparison_issues)

        return issues

    def _generate_expected_correct_matches_structure(
        self, matcher, verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Generate the expected correct_matches.yaml structure by running all strings
        through the matchers (bypassing correct_matches.yaml).

        Returns:
            Dictionary representing what the correct_matches.yaml should look like
        """
        expected_structure = {"brush": {}}

        # Get all brush entries from current correct_matches.yaml
        brush_section = (self.correct_matches or {}).get("brush", {})

        for brand, brand_data in brush_section.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                for correct_match in strings:
                    # Run through matcher to see where this string should be saved
                    match_result = self._match_using_catalog_patterns(matcher, correct_match)

                    if verbose:
                        print(f"\n🔍 DEBUG: Testing '{correct_match}'")
                        print(f"   Expected: {brand} {model}")
                        print(f"   Match result: {match_result}")

                    if match_result and "brand" in match_result:
                        actual_brand = match_result["brand"]

                        # For brush matches, check both top-level model and knot.model
                        actual_model = None
                        if "model" in match_result and match_result["model"] is not None:
                            actual_model = match_result["model"]
                        elif "knot" in match_result and isinstance(match_result["knot"], dict):
                            # Check if model info is in the knot field when top-level is None
                            knot_data = match_result["knot"]
                            if "model" in knot_data and knot_data["model"] is not None:
                                actual_model = knot_data["model"]

                        # Add to expected structure
                        if actual_brand not in expected_structure["brush"]:
                            expected_structure["brush"][actual_brand] = {}

                        if actual_model not in expected_structure["brush"][actual_brand]:
                            expected_structure["brush"][actual_brand][actual_model] = []

                        expected_structure["brush"][actual_brand][actual_model].append(
                            correct_match
                        )

        return expected_structure

    def _compare_structures(
        self, expected: Dict[str, Any], actual: Dict[str, Any], verbose: bool = False
    ) -> List[Dict]:
        """
        Compare expected vs actual correct_matches.yaml structures and return issues.

        Args:
            expected: Expected structure from matcher output
            actual: Current correct_matches.yaml structure
            verbose: Whether to show verbose output

        Returns:
            List of validation issues found
        """
        issues = []

        # Compare brush section
        expected_brush = expected.get("brush", {})
        actual_brush = actual.get("brush", {})

        # Check for strings that should be in different locations
        for brand, brand_data in expected_brush.items():
            if brand not in actual_brush:
                # Brand doesn't exist in actual
                for model, strings in brand_data.items():
                    for string in strings:
                        issue = {
                            "type": "missing_brand",
                            "string": string,
                            "expected_location": f"{brand} {model}",
                            "actual_location": "not found",
                            "message": f"String '{string}' should be saved under brand '{brand}' "
                            f"model '{model}' but this brand doesn't exist in "
                            f"correct_matches.yaml. This suggests a new brand needs "
                            f"to be added.",
                        }
                        issues.append(issue)
                continue

            actual_brand_data = actual_brush[brand]
            for model, strings in brand_data.items():
                if model not in actual_brand_data:
                    # Model doesn't exist in actual
                    for string in strings:
                        issue = {
                            "type": "missing_model",
                            "string": string,
                            "expected_location": f"{brand} {model}",
                            "actual_location": f"{brand} (model not found)",
                            "message": f"String '{string}' should be saved under brand '{brand}' "
                            f"model '{model}' but this model doesn't exist in "
                            f"correct_matches.yaml. This suggests a new model needs "
                            f"to be added.",
                        }
                        issues.append(issue)
                    continue

                actual_strings = actual_brand_data[model]
                for string in strings:
                    if string not in actual_strings:
                        # String is in wrong location - find where it actually is
                        actual_location = self._find_actual_location(string)

                        issue = {
                            "type": "wrong_location",
                            "string": string,
                            "expected_location": f"{brand} {model}",
                            "actual_location": actual_location,
                            "message": f"String '{string}' should be saved under brand '{brand}' "
                            f"model '{model}' but it's currently saved elsewhere. "
                            f"This suggests the string needs to be moved.",
                        }
                        issues.append(issue)

        return issues

    def _find_actual_location(self, string: str) -> str:
        """
        Find where a string is actually located in the current correct_matches.yaml.

        Args:
            string: The string to find

        Returns:
            String describing where the string is currently located
        """
        if not self.correct_matches:
            return "not found"

        brush_section = self.correct_matches.get("brush", {})

        for brand, brand_data in brush_section.items():
            if not isinstance(brand_data, dict):
                continue

            for model, strings in brand_data.items():
                if not isinstance(strings, list):
                    continue

                if string in strings:
                    return f"{brand} {model}"

        return "not found"

    def _get_matcher(self, field: str):
        """Get matcher for field, using pre-created matchers with bypass config.

        Args:
            field: Field type to get matcher for

        Returns:
            Matcher instance for the field
        """
        if field == "brush":
            return self.brush_matcher
        elif field == "blade":
            return self.blade_matcher
        elif field == "razor":
            return self.razor_matcher
        elif field == "soap":
            return self.soap_matcher
        else:
            raise ValueError(f"Unknown field: {field}")

    def _match_using_catalog_patterns(self, matcher, value: str) -> Optional[Dict]:
        """Match using catalog patterns with correct_matches bypassed.

        Args:
            matcher: Matcher instance to use
            value: Value to match

        Returns:
            Match result dictionary with pattern information or None
        """
        # For validation, we want to test what the regex patterns would match to
        # if the correct matches didn't exist. We create fresh matchers without correct matches.

        # Determine matcher type and get cached fresh matcher
        matcher_type = type(matcher).__name__

        if matcher_type not in self._fresh_matchers:
            # Create and cache a fresh matcher without correct matches but with
            # proper catalog configuration
            if isinstance(matcher, BladeMatcher):
                fresh_matcher = BladeMatcher(
                    catalog_path=Path("data/blades.yaml"),
                    correct_matches_path=Path("data/correct_matches.yaml"),
                )
                fresh_matcher.correct_matches = {}
            elif isinstance(matcher, RazorMatcher):
                fresh_matcher = RazorMatcher(
                    catalog_path=Path("data/razors.yaml"),
                    correct_matches_path=Path("data/correct_matches.yaml"),
                )
                fresh_matcher.correct_matches = {}
            elif isinstance(matcher, BrushMatcher):
                fresh_matcher = BrushMatcher(
                    config=BrushMatcherConfig(
                        catalog_path=Path("data/brushes.yaml"),
                        handles_path=Path("data/handles.yaml"),
                        knots_path=Path("data/knots.yaml"),
                        correct_matches_path=Path("data/correct_matches.yaml"),
                        bypass_correct_matches=True,  # Skip correct matches for validation
                    )
                )
            elif isinstance(matcher, SoapMatcher):
                fresh_matcher = SoapMatcher(
                    catalog_path=Path("data/soaps.yaml"),
                    correct_matches_path=Path("data/correct_matches.yaml"),
                )
                fresh_matcher.correct_matches = {}
            else:
                # Fallback to original method for unknown matcher types
                original_correct_matches = None
                if hasattr(matcher, "correct_matches"):
                    original_correct_matches = matcher.correct_matches
                    matcher.correct_matches = {}

                try:
                    match_result = matcher.match(value)

                    # Convert MatchResult to dict if needed for backward compatibility
                    if hasattr(match_result, "matched"):
                        # MatchResult object
                        if match_result.matched:
                            result = match_result.matched
                            if hasattr(match_result, "pattern"):
                                result["pattern"] = match_result.pattern
                            return result
                        return None
                    else:
                        # Dict object
                        if match_result and match_result.get("matched"):
                            return match_result.get("matched")
                        return None
                finally:
                    # Restore original correct matches
                    if original_correct_matches is not None:
                        matcher.correct_matches = original_correct_matches

            # Cache the fresh matcher
            self._fresh_matchers[matcher_type] = fresh_matcher

        # Use the cached fresh matcher
        fresh_matcher = self._fresh_matchers[matcher_type]

        # Get the match result with pattern information
        match_result = fresh_matcher.match(value)

        if hasattr(match_result, "matched") and match_result.matched:
            result = match_result.matched.copy()
            if hasattr(match_result, "pattern"):
                result["pattern"] = match_result.pattern
            return result
        elif isinstance(match_result, dict) and match_result.get("matched"):
            result = match_result["matched"].copy()
            if "pattern" in match_result:
                result["pattern"] = match_result["pattern"]
            return result

        return None

    def _load_correct_matches(self) -> Dict:
        """Load correct matches from file.

        Returns:
            Correct matches data dictionary

        Raises:
            FileNotFoundError: If correct_matches.yaml doesn't exist
            ValueError: If correct_matches.yaml is invalid or structure is wrong
        """
        import yaml

        correct_matches_path = self._data_dir / "correct_matches.yaml"
        if not correct_matches_path.exists():
            raise FileNotFoundError(f"Correct matches file not found: {correct_matches_path}")
        try:
            with open(correct_matches_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML from {correct_matches_path}: {e}")
        # Validate structure: must be dict of field -> dict of matches
        if not isinstance(data, dict):
            raise ValueError(
                f"Correct matches file {correct_matches_path} must be a dict at top level"
            )
        for field, matches in data.items():
            if not isinstance(matches, dict):
                raise ValueError(f"Field {field} in {correct_matches_path} must be a dict")
        return data

    def _check_duplicate_strings(self, field: str) -> List[Dict]:
        """Check for duplicate strings in correct matches.

        Args:
            field: Field type to check

        Returns:
            List of duplicate string issues
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        # Ensure catalog is loaded for format-aware validation
        if field == "blade" and field not in self.catalog_cache:
            try:
                self._load_catalog(field)
            except Exception as e:
                # Log warning but continue with basic validation
                if self.console:
                    self.console.print(f"Warning: Could not load {field} catalog: {e}")
                # Continue without catalog data - basic duplicate detection will still work

        # Track all strings and their locations with format information
        string_locations = {}  # string -> list of (brand, model, format) tuples

        if field == "blade":
            # Special handling for blade structure: format -> brand -> model -> strings
            for format_name, brands in self.correct_matches[field].items():
                for brand, models in brands.items():
                    for model, correct_matches in models.items():
                        for correct_match in correct_matches:
                            current_format = format_name  # Use the format from the structure

                            # Check if this string already exists with the same format
                            if correct_match in string_locations:
                                for (
                                    existing_brand,
                                    existing_model,
                                    existing_format,
                                ) in string_locations[correct_match]:
                                    if existing_format == current_format:
                                        # Found a forbidden duplicate (same format)
                                        issue = {
                                            "issue_type": "duplicate_string",
                                            "field": field,
                                            "duplicate_string": correct_match,
                                            "first_location": {
                                                "brand": existing_brand,
                                                "model": existing_model,
                                            },
                                            "second_location": {"brand": brand, "model": model},
                                            "severity": "high",
                                            "suggested_action": (
                                                f"Remove duplicate string '{correct_match}' from "
                                                f"either {existing_brand}:{existing_model} or "
                                                f"{brand}:{model}. "
                                                f"Each string must appear only once per format in "
                                                f"correct_matches.yaml"
                                            ),
                                            "details": (
                                                f"String '{correct_match}' appears in both "
                                                f"{existing_brand}:{existing_model} and "
                                                f"{brand}:{model} with the same format "
                                                f"({current_format}). "
                                                f"This creates ambiguity - the matcher won't know "
                                                f"which to pick."
                                            ),
                                        }
                                        issues.append(issue)

                            # Add current location to tracking
                            if correct_match not in string_locations:
                                string_locations[correct_match] = []
                            string_locations[correct_match].append((brand, model, current_format))
        else:
            # Standard handling for other fields: brand -> model -> strings
            for brand, models in self.correct_matches[field].items():
                for model, correct_matches in models.items():
                    for correct_match in correct_matches:
                        current_format = "default"  # For non-blade fields

                        # Check if this string already exists
                        if correct_match in string_locations:
                            for (
                                existing_brand,
                                existing_model,
                                existing_format,
                            ) in string_locations[correct_match]:
                                # For non-blade fields, any duplicate is forbidden
                                issue = {
                                    "issue_type": "duplicate_string",
                                    "field": field,
                                    "duplicate_string": correct_match,
                                    "first_location": {
                                        "brand": existing_brand,
                                        "model": existing_model,
                                    },
                                    "second_location": {"brand": brand, "model": model},
                                    "severity": "high",
                                    "suggested_action": (
                                        f"Remove duplicate string '{correct_match}' from either "
                                        f"{existing_brand}:{existing_model} or "
                                        f"{brand}:{model}. "
                                        f"Each string must appear only once in "
                                        f"correct_matches.yaml"
                                    ),
                                    "details": (
                                        f"String '{correct_match}' appears in both "
                                        f"{existing_brand}:{existing_model} and "
                                        f"{brand}:{model}. "
                                        f"This creates ambiguity - the matcher won't know "
                                        f"which to pick."
                                    ),
                                }
                                issues.append(issue)

                        # Add current location to tracking
                        if correct_match not in string_locations:
                            string_locations[correct_match] = []
                        string_locations[correct_match].append((brand, model, current_format))

        return issues

    def _check_format_mismatches(self, field: str) -> List[Dict]:
        """Check for format mismatches by running actual matchers against correct matches.

        This validates that when we run the actual matchers against previously approved
        correct matches, they still return the same categorization. This ensures that
        catalog updates don't break previously approved matches.

        Args:
            field: Field type to check

        Returns:
            List of format mismatch issues
        """
        issues = []

        if field != "blade" or self.correct_matches is None:
            return issues

        if "blade" not in self.correct_matches:
            return issues

        # Check each blade entry by running it through the actual blade matcher
        for format_name, brands in self.correct_matches["blade"].items():
            for brand, models in brands.items():
                for model, correct_matches in models.items():
                    for correct_match in correct_matches:
                        # Run the actual blade matcher to see what it returns
                        try:
                            match_result = self.blade_matcher.match(
                                correct_match.lower(), original=correct_match
                            )

                            if match_result and match_result.matched:
                                matched_data = match_result.matched

                                # Check if the matcher returned a different format than expected
                                if "format" in matched_data:
                                    actual_format = matched_data["format"]
                                    if actual_format != format_name:
                                        issues.append(
                                            {
                                                "issue_type": "format_mismatch",
                                                "field": field,
                                                "correct_match": correct_match,
                                                "expected_format": format_name,
                                                "actual_format": actual_format,
                                                "severity": "high",
                                                "suggested_action": (
                                                    f"Correct match '{correct_match}' was categorized as "
                                                    f"'{format_name}' but the current matcher returns "
                                                    f"'{actual_format}'. This suggests catalog changes "
                                                    f"have broken this previously approved match."
                                                ),
                                                "details": (
                                                    f"Matcher validation failed: '{correct_match}' "
                                                    f"expected format '{format_name}' but got "
                                                    f"'{actual_format}' from current catalog."
                                                ),
                                            }
                                        )
                                else:
                                    # No format field returned - this might indicate a problem
                                    issues.append(
                                        {
                                            "issue_type": "missing_format",
                                            "field": field,
                                            "correct_match": correct_match,
                                            "expected_format": format_name,
                                            "severity": "medium",
                                            "suggested_action": (
                                                f"Correct match '{correct_match}' was categorized as "
                                                f"'{format_name}' but the current matcher doesn't "
                                                f"return a format field. Check if catalog structure "
                                                f"has changed."
                                            ),
                                            "details": (
                                                f"Matcher returned no format field for '{correct_match}' "
                                                f"which was expected to be '{format_name}'."
                                            ),
                                        }
                                    )
                            else:
                                # Matcher failed to match - this is a problem
                                issues.append(
                                    {
                                        "issue_type": "match_failure",
                                        "field": field,
                                        "correct_match": correct_match,
                                        "expected_format": format_name,
                                        "severity": "high",
                                        "suggested_action": (
                                            f"Correct match '{correct_match}' was categorized as "
                                            f"'{format_name}' but the current matcher fails to "
                                            f"match it at all. This suggests catalog changes "
                                            f"have broken this previously approved match."
                                        ),
                                        "details": (
                                            f"Matcher failed to match '{correct_match}' which was "
                                            f"expected to be '{format_name}'. This indicates "
                                            f"catalog changes have broken the match."
                                        ),
                                    }
                                )

                        except Exception as e:
                            # Matcher threw an error - this is a problem
                            issues.append(
                                {
                                    "issue_type": "matcher_error",
                                    "field": field,
                                    "correct_match": correct_match,
                                    "expected_format": format_name,
                                    "error": str(e),
                                    "severity": "high",
                                    "suggested_action": (
                                        f"Correct match '{correct_match}' caused an error in the "
                                        f"current matcher: {e}. This suggests catalog changes "
                                        f"have broken this previously approved match."
                                    ),
                                    "details": (
                                        f"Matcher error for '{correct_match}': {e}. This indicates "
                                        f"catalog changes have broken the match."
                                    ),
                                }
                            )

        return issues

    def main(self, args: Optional[List[str]] = None) -> int:
        """Main entry point for CLI.

        Args:
            args: Command line arguments (optional)

        Returns:
            Exit code (0 for success, 1 for issues found)
        """
        parser = self.get_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.dry_run:
            self._show_dry_run_info(parsed_args)
            return 0

        try:
            all_issues = self.run(parsed_args)
            total_issues = sum(len(issues) for issues in all_issues.values())
            return 1 if total_issues > 0 else 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _show_dry_run_info(self, args) -> None:
        """Show dry run information.

        Args:
            args: Parsed arguments
        """
        print("Dry run mode - would validate:")
        if args.all_fields:
            print("  All fields: razor, blade, brush, soap")
        elif args.field:
            print(f"  Field: {args.field}")
        else:
            print("  All fields: razor, blade, brush, soap")
        print(f"  Verbose: {args.verbose}")


def main():
    """Main entry point."""
    validator = ValidateCorrectMatches()
    return validator.main()


if __name__ == "__main__":
    sys.exit(main())
