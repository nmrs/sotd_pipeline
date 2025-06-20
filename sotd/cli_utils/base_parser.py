"""
Base CLI parser for SOTD pipeline phases.

This module provides a standardized base class for CLI argument parsing
across all pipeline phases to eliminate code duplication and ensure consistency.
"""

import argparse
import re
from pathlib import Path
from typing import Optional


def validate_month(value: str) -> str:
    """Validate month format (YYYY-MM) and ensure month is 01-12."""
    if not re.match(r"^\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(f"Invalid month format: {value} (expected YYYY-MM)")
    year, month = value.split("-")
    if not (1 <= int(month) <= 12):
        raise argparse.ArgumentTypeError(f"Invalid month value: {value} (month must be 01-12)")
    return value


def validate_year(value: str) -> str:
    """Validate year format (YYYY)."""
    if not re.match(r"^\d{4}$", value):
        raise argparse.ArgumentTypeError(f"Invalid year format: {value} (expected YYYY)")
    return value


def validate_range(value: str) -> str:
    """Validate range format (YYYY-MM:YYYY-MM) and ensure months are 01-12."""
    if not re.match(r"^\d{4}-\d{2}:\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(
            f"Invalid range format: {value} (expected YYYY-MM:YYYY-MM)"
        )
    start, end = value.split(":")
    for v in (start, end):
        year, month = v.split("-")
        if not (1 <= int(month) <= 12):
            raise argparse.ArgumentTypeError(
                f"Invalid month value in range: {v} (month must be 01-12)"
            )
    return value


class BaseCLIParser:
    """
    Base class for CLI argument parsing in SOTD pipeline phases.

    Provides common argument patterns and validation logic to eliminate
    code duplication across phase CLIs.
    """

    def __init__(self, description: str):
        """
        Initialize the base CLI parser.

        Args:
            description: Description for the argument parser
        """
        self.parser = argparse.ArgumentParser(description=description)
        self._setup_common_arguments()

    def _setup_common_arguments(self) -> None:
        """Setup common arguments used across all pipeline phases."""
        # Date range arguments (mutually exclusive group)
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--month", type=validate_month, help="Process specific month (YYYY-MM format)"
        )
        group.add_argument(
            "--year", type=validate_year, help="Process all months in year (YYYY format)"
        )
        group.add_argument(
            "--range", type=validate_range, help="Process date range (YYYY-MM:YYYY-MM format)"
        )

        # Optional start/end for range processing
        self.parser.add_argument(
            "--start", type=validate_month, help="Start month for range (YYYY-MM format)"
        )
        self.parser.add_argument(
            "--end", type=validate_month, help="End month for range (YYYY-MM format)"
        )

        # Common options
        self.parser.add_argument(
            "--out-dir", type=Path, default=Path("data"), help="Output directory (default: data)"
        )
        self.parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        self.parser.add_argument(
            "--force", action="store_true", help="Force overwrite existing files"
        )

    def add_argument(self, *args, **kwargs) -> None:
        """Add a custom argument to the parser."""
        self.parser.add_argument(*args, **kwargs)

    def add_mutually_exclusive_group(self, **kwargs):
        """Add a mutually exclusive argument group."""
        return self.parser.add_mutually_exclusive_group(**kwargs)

    def parse_args(self, argv: Optional[list[str]] = None):
        """Parse command line arguments."""
        return self.parser.parse_args(argv)

    def print_help(self) -> None:
        """Print help message."""
        self.parser.print_help()

    def format_help(self) -> str:
        """Get formatted help message."""
        return self.parser.format_help()
