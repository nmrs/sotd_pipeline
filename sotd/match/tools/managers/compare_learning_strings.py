#!/usr/bin/env python3
"""Learning strings comparison tool.

This tool compares top-level keys from learning YAML files (like brush_user_actions)
with all strings in correct_matches.yaml to find learning entries that haven't been
added to the official catalog yet.
"""

import sys
from pathlib import Path

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse  # noqa: E402
from typing import Dict, List, Optional, Set  # noqa: E402

import yaml  # noqa: E402
from rich.console import Console  # noqa: E402


class CompareLearningStrings:
    """Compare learning YAML files with correct_matches.yaml."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the comparator.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self._data_dir = Path("data")
        self.correct_matches = None

    def get_parser(self) -> argparse.ArgumentParser:
        """Get CLI argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Compare learning YAML files with correct_matches.yaml"
        )

        # File selection - use month parameter for convenience
        file_group = parser.add_mutually_exclusive_group()
        file_group.add_argument(
            "--month",
            help="Month to process (YYYY-MM format, e.g., 2025-06)",
        )
        file_group.add_argument(
            "--learning-file",
            help="Path to learning YAML file (e.g., brush_user_actions/2025-06.yaml)",
        )
        parser.add_argument(
            "--correct-matches",
            default="data/correct_matches.yaml",
            help="Path to correct_matches.yaml file",
        )

        # Behavior options
        parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be compared without running comparison",
        )

        return parser

    def _find_latest_learning_file(self) -> Path:
        """Find the latest learning file by filename date.

        Returns:
            Path to the latest learning file

        Raises:
            FileNotFoundError: If no learning files are found
        """
        learning_dir = self._data_dir / "learning" / "brush_user_actions"
        if not learning_dir.exists():
            raise FileNotFoundError(f"Learning directory not found: {learning_dir}")

        # Find all YAML files in the learning directory
        yaml_files = list(learning_dir.glob("*.yaml"))
        if not yaml_files:
            raise FileNotFoundError(f"No YAML files found in {learning_dir}")

        # Sort by filename (which contains the date) to find the latest
        # Files are named like "2025-06.yaml", so string sorting works
        latest_file = max(yaml_files, key=lambda f: f.stem)

        return latest_file

    def run(self, args) -> Dict[str, Set[str]]:
        """
        Run comparison based on CLI arguments.

        Args:
            args: Parsed CLI arguments

        Returns:
            Dictionary with comparison results
        """
        # Determine learning file path
        if args.month:
            # Construct path from month parameter
            learning_file = (
                self._data_dir / "learning" / "brush_user_actions" / f"{args.month}.yaml"
            )
        elif args.learning_file:
            # Use explicit file path
            learning_file = Path(args.learning_file)
        else:
            # Default to latest learning file
            learning_file = self._find_latest_learning_file()
            print(f"Using latest learning file: {learning_file.name}")

        correct_matches_file = Path(args.correct_matches)

        if not learning_file.exists():
            raise FileNotFoundError(f"Learning file not found: {learning_file}")

        if not correct_matches_file.exists():
            raise FileNotFoundError(f"Correct matches file not found: {correct_matches_file}")

        # Load YAML files
        print("Loading YAML files...")
        learning_data = self._load_yaml_file(learning_file)
        correct_matches_data = self._load_yaml_file(correct_matches_file)

        if learning_data is None or correct_matches_data is None:
            raise RuntimeError("Failed to load one or more YAML files")

        # Extract top-level keys from learning file
        print("Extracting top-level keys from learning file...")
        top_level_keys = self._extract_top_level_keys(learning_data)
        print(f"Found {len(top_level_keys)} top-level keys in learning file")

        # Extract all strings from correct_matches.yaml
        print("Extracting all strings from correct_matches.yaml...")
        all_strings_correct_matches = self._extract_all_strings(correct_matches_data)
        print(f"Found {len(all_strings_correct_matches)} unique strings in correct_matches.yaml")

        # Find top-level keys that are not in correct_matches.yaml
        missing_keys = top_level_keys - all_strings_correct_matches
        found_keys = top_level_keys & all_strings_correct_matches

        # Display results
        self._display_results(
            top_level_keys, all_strings_correct_matches, missing_keys, found_keys, args.verbose
        )

        return {
            "top_level_keys": top_level_keys,
            "all_strings_correct_matches": all_strings_correct_matches,
            "missing_keys": missing_keys,
            "found_keys": found_keys,
        }

    def _load_yaml_file(self, file_path: Path) -> Optional[Dict]:
        """Load a YAML file and return its contents.

        Args:
            file_path: Path to YAML file

        Returns:
            Loaded YAML data or None if loading failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def _extract_top_level_keys(self, data: Dict) -> Set[str]:
        """Extract only the top-level keys from the YAML file.

        Args:
            data: Loaded YAML data

        Returns:
            Set of top-level keys (normalized to lowercase)
        """
        if isinstance(data, dict):
            return {key.strip().lower() for key in data.keys() if key and key.strip()}
        return set()

    def _extract_all_strings(self, data: Dict) -> Set[str]:
        """Extract all string values from the YAML file recursively.

        Args:
            data: Loaded YAML data

        Returns:
            Set of all string values (normalized to lowercase)
        """
        strings = set()

        def extract_strings_recursive(obj):
            if isinstance(obj, str):
                cleaned = obj.strip()
                if cleaned:
                    strings.add(cleaned.lower())
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_strings_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings_recursive(item)

        extract_strings_recursive(data)
        return strings

    def _display_results(
        self,
        top_level_keys: Set[str],
        all_strings_correct_matches: Set[str],
        missing_keys: Set[str],
        found_keys: Set[str],
        verbose: bool,
    ) -> None:
        """Display comparison results.

        Args:
            top_level_keys: All top-level keys from learning file
            all_strings_correct_matches: All strings from correct_matches.yaml
            missing_keys: Keys not found in correct_matches.yaml
            found_keys: Keys found in correct_matches.yaml
            verbose: Whether to show verbose output
        """
        print(
            f"\nFound {len(missing_keys)} top-level keys in learning file "
            f"that are NOT present anywhere in correct_matches.yaml:"
        )
        print("=" * 80)

        # Sort and display missing keys
        for key in sorted(missing_keys):
            print(f"  {key}")

        print(f"\nTotal missing top-level keys: {len(missing_keys)}")

        # Show statistics
        print("\nStatistics:")
        print(f"  Top-level keys in learning file: {len(top_level_keys)}")
        print(f"  Strings in correct_matches.yaml: {len(all_strings_correct_matches)}")
        print(f"  Top-level keys found in correct_matches.yaml: {len(found_keys)}")
        print(f"  Top-level keys NOT in correct_matches.yaml: {len(missing_keys)}")

        # Always show the actual keys found and missing for clarity
        if found_keys:
            print("\nTop-level keys found in correct_matches.yaml:")
            print("-" * 50)
            for key in sorted(found_keys):
                print(f"  {key}")

        if missing_keys:
            print("\nTop-level keys NOT found in correct_matches.yaml:")
            print("-" * 50)
            for key in sorted(missing_keys):
                print(f"  {key}")

        # Show all top-level keys from learning file if verbose
        if verbose:
            print("\nAll top-level keys from learning file:")
            print("-" * 50)
            for key in sorted(top_level_keys):
                print(f"  {key}")

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
            results = self.run(parsed_args)
            missing_count = len(results["missing_keys"])

            if missing_count > 0:
                print(f"\n❌ Found {missing_count} learning entries not in correct_matches.yaml")
                return 1
            else:
                print("\n✅ All learning entries are present in correct_matches.yaml")
                return 0

        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _show_dry_run_info(self, args) -> None:
        """Show dry run information.

        Args:
            args: Parsed arguments
        """
        print("Dry run mode - would compare:")

        # Determine which file would be used
        if args.month:
            learning_file = f"data/learning/brush_user_actions/{args.month}.yaml"
        elif args.learning_file:
            learning_file = args.learning_file
        else:
            learning_file = "latest learning file (auto-detected)"

        print(f"  Learning file: {learning_file}")
        print(f"  Correct matches: {args.correct_matches}")
        print(f"  Verbose: {args.verbose}")


def main():
    """Main entry point."""
    comparator = CompareLearningStrings()
    return comparator.main()


if __name__ == "__main__":
    sys.exit(main())
