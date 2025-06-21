import argparse

from ..cli_utils.base_parser import BaseCLIParser
from .annual_engine import process_annual, process_annual_range
from .engine import process_months

__all__ = [
    "get_parser",
    "run",
    "main",
    "process_months",
    "process_annual",
    "process_annual_range",
]


class AggregateCLIParser(BaseCLIParser):
    """Custom CLI parser for aggregate phase with annual aggregation support."""

    def __init__(self, description: str, **kwargs):
        super().__init__(description=description, **kwargs)
        self._add_annual_argument()

    def _add_annual_argument(self) -> None:
        """Add annual aggregation argument."""
        self.add_argument(
            "--annual",
            action="store_true",
            help="Generate annual aggregated data instead of monthly data",
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
        # We need to call the parent's static method, but we can't use super() in a static method
        # So we'll import and call the base validation directly
        import re

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
        """Validate parsed arguments with annual aggregation rules."""
        # First run base validation
        args = super().validate_args(args)

        # Annual aggregation validation
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


def get_parser() -> argparse.ArgumentParser:
    """Get the argument parser for the aggregate phase."""
    return AggregateCLIParser(
        description="Aggregate enriched SOTD data to generate statistical summaries.",
        require_date_args=True,
    )


def run(args: argparse.Namespace) -> None:
    """Run the aggregate phase with the given arguments."""
    from .run import run as _run

    _run(args)


def main():
    """Main CLI entry point for the aggregate phase."""
    parser = get_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
