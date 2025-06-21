import argparse

from ..cli_utils.base_parser import BaseCLIParser
from ..cli_utils.date_span import month_span
from .engine import process_months


def get_parser() -> argparse.ArgumentParser:
    """Get the argument parser for the aggregate phase."""
    return BaseCLIParser(
        description="Aggregate enriched SOTD data to generate statistical summaries.",
        require_date_args=True,
    )


def main():
    """Main CLI entry point for the aggregate phase."""
    parser = get_parser()
    args = parser.parse_args()

    # Get months to process
    month_tuples = month_span(args)
    months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]

    # Process the months
    process_months(months, args.out_dir, debug=args.debug)


if __name__ == "__main__":
    main()
