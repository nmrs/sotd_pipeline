"""
Aggregate enriched SOTD data into statistical summaries.

CLI matrix
──────────
(no flags)                 → current month
--month YYYY-MM            → that single month
--year  YYYY               → Jan..Dec of that year
--start YYYY-MM            → that month (single) unless --end also given
--end   YYYY-MM            → that month (single) unless --start also given
--start A --end B          → inclusive span A…B
--range A:B                → shorthand for above (either side optional)
(conflicting combos)       → error
"""

import argparse
from pathlib import Path
from typing import Sequence
import json

from tqdm import tqdm

from sotd.aggregate.engine import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
    aggregate_users,
    calculate_basic_metrics,
    filter_matched_records,
)
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.save import get_aggregated_file_path, save_aggregated_data
from sotd.cli_utils.date_span import month_span


def process_month(year: int, month: int, args: argparse.Namespace) -> dict:
    """Process a single month of enriched data."""
    # Validate input parameters
    if not isinstance(year, int) or year < 2000 or year > 2100:
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Invalid year: {year} (must be between 2000-2100)",
        }

    if not isinstance(month, int) or month < 1 or month > 12:
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Invalid month: {month} (must be between 1-12)",
        }

    # Get file paths
    base_dir = Path(args.out_dir)
    enriched_path = get_enriched_file_path(base_dir, year, month)
    aggregated_path = get_aggregated_file_path(base_dir, year, month)

    if not enriched_path.exists():
        if args.debug:
            print(f"[DEBUG] Skipping missing enriched file: {enriched_path}")
        return {
            "year": year,
            "month": month,
            "status": "skipped",
            "reason": "missing_enriched_file",
        }

    try:
        # Load enriched data with enhanced validation
        metadata, data = load_enriched_data(enriched_path, debug=args.debug)

        # Validate that we have data to process
        if not data:
            if args.debug:
                print(f"[DEBUG] No data to process for {year:04d}-{month:02d}")
            return {
                "year": year,
                "month": month,
                "status": "skipped",
                "reason": "no_data",
            }

        # Filter for matched records
        matched_records = filter_matched_records(data, debug=args.debug)

        # Calculate basic metrics
        basic_metrics = calculate_basic_metrics(matched_records, debug=args.debug)

        # Perform aggregations with error handling for each
        try:
            razors = aggregate_razors(matched_records, debug=args.debug)
        except Exception as e:
            if args.debug:
                print(f"[DEBUG] Error aggregating razors: {e}")
            razors = []

        try:
            blades = aggregate_blades(matched_records, debug=args.debug)
        except Exception as e:
            if args.debug:
                print(f"[DEBUG] Error aggregating blades: {e}")
            blades = []

        try:
            soaps = aggregate_soaps(matched_records, debug=args.debug)
        except Exception as e:
            if args.debug:
                print(f"[DEBUG] Error aggregating soaps: {e}")
            soaps = []

        try:
            brushes = aggregate_brushes(matched_records, debug=args.debug)
        except Exception as e:
            if args.debug:
                print(f"[DEBUG] Error aggregating brushes: {e}")
            brushes = []

        try:
            users = aggregate_users(matched_records, debug=args.debug)
        except Exception as e:
            if args.debug:
                print(f"[DEBUG] Error aggregating users: {e}")
            users = []

        # Prepare results
        results = {
            "year": year,
            "month": month,
            "status": "success",
            "basic_metrics": basic_metrics,
            "aggregations": {
                "razors": razors,
                "blades": blades,
                "soaps": soaps,
                "brushes": brushes,
                "users": users,
            },
            "summary": {
                "total_records": len(data),
                "matched_records": len(matched_records),
                "razor_count": len(razors),
                "blade_count": len(blades),
                "soap_count": len(soaps),
                "brush_count": len(brushes),
                "user_count": len(users),
            },
        }

        # Save aggregated data
        save_aggregated_data(results, aggregated_path, force=args.force, debug=args.debug)

        if args.debug:
            print(f"[DEBUG] Processed {year:04d}-{month:02d}: {results['summary']}")

        return results

    except FileNotFoundError as e:
        if args.debug:
            print(f"[DEBUG] File not found error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"File not found: {e}",
        }
    except json.JSONDecodeError as e:
        if args.debug:
            print(f"[DEBUG] JSON decode error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"JSON decode error: {e}",
        }
    except ValueError as e:
        if args.debug:
            print(f"[DEBUG] Data validation error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Data validation error: {e}",
        }
    except OSError as e:
        if args.debug:
            print(f"[DEBUG] File system error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"File system error: {e}",
        }
    except Exception as e:
        if args.debug:
            print(f"[DEBUG] Unexpected error processing {year:04d}-{month:02d}: {e}")
        return {
            "year": year,
            "month": month,
            "status": "error",
            "error": f"Unexpected error: {e}",
        }


