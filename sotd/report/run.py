#!/usr/bin/env python3
"""
Generate statistical analysis reports from aggregated SOTD data.

CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--type hardware|software   → report type (default: hardware)
--out-dir DIR              → output directory (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
"""

import argparse
import datetime
from typing import Sequence


def parse_report_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and validate CLI arguments for the report phase."""
    parser = argparse.ArgumentParser(
        description="Generate statistical analysis reports from aggregated SOTD data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--type hardware|software   → report type (default: hardware)
--out-dir DIR              → output directory (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
""",
    )

    # Date arguments
    parser.add_argument("--month", help="Process specific month (YYYY-MM format)")

    # Report type
    parser.add_argument(
        "--type",
        choices=["hardware", "software"],
        default="hardware",
        help="Report type (default: hardware)",
    )

    # Output and control arguments
    parser.add_argument("--out-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files")

    args = parser.parse_args(argv)

    # Validate date arguments
    if not args.month:
        # Default to current month
        now = datetime.datetime.now()
        args.month = f"{now.year:04d}-{now.month:02d}"

    return args


def run_report(args: argparse.Namespace) -> None:
    """Main report generation logic."""
    if args.debug:
        print("[DEBUG] Report phase started")
        print(f"[DEBUG] Month: {args.month}")
        print(f"[DEBUG] Report type: {args.type}")
        print(f"[DEBUG] Output directory: {args.out_dir}")
        print(f"[DEBUG] Force overwrite: {args.force}")

    # TODO: Implement report generation logic
    print(f"[INFO] Generating {args.type} report for {args.month}")
    print("[INFO] Report generation not yet implemented")


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the report phase."""
    try:
        args = parse_report_args(argv)
        run_report(args)
    except KeyboardInterrupt:
        print("\n[INFO] Report generation interrupted by user")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        # Note: args might not be defined if parse_report_args fails
        # We'll handle this in the exception handler


if __name__ == "__main__":
    main()
