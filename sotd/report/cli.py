"""
CLI argument parsing for the report phase.

This module provides standardized CLI argument parsing for the report phase
using the BaseCLIParser to eliminate code duplication.
"""

import argparse
import datetime
from pathlib import Path

from sotd.cli_utils.base_parser import BaseCLIParser


class ReportCLIParser(BaseCLIParser):
    """Custom CLI parser for report phase with annual range support."""

    def __init__(self, description: str, **kwargs):
        super().__init__(description=description, **kwargs)
        self._add_annual_argument()
        self._add_report_arguments()

    def _add_annual_argument(self) -> None:
        """Add annual report argument."""
        self.add_argument(
            "--annual",
            action="store_true",
            help="Generate annual reports (requires --year or --range)",
        )

    def _add_report_arguments(self) -> None:
        """Add report-specific arguments."""
        self.add_argument(
            "--type",
            choices=["hardware", "software"],
            default="hardware",
            help="Report type (default: hardware)",
        )

        self.add_argument(
            "--data-root",
            type=Path,
            default=Path("data"),
            help="Root directory for all input data (default: data)",
        )

    def _validate_range_with_annual_support(self, value: str) -> str:
        """Validate range format with support for both monthly and annual formats."""
        # Check if this is an annual range (YYYY:YYYY format)
        if ":" in value and len(value.split(":")) == 2:
            start, end = value.split(":")
            if len(start) == 4 and start.isdigit() and len(end) == 4 and end.isdigit():
                # This is a valid annual range format
                return value

        # Fall back to base validation for monthly ranges
        import re

        if not re.match(r"^\d{4}-\d{2}:\d{4}-\d{2}$", value):
            raise argparse.ArgumentTypeError(
                f"Invalid range format: {value} (expected YYYY-MM:YYYY-MM or YYYY:YYYY for annual)"
            )

        # Validate month values in range
        start, end = value.split(":")
        for v in (start, end):
            year, month = v.split("-")
            if not (1 <= int(month) <= 12):
                raise argparse.ArgumentTypeError(
                    f"Invalid month value in range: {v} (month must be 01-12)"
                )

        return value

    def _add_date_arguments(self) -> None:
        """Override to use custom range validation."""
        # Mutually exclusive group for date specification (optional when using start/end)
        date_group = self.add_mutually_exclusive_group(required=False)

        date_group.add_argument(
            "--month", type=self._validate_month, help="Process specific month (YYYY-MM)"
        )
        date_group.add_argument(
            "--year", type=self._validate_year, help="Process all months in year (YYYY)"
        )
        date_group.add_argument(
            "--range",
            type=self._validate_range_with_annual_support,
            help="Process date range (YYYY-MM:YYYY-MM or YYYY:YYYY for annual)",
        )

        # Alternative: start/end range specification (both must be provided)
        self.add_argument(
            "--start", type=self._validate_month, help="Start month for range (YYYY-MM)"
        )
        self.add_argument("--end", type=self._validate_month, help="End month for range (YYYY-MM)")

    def validate_args(self, args: argparse.Namespace) -> argparse.Namespace:
        """Validate parsed arguments with annual report rules."""
        # First run base validation
        args = super().validate_args(args)

        # Annual report validation
        if args.annual:
            # Annual mode requires year or year range (not month or month range)
            if args.month:
                self.error("--annual cannot be used with --month (use --year instead)")

            if args.start or args.end:
                self.error(
                    "--annual cannot be used with --start/--end (use --year or --range instead)"
                )

            # Annual mode requires either --year or --range
            if not args.year and not args.range:
                self.error("--annual requires either --year or --range argument")

            # For annual mode, range should be in YYYY:YYYY format
            if args.range and ":" in args.range:
                start, end = args.range.split(":")
                if len(start) != 4 or not start.isdigit() or len(end) != 4 or not end.isdigit():
                    self.error("Annual range must be in YYYY:YYYY format")

        return args


def get_parser() -> ReportCLIParser:
    """
    Get the argument parser for the report phase.

    Returns:
        ReportCLIParser: Configured argument parser for report phase
    """
    parser = ReportCLIParser(
        description="Generate statistical analysis reports from aggregated SOTD data",
        epilog="""
CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--annual --year YYYY       → annual report for specific year
--annual --range YYYY:YYYY → annual reports for year range
--type hardware|software   → report type (default: hardware)
--data-root DIR            → root directory for all input data (default: data)
--out-dir DIR              → output directory for report file (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
""",
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
        args: Parsed arguments from ReportCLIParser

    Raises:
        ValueError: If arguments are invalid
    """
    # Handle annual report validation
    if args.annual:
        # Check for conflicts first
        if args.month:
            raise ValueError("Annual reports cannot be combined with monthly")
        if args.year and args.range:
            raise ValueError("Cannot specify both --year and --range")

        # Then check for required arguments
        if not args.year and not args.range:
            raise ValueError("Annual reports require --year or --range")
        return

    # For monthly reports, we only support single month processing
    if args.year or args.range or args.start or args.end:
        raise ValueError(
            "Report phase only supports single month processing. "
            "Use --month YYYY-MM to specify a single month."
        )
