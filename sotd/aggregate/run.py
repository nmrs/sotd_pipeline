#!/usr/bin/env python3
"""Main entry point for the aggregate phase of the SOTD pipeline."""

from typing import Optional, Sequence

from ..cli_utils.date_span import month_span
from .cli import get_parser, process_months


def run(args) -> None:
    """Run the aggregate phase for the specified date range."""
    # Get months to process
    month_tuples = month_span(args)
    months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]

    # Process the months
    process_months(months, args.out_dir, debug=args.debug)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Main CLI entry point for the aggregate phase."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
