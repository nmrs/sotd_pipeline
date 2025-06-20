"""
CLI argument parsing for the report phase.

This module provides standardized CLI argument parsing for the report phase
using the BaseCLIParser to eliminate code duplication.
"""

import datetime
from pathlib import Path

from sotd.cli_utils.base_parser import BaseCLIParser


def get_parser() -> BaseCLIParser:
    """
    Get the argument parser for the report phase.

    Returns:
        BaseCLIParser: Configured argument parser for report phase
    """
    parser = BaseCLIParser(
        description="Generate statistical analysis reports from aggregated SOTD data",
        epilog="""
CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--type hardware|software   → report type (default: hardware)
--data-root DIR            → root directory for all input data (default: data)
--out-dir DIR              → output directory for report file (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
""",
    )

    # Add report-specific arguments
    parser.add_argument(
        "--type",
        choices=["hardware", "software"],
        default="hardware",
        help="Report type (default: hardware)",
    )

    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Root directory for all input data (default: data)",
    )

    return parser


def get_default_month() -> str:
    """
    Get the default month (current month) for report generation.

    Returns:
        str: Current month in YYYY-MM format
    """
    now = datetime.datetime.now()
    return f"{now.year:04d}-{now.month:02d}"


def validate_args(args) -> None:
    """
    Validate report-specific arguments.

    Args:
        args: Parsed arguments from BaseCLIParser

    Raises:
        ValueError: If arguments are invalid
    """
    # For report phase, we only support single month processing
    if args.year or args.range or args.start or args.end:
        raise ValueError(
            "Report phase only supports single month processing. "
            "Use --month YYYY-MM to specify a single month."
        )
