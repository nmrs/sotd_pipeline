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
import datetime
import json
import time
from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from sotd.aggregate.engine import (
    aggregate_blade_manufacturers,
    aggregate_blades,
    aggregate_brush_fibers,
    aggregate_brush_handle_makers,
    aggregate_brush_knot_makers,
    aggregate_brush_knot_sizes,
    aggregate_brushes,
    aggregate_razor_manufacturers,
    aggregate_razors,
    aggregate_soap_makers,
    aggregate_soaps,
    aggregate_users,
    calculate_basic_metrics,
    filter_matched_records,
)
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.save import get_aggregated_file_path, save_aggregated_data
from sotd.cli_utils.date_span import month_span


def get_memory_usage() -> dict:
    """
    Get current memory usage information.

    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil

        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent_used": memory.percent,
        }
    except ImportError:
        return {"error": "psutil not available"}


def log_performance_metrics(metrics: dict, debug: bool = False) -> None:
    """
    Log performance metrics in a structured way.

    Args:
        metrics: Performance metrics dictionary
        debug: Enable debug logging
    """
    if not debug:
        return

    print("\n[DEBUG] Performance Summary:")
    print("=" * 50)

    total_time = sum(op.get("elapsed_seconds", 0) for op in metrics.values())
    total_records = sum(op.get("record_count", 0) for op in metrics.values())

    print(f"Total processing time: {total_time:.3f}s")
    print(f"Total records processed: {total_records}")
    if total_time > 0:
        print(f"Overall throughput: {total_records / total_time:.1f} records/sec")

    print("\nOperation breakdown:")
    for operation, data in metrics.items():
        elapsed = data.get("elapsed_seconds", 0)
        records = data.get("record_count", 0)
        rate = data.get("records_per_second", 0)
        print(f"  {operation}: {elapsed:.3f}s, {records} records, {rate:.1f} records/sec")

    # Memory usage
    memory_info = get_memory_usage()
    if "error" not in memory_info:
        print(
            f"\nMemory usage: {memory_info['used_gb']}GB / {memory_info['total_gb']}GB "
            f"({memory_info['percent_used']}%)"
        )
    print("=" * 50)


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

    # Check if output file exists and force flag
    if aggregated_path.exists() and not args.force:
        if args.debug:
            print(f"[DEBUG] Skipping existing aggregated file: {aggregated_path}")
        return {
            "year": year,
            "month": month,
            "status": "skipped",
            "reason": "file_exists",
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

        # Perform aggregations - let internal errors bubble up for fail-fast behavior
        # Only handle specific external failures that should be handled gracefully
        razors = aggregate_razors(matched_records, debug=args.debug)
        blades = aggregate_blades(matched_records, debug=args.debug)
        soaps = aggregate_soaps(matched_records, debug=args.debug)
        brushes = aggregate_brushes(matched_records, debug=args.debug)
        users = aggregate_users(matched_records, debug=args.debug)
        razor_manufacturers = aggregate_razor_manufacturers(matched_records, debug=args.debug)
        blade_manufacturers = aggregate_blade_manufacturers(matched_records, debug=args.debug)
        soap_makers = aggregate_soap_makers(matched_records, debug=args.debug)
        brush_knot_makers = aggregate_brush_knot_makers(matched_records, debug=args.debug)
        brush_handle_makers = aggregate_brush_handle_makers(matched_records, debug=args.debug)
        brush_fibers = aggregate_brush_fibers(matched_records, debug=args.debug)
        brush_knot_sizes = aggregate_brush_knot_sizes(matched_records, debug=args.debug)

        # Prepare results
        results = {
            "year": year,
            "month": month,
            "status": "success",
            "basic_metrics": basic_metrics,
            "aggregations": {
                "razors": razors,
                "razor_manufacturers": razor_manufacturers,
                "blades": blades,
                "blade_manufacturers": blade_manufacturers,
                "soaps": soaps,
                "soap_makers": soap_makers,
                "brushes": brushes,
                "brush_knot_makers": brush_knot_makers,
                "brush_handle_makers": brush_handle_makers,
                "brush_fibers": brush_fibers,
                "brush_knot_sizes": brush_knot_sizes,
                "users": users,
            },
            "summary": {
                "total_records": len(data),
                "matched_records": len(matched_records),
                "razor_count": len(razors),
                "razor_manufacturer_count": len(razor_manufacturers),
                "blade_count": len(blades),
                "blade_manufacturer_count": len(blade_manufacturers),
                "soap_count": len(soaps),
                "soap_maker_count": len(soap_makers),
                "brush_count": len(brushes),
                "brush_knot_maker_count": len(brush_knot_makers),
                "brush_handle_maker_count": len(brush_handle_makers),
                "brush_fiber_count": len(brush_fibers),
                "brush_knot_size_count": len(brush_knot_sizes),
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
    # Start overall performance monitoring
    overall_start = time.time()

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

        # Initial memory usage
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            print(
                f"[DEBUG] Initial memory usage: {memory_info['used_gb']}GB / "
                f"{memory_info['total_gb']}GB ({memory_info['percent_used']}%)"
            )

    results = []
    performance_metrics = {}

    # Process each month with progress bar
    for year, month in tqdm(months, desc="Aggregating", unit="month"):
        month_start = time.time()
        result = process_month(year, month, args)
        month_elapsed = time.time() - month_start

        # Record performance metrics for this month
        if result["status"] == "success":
            performance_metrics[f"{year:04d}-{month:02d}"] = {
                "elapsed_seconds": month_elapsed,
                "record_count": result.get("summary", {}).get("total_records", 0),
                "matched_records": result.get("summary", {}).get("matched_records", 0),
            }

        results.append(result)

    # Calculate overall performance
    overall_elapsed = time.time() - overall_start
    total_records = sum(
        r.get("summary", {}).get("total_records", 0) for r in results if r["status"] == "success"
    )

    if args.debug:
        print("\n[DEBUG] Overall performance:")
        print(f"  Total time: {overall_elapsed:.3f}s")
        print(f"  Total records: {total_records}")
        if overall_elapsed > 0:
            print(f"  Overall throughput: {total_records / overall_elapsed:.1f} records/sec")

        # Final memory usage
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            print(
                f"  Final memory usage: {memory_info['used_gb']}GB / "
                f"{memory_info['total_gb']}GB ({memory_info['percent_used']}%)"
            )

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
            print(
                f"  {error['year']:04d}-{error['month']:02d}: {error.get('error', 'Unknown error')}"
            )

    if skipped and args.debug:
        print("\n[DEBUG] Skipped:")
        for skip in skipped:
            print(
                f"  {skip['year']:04d}-{skip['month']:02d}: {skip.get('reason', 'Unknown reason')}"
            )


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the aggregate phase."""
    parser = argparse.ArgumentParser(
        description="Aggregate enriched SOTD data into statistical summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Date range arguments
    parser.add_argument(
        "--month",
        help="Process specific month (YYYY-MM format)",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Process entire year (YYYY format)",
    )
    parser.add_argument(
        "--start",
        help="Start month for range (YYYY-MM format)",
    )
    parser.add_argument(
        "--end",
        help="End month for range (YYYY-MM format)",
    )
    parser.add_argument(
        "--range",
        help="Month range (YYYY-MM:YYYY-MM format)",
    )

    # Output and control arguments
    parser.add_argument(
        "--out-dir",
        default="data",
        help="Output directory (default: data)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files",
    )

    args = parser.parse_args(argv)

    # Validate date arguments
    date_args = [args.month, args.year, args.start, args.end, args.range]
    if not any(date_args):
        # Default to current month
        now = datetime.datetime.now()
        args.month = f"{now.year:04d}-{now.month:02d}"
    elif sum(1 for arg in date_args if arg is not None) > 1:
        print("[ERROR] Only one date argument allowed")
        return

    try:
        run_aggregate(args)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
