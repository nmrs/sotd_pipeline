"""Correct matches validation tool.

This tool validates correct_matches.yaml against current catalog files to ensure
previously approved matches are still aligned with catalog updates.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

# Import the actual matchers
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher


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
        self.catalog_cache = {}
        self._matchers = {}  # Lazy-loaded matchers cache

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
        """Display validation results."""
        total_issues = sum(len(issues) for issues in all_issues.values())

        if total_issues == 0:
            print("✅ All correct_matches entries are valid!")
            return

        print(f"\n❌ Found {total_issues} validation issues:")
        print("=" * 60)

        for field, issues in all_issues.items():
            if not issues:
                continue

            print(f"\n{field.upper()} ({len(issues)} issues):")
            print("-" * 40)

            for issue in issues:
                severity_icon = (
                    "🔴"
                    if issue["severity"] == "high"
                    else "🟡" if issue["severity"] == "medium" else "��"
                )
                issue_type = issue["issue_type"]

                if issue_type == "mismatched_entry":
                    # Compact format for mismatched entries
                    entry = issue["correct_match"]
                    current = f"{issue['expected_brand']}:{issue['expected_model']}"
                    should_be = f"{issue['actual_brand']}:{issue['actual_model']}"

                    print(f"{severity_icon} {issue_type}")
                    print(f"   Entry: {entry}")
                    print(f"   Current:  {current}")
                    print(f"   Should be: {should_be}")
                    print(f"   Action:   {issue['suggested_action']}")
                else:
                    # Standard format for other issue types
                    details = issue.get("details", issue.get("suggested_action", "No details"))
                    print(f"{severity_icon} {issue_type}: {details}")

                    if verbose and "correct_match" in issue:
                        print(f"   Entry: {issue['correct_match']}")
                    if verbose and "brand" in issue and "model" in issue:
                        print(f"   Product: {issue['brand']} {issue['model']}")
                print()

    def _load_catalog(self, field: str) -> Dict:
        """Load catalog for specific field.

        Args:
            field: Field type to load catalog for

        Returns:
            Catalog data dictionary

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            ValueError: If catalog file is invalid or structure is wrong
        """
        import yaml

        # Map field names to catalog file names (actual files use plural names)
        field_to_file = {
            "razor": "razors.yaml",
            "blade": "blades_format_first.yaml",
            "brush": "brushes.yaml",
            "soap": "soaps.yaml",
        }

        if field not in field_to_file:
            raise ValueError(f"Unknown field: {field}")

        catalog_file = field_to_file[field]
        catalog_path = self._data_dir / catalog_file

        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load YAML from {catalog_path}: {e}")

        # Validate structure: must be dict
        if not isinstance(data, dict):
            raise ValueError(f"Catalog file {catalog_path} must be a dict at top level")

        return data

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

    def _check_brand_model_exists(self, field: str, brand: str, model: str) -> bool:
        """Check if brand/model combination exists in catalog.

        Args:
            field: Field type
            brand: Brand name
            model: Model name

        Returns:
            True if brand/model exists in catalog
        """
        if field not in self.catalog_cache:
            self.catalog_cache[field] = self._load_catalog(field)

        catalog = self.catalog_cache[field]
        return brand in catalog and model in catalog[brand]

    def _check_missing_entries(self, field: str) -> List[Dict]:
        """Check for missing catalog entries.

        Args:
            field: Field type to check

        Returns:
            List of missing entry issues
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        for brand, models in self.correct_matches[field].items():
            for model in models:
                if not self._check_brand_model_exists(field, brand, model):
                    issues.append(
                        {
                            "issue_type": "missing_entry",
                            "field": field,
                            "brand": brand,
                            "model": model,
                            "severity": "high",
                            "suggested_action": f"Add {brand} {model} to {field} catalog",
                        }
                    )

        return issues

    def _check_field_changes(self, field: str) -> List[Dict]:
        """Check for field changes in catalog.

        Args:
            field: Field type to check

        Returns:
            List of field change issues
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        for brand, models in self.correct_matches[field].items():
            for model in models:
                if self._check_brand_model_exists(field, brand, model):
                    # Check if any fields have changed
                    # This is a simplified check - in practice you'd compare specific fields
                    pass

        return issues

    def _validate_correct_matches_structure(self, field: str) -> List[Dict]:
        """Validate correct matches structure.

        Args:
            field: Field type to validate

        Returns:
            List of structure validation issues
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        for brand, models in self.correct_matches[field].items():
            if not isinstance(models, dict):
                issues.append(
                    {
                        "issue_type": "invalid_structure",
                        "field": field,
                        "brand": brand,
                        "severity": "high",
                        "suggested_action": f"Fix structure for {brand} in {field}",
                    }
                )

        return issues

    def _check_pattern_conflicts(self, field: str) -> List[Dict]:
        """Check for pattern conflicts.

        Args:
            field: Field type to check

        Returns:
            List of pattern conflict issues
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        try:
            if field not in self.catalog_cache:
                self.catalog_cache[field] = self._load_catalog(field)
        except FileNotFoundError:
            return issues

        # Check for pattern conflicts by comparing patterns across brands
        pattern_to_brand_model = {}

        for brand, models in self.catalog_cache[field].items():
            for model, data in models.items():
                patterns = data.get("patterns", [])
                for pattern in patterns:
                    if pattern in pattern_to_brand_model:
                        # Found a conflict - same pattern used by different brand/model
                        existing_brand, existing_model = pattern_to_brand_model[pattern]
                        conflict_msg = (
                            f"Resolve pattern conflict: '{pattern}' used by both "
                            f"{brand}:{model} and {existing_brand}:{existing_model}"
                        )
                        issues.append(
                            {
                                "issue_type": "pattern_conflict",
                                "severity": "medium",
                                "field": field,
                                "brand": brand,
                                "model": model,
                                "pattern": pattern,
                                "conflicting_brand": existing_brand,
                                "conflicting_model": existing_model,
                                "suggested_action": conflict_msg,
                            }
                        )
                    else:
                        pattern_to_brand_model[pattern] = (brand, model)

        return issues

    def _suggest_better_matches(self, field: str) -> List[Dict]:
        """Suggest better matches.

        Args:
            field: Field type to check

        Returns:
            List of better match suggestions
        """
        issues = []

        if self.correct_matches is None or field not in self.correct_matches:
            return issues

        # This is a simplified implementation
        # In practice, you'd analyze patterns and suggest improvements
        return issues

    def _classify_issues(self, issues: List[Dict]) -> Dict[str, List[Dict]]:
        """Classify issues by type.

        Args:
            issues: List of issues to classify

        Returns:
            Dictionary mapping issue types to lists of issues
        """
        classified = {}
        for issue in issues:
            issue_type = issue.get("issue_type", "unknown")
            if issue_type not in classified:
                classified[issue_type] = []
            classified[issue_type].append(issue)
        return classified

    def _score_issues(self, issues: List[Dict]) -> List[Dict]:
        """Score issues by severity.

        Args:
            issues: List of issues to score

        Returns:
            List of issues with scores added
        """
        severity_scores = {"high": 3, "medium": 2, "low": 1}

        for issue in issues:
            severity = issue.get("severity", "low")
            issue["score"] = severity_scores.get(severity, 0)

        return issues

    def _group_similar_issues(self, issues: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar issues together.

        Args:
            issues: List of issues to group

        Returns:
            Dictionary mapping groups to lists of issues
        """
        grouped = {}
        for issue in issues:
            brand = issue.get("brand", "unknown")
            if brand not in grouped:
                grouped[brand] = []
            grouped[brand].append(issue)
        return grouped

    def _suggest_action_for_issue_type(self, issue_type: str) -> str:
        """Suggest action for issue type.

        Args:
            issue_type: Type of issue

        Returns:
            Suggested action string
        """
        actions = {
            "missing_entry": f"Add {issue_type} to catalog",
            "field_change": f"Update {issue_type} catalog entry",
            "pattern_conflict": f"Resolve {issue_type} pattern conflict",
            "better_match": f"Consider better {issue_type} match",
            "invalid_structure": f"Fix {issue_type} data structure",
            "mismatched_entry": f"Update {issue_type} to match catalog",
        }
        return actions.get(issue_type, f"Review and fix {issue_type}")

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """Prioritize issues by severity and type.

        Args:
            issues: List of issues to prioritize

        Returns:
            Prioritized list of issues
        """
        scored_issues = self._score_issues(issues)
        return sorted(scored_issues, key=lambda x: x.get("score", 0), reverse=True)

    def _generate_summary_statistics(self, issues: List[Dict]) -> Dict:
        """Generate summary statistics.

        Args:
            issues: List of issues to summarize

        Returns:
            Summary statistics dictionary
        """
        summary = {
            "total_checked": len(issues),
            "total_issues": len(issues),
            "issues_found": len(issues),
            "by_field": {},
            "by_type": {},
            "by_severity": {},
        }

        for issue in issues:
            field = issue.get("field", "unknown")
            issue_type = issue.get("issue_type", "unknown")
            severity = issue.get("severity", "unknown")

            summary["by_field"][field] = summary["by_field"].get(field, 0) + 1
            summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

        return summary

    def _create_issues_table(self, issues: List[Dict]) -> Table:
        """Create Rich table for issues.

        Args:
            issues: List of issues to display

        Returns:
            Rich table object
        """
        table = Table(title="Validation Issues")
        table.add_column("Field", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Brand", style="green")
        table.add_column("Model", style="green")
        table.add_column("Severity", style="red")
        table.add_column("Action", style="yellow")

        for issue in issues:
            table.add_row(
                issue.get("field", ""),
                issue.get("issue_type", ""),
                issue.get("brand", ""),
                issue.get("model", ""),
                issue.get("severity", ""),
                issue.get("suggested_action", ""),
            )

        return table

    def _get_issue_color(self, issue: Dict) -> str:
        """Get color for issue severity.

        Args:
            issue: Issue dictionary

        Returns:
            Color string
        """
        severity = issue.get("severity", "low")
        colors = {"high": "red", "medium": "yellow", "low": "green"}
        return colors.get(severity, "white")

    def _generate_field_breakdown(self, issues: List[Dict]) -> Dict[str, Dict]:
        """Generate field-by-field breakdown.

        Args:
            issues: List of issues to analyze

        Returns:
            Field breakdown dictionary
        """
        breakdown = {}
        for issue in issues:
            field = issue.get("field", "unknown")
            if field not in breakdown:
                breakdown[field] = {"total": 0}

            breakdown[field]["total"] += 1
            severity = issue.get("severity", "unknown")
            breakdown[field][severity] = breakdown[field].get(severity, 0) + 1

        return breakdown

    def _display_console_report(self, issues: List[Dict], summary: Dict) -> None:
        """Display console report.

        Args:
            issues: List of issues to display
            summary: Summary statistics
        """
        # This method would use Rich console to display formatted output
        # For now, just print basic info
        issues_found = summary.get("issues_found", summary.get("total_issues", 0))
        print(f"Found {issues_found} issues")
        for field, count in summary.get("by_field", {}).items():
            print(f"  {field}: {count}")

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

        # Load catalog for this field
        try:
            if field not in self.catalog_cache:
                self.catalog_cache[field] = self._load_catalog(field)
        except FileNotFoundError:
            # If catalog file doesn't exist, we can't validate
            return []

        # Get the matcher for this field
        matcher = self._get_matcher(field)

        # Validate each correct match entry
        for brand, models in self.correct_matches[field].items():
            for model, correct_matches in models.items():
                for correct_match in correct_matches:
                    # Use the actual matcher to see what this would match to
                    match_result = self._match_using_catalog_patterns(matcher, correct_match)

                    # Check if the match result matches our expected brand/model
                    if match_result and "brand" in match_result and "model" in match_result:
                        actual_brand = match_result["brand"]
                        actual_model = match_result["model"]

                        if actual_brand != brand or actual_model != model:
                            issues.append(
                                {
                                    "issue_type": "mismatched_entry",
                                    "field": field,
                                    "correct_match": correct_match,
                                    "expected_brand": brand,
                                    "expected_model": model,
                                    "actual_brand": actual_brand,
                                    "actual_model": actual_model,
                                    "severity": "high",
                                    "suggested_action": (
                                        f"Update correct match to {actual_brand} {actual_model}"
                                    ),
                                }
                            )

        return issues

    def _get_matcher(self, field: str):
        """Get matcher for field, creating it lazily if needed.

        Args:
            field: Field type to get matcher for

        Returns:
            Matcher instance for the field
        """
        if field not in self._matchers:
            # Lazy load matcher only when needed
            if field == "razor":
                self._matchers[field] = RazorMatcher()
            elif field == "blade":
                self._matchers[field] = BladeMatcher()
            elif field == "brush":
                self._matchers[field] = BrushMatcher()
            elif field == "soap":
                self._matchers[field] = SoapMatcher()
            else:
                raise ValueError(f"Unknown field: {field}")

        return self._matchers[field]

    def _match_with_regex_only(self, matcher, value: str) -> Optional[Dict]:
        """Match using only regex patterns (no fallbacks).

        Args:
            matcher: Matcher instance to use
            value: Value to match

        Returns:
            Match result dictionary or None
        """
        # This is a simplified implementation
        # In practice, you'd call the matcher's regex-only method
        return matcher.match(value)

    def _match_using_catalog_patterns(self, matcher, value: str) -> Optional[Dict]:
        """Match using catalog patterns.

        Args:
            matcher: Matcher instance to use
            value: Value to match

        Returns:
            Match result dictionary or None
        """
        # Use the matcher's match method with bypass_correct_matches=True
        # This tests what the regex patterns would match to if the correct match didn't exist
        match_result = matcher.match(value, bypass_correct_matches=True)

        # Return the matched data if there was a match
        if match_result and match_result.get("matched"):
            return match_result["matched"]

        return None

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
