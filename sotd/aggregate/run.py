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


def run(args) -> bool:
    """Run the aggregate phase for the specified date range."""
    if args.annual:
        # Handle annual aggregation (annual handles missing files gracefully)
        if args.year:
            process_annual(
                year=args.year, data_dir=args.out_dir, debug=args.debug, force=args.force
            )
            return False  # Annual aggregation handles missing files gracefully
        elif args.range:
            # Parse year range for annual mode
            start_year, end_year = args.range.split(":")
            years = [str(year) for year in range(int(start_year), int(end_year) + 1)]
            process_annual_range(
                years=years, data_dir=args.out_dir, debug=args.debug, force=args.force
            )
            return False  # Annual aggregation handles missing files gracefully
        else:
            # No year or range specified for annual mode - this should be caught by argparse
            # but handle gracefully
            return True  # Error case
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
            has_errors = process_months_parallel(
                months=months,
                data_dir=args.out_dir,
                debug=args.debug,
                force=args.force,
                max_workers=max_workers,
            )
        else:
            # Use sequential processing
            has_errors = process_months(
                months=months, data_dir=args.out_dir, debug=args.debug, force=args.force
            )

        return has_errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point for the aggregate phase."""
    try:
        parser = get_parser()
        args = parser.parse_args(argv)
        has_errors = run(args)
        return 1 if has_errors else 0
    except KeyboardInterrupt:
        print("\n[INFO] Aggregate phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        print(f"[ERROR] Aggregate phase failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
