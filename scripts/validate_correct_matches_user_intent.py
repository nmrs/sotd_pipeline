#!/usr/bin/env python3
"""
Script to validate and enhance existing correct_matches directory entries with user intent data.

This script:
1. Extracts all brush entries from data/correct_matches directory
2. Runs each entry through BrushMatcher to detect user intent
3. For successful matches: Augments correct_matches directory with user_intent field
4. For failed matches: Documents entries requiring manual validation
5. Creates a validation report with success/failure statistics
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sotd.match.brush_matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig


class CorrectMatchesValidator:
    """Validator for correct_matches directory entries with user intent enhancement."""

    def __init__(self):
        """Initialize the validator with brush matcher."""
        self.config = BrushMatcherConfig.create_default()
        self.brush_matcher = BrushMatcher(config=self.config)
        self.correct_matches_path = Path("data/correct_matches")

    def load_correct_matches(self) -> Dict[str, Any]:
        """Load correct_matches from directory structure."""
        if not self.correct_matches_path.exists():
            raise FileNotFoundError(f"Correct matches directory not found: {self.correct_matches_path}")

        correct_matches = {}
        
        # Load all field files from directory structure
        for field_file in self.correct_matches_path.glob("*.yaml"):
            field_name = field_file.stem
            # Skip backup and report files
            if field_file.name.endswith((".backup", ".bk")) or "duplicates_report" in field_file.name:
                continue
            try:
                with field_file.open("r", encoding="utf-8") as f:
                    field_data = yaml.safe_load(f)
                    if field_data:
                        correct_matches[field_name] = field_data
            except Exception as e:
                print(f"Warning: Error loading {field_file}: {e}")
        
        return correct_matches

    def extract_brush_entries(
        self, correct_matches: Dict[str, Any]
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Extract all brush entries from correct_matches directory.

        Returns:
            List of tuples: (entry_type, brush_string, entry_data)
        """
        brush_entries = []

        # Extract from brush section (simple brushes)
        brush_section = correct_matches.get("brush", {})
        for brand, brand_data in brush_section.items():
            for model, patterns in brand_data.items():
                for pattern in patterns:
                    if isinstance(pattern, dict):
                        # Dictionary with handle_match flag
                        brush_string = list(pattern.keys())[0]
                        entry_data = pattern[brush_string]
                    else:
                        # Simple string pattern
                        brush_string = pattern
                        entry_data = {}

                    brush_entries.append(("brush", brush_string, entry_data))

        # Extract from split_brush section (composite brushes)
        split_brush_section = correct_matches.get("split_brush", {})
        for brush_string, split_data in split_brush_section.items():
            brush_entries.append(("split_brush", brush_string, split_data))

        # Extract from handle_knot_section (composite brushes)
        handle_knot_section = correct_matches.get("handle_knot_section", {})
        for brush_string, handle_knot_data in handle_knot_section.items():
            brush_entries.append(("handle_knot_section", brush_string, handle_knot_data))

        return brush_entries

    def validate_brush_entry(
        self, entry_type: str, brush_string: str, entry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a single brush entry and extract user intent.

        Args:
            entry_type: Type of entry ("brush", "split_brush", "handle_knot_section")
            brush_string: The brush string to validate
            entry_data: The entry data from correct_matches directory

        Returns:
            Dictionary with validation results
        """
        try:
            # Run through brush matcher
            result = self.brush_matcher.match(brush_string)

            if result is None or result.matched is None:
                return {
                    "status": "failed",
                    "error": "No match found",
                    "brush_string": brush_string,
                    "entry_type": entry_type,
                    "entry_data": entry_data,
                }

            # Check if user_intent is present
            user_intent = result.matched.get("user_intent")
            if user_intent is None:
                return {
                    "status": "failed",
                    "error": "No user_intent detected",
                    "brush_string": brush_string,
                    "entry_type": entry_type,
                    "entry_data": entry_data,
                    "match_result": result.matched,
                }

            return {
                "status": "success",
                "brush_string": brush_string,
                "entry_type": entry_type,
                "entry_data": entry_data,
                "user_intent": user_intent,
                "match_result": result.matched,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "brush_string": brush_string,
                "entry_type": entry_type,
                "entry_data": entry_data,
            }

    def enhance_correct_matches(
        self, correct_matches: Dict[str, Any], validation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhance correct_matches directory with user intent data for successful validations.

        Only composite brushes (split_brush, handle_knot_section) should have user_intent.
        Simple brushes (brush section) should not have user_intent.

        Args:
            correct_matches: Original correct_matches directory data
            validation_results: Results from validation

        Returns:
            Enhanced correct_matches directory data
        """
        enhanced_matches = correct_matches.copy()

        # Track which entries were enhanced
        enhanced_entries = []

        for result in validation_results:
            if result["status"] == "success":
                brush_string = result["brush_string"]
                entry_type = result["entry_type"]
                user_intent = result["user_intent"]

                # Only enhance composite brushes with user_intent
                if entry_type in ["split_brush", "handle_knot_section"]:
                    if entry_type == "split_brush":
                        # Add user_intent to split_brush entry
                        if "user_intent" not in enhanced_matches["split_brush"][brush_string]:
                            enhanced_matches["split_brush"][brush_string][
                                "user_intent"
                            ] = user_intent
                            enhanced_entries.append(f"{entry_type}: {brush_string}")

                    elif entry_type == "handle_knot_section":
                        # Add user_intent to handle_knot_section entry
                        if (
                            "user_intent"
                            not in enhanced_matches["handle_knot_section"][brush_string]
                        ):
                            enhanced_matches["handle_knot_section"][brush_string][
                                "user_intent"
                            ] = user_intent
                            enhanced_entries.append(f"{entry_type}: {brush_string}")

                # For simple brushes (brush section), remove any existing user_intent
                elif entry_type == "brush":
                    # Find and remove user_intent from brush entries
                    for brand, brand_data in enhanced_matches["brush"].items():
                        for model, patterns in brand_data.items():
                            for i, pattern in enumerate(patterns):
                                if isinstance(pattern, dict):
                                    pattern_string = list(pattern.keys())[0]
                                    if pattern_string == brush_string:
                                        # Remove user_intent if present
                                        if "user_intent" in pattern[pattern_string]:
                                            del pattern[pattern_string]["user_intent"]
                                            enhanced_entries.append(
                                                f"{entry_type}: {brush_string} (removed user_intent)"
                                            )
                                        break
                                else:
                                    if pattern == brush_string:
                                        # Convert string to dictionary without user_intent
                                        patterns[i] = {pattern_string: {}}
                                        enhanced_entries.append(
                                            f"{entry_type}: {brush_string} (removed user_intent)"
                                        )
                                        break

        return enhanced_matches, enhanced_entries

    def generate_validation_report(
        self, validation_results: List[Dict[str, Any]], enhanced_entries: List[str]
    ) -> str:
        """
        Generate a comprehensive validation report.

        Args:
            validation_results: Results from validation
            enhanced_entries: List of entries that were enhanced

        Returns:
            Formatted validation report
        """
        total_entries = len(validation_results)
        successful = len([r for r in validation_results if r["status"] == "success"])
        failed = len([r for r in validation_results if r["status"] == "failed"])
        errors = len([r for r in validation_results if r["status"] == "error"])
        enhanced = len(enhanced_entries)

        report = f"""
# Correct Matches User Intent Validation Report

## Summary
- Total entries processed: {total_entries}
- Successful validations: {successful} ({successful / total_entries * 100:.1f}%)
- Failed validations: {failed} ({failed / total_entries * 100:.1f}%)
- Errors: {errors} ({errors / total_entries * 100:.1f}%)
- Entries enhanced: {enhanced}

## Successful Validations ({successful})
"""

        for result in validation_results:
            if result["status"] == "success":
                report += f"- {result['entry_type']}: `{result['brush_string']}` → `{result['user_intent']}`\n"

        if failed > 0:
            report += f"\n## Failed Validations ({failed})\n"
            report += "These entries need manual validation:\n\n"

            for result in validation_results:
                if result["status"] == "failed":
                    report += f"### {result['entry_type']}: `{result['brush_string']}`\n"
                    report += f"- Error: {result['error']}\n"
                    if "match_result" in result:
                        report += (
                            f"- Match result: {json.dumps(result['match_result'], indent=2)}\n"
                        )
                    report += "\n"

        if errors > 0:
            report += f"\n## Errors ({errors})\n"
            report += "These entries caused exceptions:\n\n"

            for result in validation_results:
                if result["status"] == "error":
                    report += f"### {result['entry_type']}: `{result['brush_string']}`\n"
                    report += f"- Error: {result['error']}\n\n"

        if enhanced > 0:
            report += f"\n## Enhanced Entries ({enhanced})\n"
            report += "These entries were successfully enhanced with user_intent:\n\n"

            for entry in enhanced_entries:
                report += f"- {entry}\n"

        return report

    def save_enhanced_correct_matches(
        self, enhanced_matches: Dict[str, Any], backup: bool = True
    ) -> None:
        """
        Save enhanced correct_matches directory files.

        Args:
            enhanced_matches: Enhanced correct_matches directory data
            backup: Whether to create backups of the original files
        """
        import yaml
        import shutil

        # Save each field to its own file
        for field_name, field_data in enhanced_matches.items():
            field_file = self.correct_matches_path / f"{field_name}.yaml"
            
            if backup and field_file.exists():
                # Create backup
                backup_path = field_file.with_suffix(".yaml.backup")
                shutil.copy2(field_file, backup_path)
                print(f"Created backup: {backup_path}")

            # Save enhanced file with proper unicode handling
            with field_file.open("w", encoding="utf-8") as f:
                yaml.dump(
                    field_data,
                    f,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=False,
                    allow_unicode=True,
                )

        print(f"Saved enhanced correct_matches directory: {self.correct_matches_path}")

    def run_validation(self, dry_run: bool = False) -> None:
        """
        Run the complete validation and enhancement process.

        Args:
            dry_run: If True, don't save changes, just generate report
        """
        print("Loading correct_matches directory...")
        correct_matches = self.load_correct_matches()

        print("Extracting brush entries...")
        brush_entries = self.extract_brush_entries(correct_matches)
        print(f"Found {len(brush_entries)} brush entries to validate")

        print("Validating entries...")
        validation_results = []
        for i, (entry_type, brush_string, entry_data) in enumerate(brush_entries, 1):
            print(f"Validating {i}/{len(brush_entries)}: {entry_type} - {brush_string}")
            result = self.validate_brush_entry(entry_type, brush_string, entry_data)
            validation_results.append(result)

        print("Enhancing correct_matches directory...")
        enhanced_matches, enhanced_entries = self.enhance_correct_matches(
            correct_matches, validation_results
        )

        print("Generating validation report...")
        report = self.generate_validation_report(validation_results, enhanced_entries)

        # Save report
        report_path = Path("validation_report_user_intent.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Saved validation report: {report_path}")

        # Print summary
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        print(report.split("## Summary")[1].split("## Successful")[0].strip())
        print("=" * 50)

        if not dry_run:
            print("Saving enhanced correct_matches directory...")
            self.save_enhanced_correct_matches(enhanced_matches)
        else:
            print("DRY RUN: No changes saved")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate and enhance correct_matches directory with user intent"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't save changes, just generate report"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Don't create backup of original file"
    )

    args = parser.parse_args()

    try:
        validator = CorrectMatchesValidator()
        validator.run_validation(dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
