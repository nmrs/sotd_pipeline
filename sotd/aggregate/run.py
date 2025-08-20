#!/usr/bin/env python3
"""Main entry point for the aggregate phase of the SOTD pipeline."""

from typing import Optional, Sequence

from ..cli_utils.date_span import month_span
from .annual_engine import process_annual, process_annual_range
from .cli import get_parser
from .engine import process_months, process_months_parallel

__all__ = [
    "run",
    "main",
    "process_annual",
    "process_annual_range",
]


def run(args) -> None:
    """Run the aggregate phase for the specified date range."""
    if args.annual:
        # Handle annual aggregation
        if args.year:
            process_annual(
                year=args.year, data_dir=args.out_dir, debug=args.debug, force=args.force
            )
        elif args.range:
            # Parse year range for annual mode
            start_year, end_year = args.range.split(":")
            years = [str(year) for year in range(int(start_year), int(end_year) + 1)]
            process_annual_range(
                years=years, data_dir=args.out_dir, debug=args.debug, force=args.force
            )
    else:
        # Handle monthly aggregation with parallel processing support
        # Get months to process
        month_tuples = month_span(args)
        months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]

        # Check if we should use parallel processing
        use_parallel = (
            hasattr(args, "parallel") and args.parallel or (len(months) > 1 and not args.debug)
        )

        if use_parallel and len(months) > 1:
            # Use parallel processing
            max_workers = getattr(args, "max_workers", 8)
            process_months_parallel(
                months=months,
                data_dir=args.out_dir,
                debug=args.debug,
                force=args.force,
                max_workers=max_workers,
            )
        else:
            # Use sequential processing
            process_months(months=months, data_dir=args.out_dir, debug=args.debug, force=args.force)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point for the aggregate phase."""
    try:
        parser = get_parser()
        args = parser.parse_args(argv)
        run(args)
        return 0  # Success
    except KeyboardInterrupt:
        print("\n[INFO] Aggregate phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        print(f"[ERROR] Aggregate phase failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
