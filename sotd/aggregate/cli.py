#!/usr/bin/env python3
"""CLI argument parsing and validation for the aggregate phase."""

import argparse
import datetime
from typing import Sequence


def parse_aggregate_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and validate CLI arguments for the aggregate phase."""
    parser = argparse.ArgumentParser(
        description="Aggregate enriched SOTD data into statistical summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CLI matrix
──────────
(no flags)                 → current month
--month YYYY-MM            → that single month
--year  YYYY               → Jan..Dec of that year
--start YYYY-MM            → that month (single) unless --end also given
--end   YYYY-MM            → that month (single) unless --start also given
--start A --end B          → inclusive span A…B
--range A:B                → shorthand for above (either side optional)
(conflicting combos)       → error
""",
    )

    # Date range arguments
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--month", help="Process specific month (YYYY-MM format)")
    g.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    g.add_argument("--range", help="Month range (YYYY-MM:YYYY-MM format)")
    parser.add_argument("--start", help="Start month for range (YYYY-MM format)")
    parser.add_argument("--end", help="End month for range (YYYY-MM format)")

    # Output and control arguments
    parser.add_argument("--out-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files")

    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["aggregate", "benchmark"],
        default="aggregate",
        help="Operation mode (default: aggregate)",
    )

    # Specialized aggregation control arguments (only for aggregate mode)
    parser.add_argument(
        "--disable-specialized",
        action="store_true",
        help="Disable specialized aggregations (use only core aggregations)",
    )
    parser.add_argument(
        "--disable-cross-product",
        action="store_true",
        help="Disable cross-product analysis",
    )

    # Benchmark-specific arguments
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save benchmark results to file (only for benchmark mode)",
    )

    args = parser.parse_args(argv)

    # Validate date arguments
    date_args = [args.month, args.year, args.start, args.end, args.range]
    if not any(date_args):
        # Default to current month
        now = datetime.datetime.now()
        args.month = f"{now.year:04d}-{now.month:02d}"
    elif sum(1 for arg in date_args if arg is not None) > 1:
        print("[ERROR] Only one date argument allowed")
        exit(1)

    return args
