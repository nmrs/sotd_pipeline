#!/usr/bin/env python3
"""
CLI script for catalog validation that follows DRY principles.

This script provides the same validation logic as the API endpoint,
ensuring consistent results between CLI and API calls.
"""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification
try:
    from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches
except ImportError:
    print(
        "❌ Failed to import ValidateCorrectMatches. "
        "Make sure you're running from the project root."
    )
    sys.exit(1)


def main():
    """Main CLI function for catalog validation."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate catalog entries against correct_matches.yaml using DRY validation logic"
        )
    )
    parser.add_argument(
        "--field",
        choices=["brush", "blade", "razor", "soap", "handle", "knot"],
        help="Field to validate (default: all fields)",
    )
    parser.add_argument(
        "--output-format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human-readable)",
    )
    parser.add_argument(
        "--correct-matches-path",
        type=Path,
        help="Path to correct_matches.yaml (default: data/correct_matches.yaml)",
    )

    args = parser.parse_args()

    try:
        # Initialize validator
        validator = ValidateCorrectMatches(correct_matches_path=args.correct_matches_path)

        # Set the same data directory as the API for consistent validation
        # This ensures we use the same catalog files and validation logic
        project_root = Path(__file__).parent.parent
        validator._data_dir = project_root / "data"

        if args.output_format == "json":
            # JSON output for programmatic use
            if args.field:
                # Use the CLI-specific method that follows DRY principles
                issues = validator.validate_field_cli(args.field)
                result = {
                    "field": args.field,
                    "total_entries": len(issues),
                    "issues": issues,
                    "processing_time": 0.0,
                }
            else:
                # Use the CLI-specific method that follows DRY principles
                issues, _ = validator.run_validation_cli()
                result = {
                    "field": "all",
                    "total_entries": len(issues),
                    "issues": issues,
                    "processing_time": 0.0,
                }

            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            if args.field:
                print(f"🔍 Validating {args.field} field...")
                # Use the CLI-specific method that follows DRY principles
                validator.run_validation_cli(args.field)
            else:
                print("🔍 Validating all fields...")
                # Use the CLI-specific method that follows DRY principles
                validator.run_validation_cli()

    except Exception as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
