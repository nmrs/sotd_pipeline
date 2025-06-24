"""
Base CLI parser for SOTD Pipeline phases.

This module provides a standardized base class for CLI argument parsing
to eliminate code duplication across all pipeline phases.
"""

import argparse
import re
from pathlib import Path
from typing import Optional


class BaseCLIParser(argparse.ArgumentParser):
    """
    Base argument parser with common CLI patterns for SOTD Pipeline phases.

    Provides standardized arguments for:
    - Date/time range specification (month, year, range, start/end)
    - Output directory
    - Debug mode
    - Force overwrite
    - Common validation logic
    """

    def __init__(
        self,
        description: str,
        add_date_args: bool = True,
        add_output_args: bool = True,
        add_debug_args: bool = True,
        add_force_args: bool = True,
        require_date_args: bool = True,
        **kwargs,
    ):
        """
        Initialize the base parser with common arguments.

        Args:
            description: Parser description
            add_date_args: Whether to add date/time range arguments
            add_output_args: Whether to add output directory argument
            add_debug_args: Whether to add debug flag
            add_force_args: Whether to add force flag
            require_date_args: Whether date arguments are required (default: True since main run.py
                provides them)
            **kwargs: Additional arguments passed to argparse.ArgumentParser
        """
        super().__init__(description=description, **kwargs)

        self._require_date_args = require_date_args

        if add_date_args:
            self._add_date_arguments()

        if add_output_args:
            self._add_output_arguments()

        if add_debug_args:
            self._add_debug_arguments()

        if add_force_args:
            self._add_force_arguments()

    def _add_date_arguments(self) -> None:
        """Add standardized date/time range arguments."""
        # Mutually exclusive group for date specification (optional when using start/end)
        date_group = self.add_mutually_exclusive_group(required=False)

        date_group.add_argument(
            "--month", type=self._validate_month, help="Process specific month (YYYY-MM)"
        )
        date_group.add_argument(
            "--year", type=self._validate_year, help="Process all months in year (YYYY)"
        )
        date_group.add_argument(
            "--range", type=self._validate_range, help="Process date range (YYYY-MM:YYYY-MM)"
        )

        # Alternative: start/end range specification (both must be provided)
        self.add_argument(
            "--start", type=self._validate_month, help="Start month for range (YYYY-MM)"
        )
        self.add_argument("--end", type=self._validate_month, help="End month for range (YYYY-MM)")

    def _add_output_arguments(self) -> None:
        """Add standardized output directory argument."""
        self.add_argument(
            "--out-dir", type=Path, default=Path("data"), help="Output directory (default: data)"
        )

    def _add_debug_arguments(self) -> None:
        """Add standardized debug flag."""
        self.add_argument("--debug", action="store_true", help="Enable debug logging")

    def _add_force_arguments(self) -> None:
        """Add standardized force flag."""
        self.add_argument("--force", action="store_true", help="Overwrite existing files")

    @staticmethod
    def _validate_month(value: str) -> str:
        """Validate month format (YYYY-MM) and ensure month is 01-12."""
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise argparse.ArgumentTypeError(f"Invalid month format: {value} (expected YYYY-MM)")

        # Validate month value
        year, month = value.split("-")
        if not (1 <= int(month) <= 12):
            raise argparse.ArgumentTypeError(f"Invalid month value: {value} (month must be 01-12)")

        return value

    @staticmethod
    def _validate_year(value: str) -> str:
        """Validate year format (YYYY)."""
        if not re.match(r"^\d{4}$", value):
            raise argparse.ArgumentTypeError(f"Invalid year format: {value} (expected YYYY)")
        return value

    @staticmethod
    def _validate_range(value: str) -> str:
        """Validate range format (YYYY-MM:YYYY-MM) and ensure months are 01-12."""
        if not re.match(r"^\d{4}-\d{2}:\d{4}-\d{2}$", value):
            raise argparse.ArgumentTypeError(
                f"Invalid range format: {value} (expected YYYY-MM:YYYY-MM)"
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

    def add_parallel_processing_group(self) -> argparse._MutuallyExclusiveGroup:
        """
        Add a mutually exclusive group for parallel processing options.

        Returns:
            The argument group for adding parallel processing arguments
        """
        return self.add_mutually_exclusive_group()

    def add_parallel_processing_arguments(
        self, default_max_workers: int = 4, help_max_workers: Optional[str] = None
    ) -> None:
        """
        Add standardized parallel processing arguments.

        Args:
            default_max_workers: Default value for max-workers
            help_max_workers: Custom help text for max-workers
        """
        parallel_group = self.add_parallel_processing_group()
        parallel_group.add_argument(
            "--parallel", action="store_true", help="Force parallel processing"
        )
        parallel_group.add_argument(
            "--sequential", action="store_true", help="Force sequential processing"
        )

        self.add_argument(
            "--max-workers",
            type=int,
            default=default_max_workers,
            help=help_max_workers or f"Maximum parallel workers (default: {default_max_workers})",
        )

    def parse_args(self, args=None, namespace=None):  # type: ignore
        """Parse arguments and validate them."""
        parsed_args = super().parse_args(args, namespace)
        return self.validate_args(parsed_args)

    def validate_args(self, args: argparse.Namespace) -> argparse.Namespace:
        """Validate parsed arguments."""
        # Special case: --list-months and --audit can work without date arguments
        # These are utility operations that don't require date ranges
        has_primary_date = bool(
            getattr(args, "month", None)
            or getattr(args, "year", None)
            or getattr(args, "range", None)
        )
        has_start_end = bool(getattr(args, "start", None) or getattr(args, "end", None))

        if (
            hasattr(args, "list_months")
            and args.list_months
            and not has_primary_date
            and not has_start_end
        ):
            return args
        if hasattr(args, "audit") and args.audit and not has_primary_date and not has_start_end:
            return args

        # Special case: annual mode - don't set default month
        if hasattr(args, "annual") and args.annual:
            return args

        # If no date specification is provided
        if not has_primary_date and not has_start_end:
            if self._require_date_args:
                self.error(
                    "At least one date argument (--month, --year, --range, "
                    "or --start/--end) is required"
                )

            # Individual phases should always receive date arguments from main run.py
            # No default logic needed here
            return args

        # Validate start/end pair
        if (getattr(args, "start", None) is not None) != (getattr(args, "end", None) is not None):
            self.error("Both --start and --end must be provided together")

        return args