def run_aggregate(args: argparse.Namespace) -> None:
    """Main aggregation logic."""
    # Validate output directory
    out_dir = Path(args.out_dir)
    if not out_dir.exists():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            if args.debug:
                print(f"[DEBUG] Created output directory: {out_dir}")
        except OSError as e:
            print(f"[ERROR] Failed to create output directory {out_dir}: {e}")
            return

    months = list(month_span(args))

    if not months:
        print("[ERROR] No months to process")
        return

    if args.debug:
        print(f"[DEBUG] Processing {len(months)} month(s)")
        print(f"[DEBUG] Output directory: {args.out_dir}")
        print(f"[DEBUG] Force overwrite: {args.force}")

    results = []

    # Process each month with progress bar
    for year, month in tqdm(months, desc="Aggregating", unit="month"):
        result = process_month(year, month, args)
        results.append(result)

    # Print summary
    successful = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    print("[INFO] Aggregate phase complete:")
    print(f"  Successful: {len(successful)} month(s)")
    print(f"  Skipped: {len(skipped)} month(s)")
    print(f"  Errors: {len(errors)} month(s)")

    if successful:
        total_shaves = sum(r["basic_metrics"]["total_shaves"] for r in successful)
        total_users = sum(r["basic_metrics"]["unique_shavers"] for r in successful)
        print(f"  Total shaves: {total_shaves}")
        print(f"  Total unique users: {total_users}")

    if errors and args.debug:
        print("\n[DEBUG] Errors:")
        for error in errors:
            print(f"  {error['year']:04d}-{error['month']:02d}: {error['error']}")

    if errors and not args.debug:
        print(f"\n[INFO] {len(errors)} month(s) had errors. Use --debug for details.")


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point for aggregate phase."""
    p = argparse.ArgumentParser(
        description="Aggregate enriched SOTD data into statistical summaries"
    )

    # Date range arguments (same pattern as other phases)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--month", type=str, help="e.g., 2025-04")
    g.add_argument("--year", type=int, help="e.g., 2025 (runs all months in that year)")
    g.add_argument("--range", type=str, help="Format: YYYY-MM:YYYY-MM (inclusive)")
    p.add_argument("--start", type=str, help="Optional: overrides start date (YYYY-MM)")
    p.add_argument("--end", type=str, help="Optional: overrides end date (YYYY-MM)")

    # Standard pipeline arguments
    p.add_argument("--out-dir", default="data", help="Output directory for aggregated data")
    p.add_argument("--debug", action="store_true", help="Enable debug logging")
    p.add_argument("--force", action="store_true", help="Force overwrite existing files")

    args = p.parse_args(argv)

    # Validate arguments
    if not args.month and not args.year and not args.range and not args.start and not args.end:
        # No date specified - use current month
        from datetime import datetime

        now = datetime.now()
        args.month = f"{now.year:04d}-{now.month:02d}"

    # Validate output directory
    out_dir = Path(args.out_dir)
    if not out_dir.exists():
        if args.debug:
            print(f"[DEBUG] Creating output directory: {out_dir}")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[ERROR] Failed to create output directory {out_dir}: {e}")
            return

    # Run aggregation
    run_aggregate(args)


if __name__ == "__main__":
    main()
