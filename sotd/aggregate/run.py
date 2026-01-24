#!/usr/bin/env python3
"""Main entry point for the aggregate phase of the SOTD pipeline."""

from pathlib import Path
from typing import Optional, Sequence

from tqdm import tqdm

from ..cli_utils.date_span import month_span
from .annual_engine import process_annual, process_annual_range, process_annual_range_parallel
from .annual_loader import load_annual_data
from .cli import get_parser
from .engine import process_months, process_months_parallel

__all__ = [
    "run",
    "main",
    "process_annual",
    "process_annual_range",
    "process_annual_range_parallel",
]


def run(args) -> bool:
    """Run the aggregate phase for the specified date range."""
    if args.annual:
        # Handle annual aggregation (annual handles missing files gracefully)
        if args.year:
            # Single year - use sequential processing
            process_annual(
                year=args.year, data_dir=args.out_dir, debug=args.debug, force=args.force
            )
            return False  # Annual aggregation handles missing files gracefully
        elif args.range:
            # Parse year range for annual mode
            start_year, end_year = args.range.split(":")
            years = [str(year) for year in range(int(start_year), int(end_year) + 1)]

            # Check if we should use parallel processing
            use_parallel = (
                hasattr(args, "parallel") and args.parallel or (len(years) > 1 and not args.debug)
            )

            if use_parallel and len(years) > 1:
                # Use parallel processing
                max_workers = getattr(args, "max_workers", 8)
                has_errors = process_annual_range_parallel(
                    years=years,
                    data_dir=args.out_dir,
                    debug=args.debug,
                    force=args.force,
                    max_workers=max_workers,
                )
                return has_errors
            else:
                # Use sequential processing
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

        # If --year or --range is specified (not --month), we're doing annual aggregation
        # In this case, monthly aggregation errors are non-fatal - we'll aggregate whatever months exist
        is_annual_mode = (args.year or args.range) and not args.month

        if use_parallel and len(months) > 1:
            # Use parallel processing
            max_workers = getattr(args, "max_workers", 8)
            has_errors = process_months_parallel(
                months=months,
                data_dir=args.out_dir,
                debug=args.debug,
                force=args.force,
                max_workers=max_workers,
                annual_mode=is_annual_mode,
            )
        else:
            # Use sequential processing
            has_errors = process_months(
                months=months,
                data_dir=args.out_dir,
                debug=args.debug,
                force=args.force,
                annual_mode=is_annual_mode,
            )

        # After monthly aggregation, check if we should create annual files
        # This happens when --year or --range is specified (not --month)
        if is_annual_mode:
            _create_annual_files(months, args.out_dir, args.debug, args.force)
            # In annual mode, monthly aggregation errors are expected if enriched data is missing
            # The annual aggregation will work with whatever monthly aggregated files exist
            # So we don't treat monthly errors as fatal failures
            return False

        return has_errors


def _create_annual_files(
    months: Sequence[str], data_dir: Path, debug: bool = False, force: bool = False
) -> None:
    """
    Create annual aggregation files for years with available monthly data.

    This function checks all years that appear in the months list, and for each year
    where at least one month exists in the aggregated directory, it creates the annual file.
    The annual aggregation will include whatever months are available, even if some are missing.

    Args:
        months: List of months that were just aggregated (YYYY-MM format)
        data_dir: Data directory containing aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing annual files
    """
    from collections import defaultdict

    # Group months by year and find all unique years
    years = set(month.split("-")[0] for month in months)

    # Check each year to see if any months are present
    monthly_data_dir = data_dir / "aggregated"

    # Collect years that need annual files created
    years_to_process = []
    for year in sorted(years):
        # Check if at least one month exists in the aggregated directory
        months_present = []
        for month_num in range(1, 13):
            month_str = f"{year}-{month_num:02d}"
            month_file = monthly_data_dir / f"{month_str}.json"
            if month_file.exists():
                months_present.append(month_str)

        # If at least one month is present, add to processing list
        if months_present:
            # Check if annual file already exists and force is False
            annual_file = monthly_data_dir / "annual" / f"{year}.json"
            if annual_file.exists() and not force:
                if debug:
                    print(
                        f"[DEBUG] Annual file for {year} already exists, skipping (use --force to regenerate)"
                    )
                continue
            years_to_process.append(year)
            if debug:
                missing_count = 12 - len(months_present)
                if missing_count > 0:
                    print(
                        f"[DEBUG] Found {len(months_present)} months for {year} ({missing_count} missing), will create annual aggregation"
                    )
                else:
                    print(
                        f"[DEBUG] All 12 months present for {year}, creating annual aggregation file"
                    )
        else:
            if debug:
                print(
                    f"[DEBUG] No months found for {year}, skipping annual file creation"
                )

    # Process years with progress bar
    if years_to_process:
        print(f"Creating annual aggregation files for {len(years_to_process)} year(s)...")
        for year in tqdm(years_to_process, desc="Annual aggregation", unit="year"):
            try:
                # Create the annual file (will aggregate whatever months are available)
                try:
                    process_annual(year=year, data_dir=data_dir, debug=debug, force=force)
                    if debug:
                        print(f"[DEBUG] Created annual aggregation file for {year}")
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] Could not create annual file for {year}: {e}")
                    # Continue with other years even if one fails
                    continue
            except Exception as e:
                if debug:
                    print(f"[DEBUG] Error checking/creating annual file for {year}: {e}")
                # Continue with other years even if one fails
                continue


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
