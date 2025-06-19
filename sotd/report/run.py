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
from pathlib import Path
from typing import Sequence

from . import load, process, save


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

    # Parse month to get year and month
    try:
        year_str, month_str = args.month.split("-")
        year = int(year_str)
        month = int(month_str)
    except ValueError:
        raise ValueError(f"Invalid month format: {args.month}. Expected YYYY-MM format.")

    # Convert output directory to Path
    base_dir = Path(args.out_dir)

    # Load aggregated data
    if args.debug:
        print(f"[DEBUG] Loading aggregated data for {args.month}")

    try:
        aggregated_file_path = load.get_aggregated_file_path(base_dir, year, month)
        metadata, data = load.load_aggregated_data(aggregated_file_path, args.debug)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Aggregated data not found for {args.month}. "
            f"Run the aggregate phase first to generate the required data."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to load aggregated data: {e}") from e

    # Generate report content
    if args.debug:
        print(f"[DEBUG] Generating {args.type} report content")

    try:
        report_content = process.generate_report_content(args.type, metadata, data, args.debug)
    except Exception as e:
        raise RuntimeError(f"Failed to generate report content: {e}") from e

    # Save report to file
    if args.debug:
        print("[DEBUG] Saving report to file")

    try:
        output_path = save.generate_and_save_report(
            report_content, base_dir, year, month, args.type, args.force, args.debug
        )
    except FileExistsError as e:
        raise FileExistsError(f"Report file already exists. Use --force to overwrite: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to save report: {e}") from e

    # Success message
    print(f"[INFO] Successfully generated {args.type} report for {args.month}")
    print(f"[INFO] Report saved to: {output_path}")


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
