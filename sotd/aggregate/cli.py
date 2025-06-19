import argparse
import re
from pathlib import Path

from ..cli_utils.date_span import month_span
from .engine import process_months


def validate_month(value: str) -> str:
    if not re.match(r"^\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(f"Invalid month format: {value} (expected YYYY-MM)")
    return value


def validate_year(value: str) -> str:
    if not re.match(r"^\d{4}$", value):
        raise argparse.ArgumentTypeError(f"Invalid year format: {value} (expected YYYY)")
    return value


def validate_range(value: str) -> str:
    if not re.match(r"^\d{4}-\d{2}:\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(
            f"Invalid range format: {value} (expected YYYY-MM:YYYY-MM)"
        )
    return value


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate enriched SOTD data to generate statistical summaries."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--month", type=validate_month, help="Process specific month (YYYY-MM)")
    group.add_argument("--year", type=validate_year, help="Process all months in year (YYYY)")
    group.add_argument("--range", type=validate_range, help="Process date range (YYYY-MM:YYYY-MM)")
    parser.add_argument("--start", type=validate_month, help="Start month for range (YYYY-MM)")
    parser.add_argument("--end", type=validate_month, help="End month for range (YYYY-MM)")
    parser.add_argument(
        "--out-dir", type=Path, default=Path("data"), help="Output directory (default: data)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Get months to process
    month_tuples = month_span(args)
    months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]

    # Process the months
    process_months(months, args.out_dir, debug=args.debug)


if __name__ == "__main__":
    main()
