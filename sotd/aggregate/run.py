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
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

from tqdm import tqdm

from sotd.aggregate.aggregation_functions import calculate_basic_metrics, filter_matched_records
from sotd.aggregate.benchmarks import run_performance_benchmark
from sotd.aggregate.engine import (
    aggregate_blackbird_plates,
    aggregate_blade_manufacturers,
    aggregate_brush_fibers,
    aggregate_brush_handle_makers,
    aggregate_brush_knot_makers,
    aggregate_brush_knot_sizes,
    aggregate_christopher_bradley_plates,
    aggregate_game_changer_plates,
    aggregate_razor_blade_combinations,
    aggregate_razor_manufacturers,
    aggregate_soap_makers,
    aggregate_straight_razor_specs,
    aggregate_super_speed_tips,
)
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.product_aggregators import (
    aggregate_blades,
    aggregate_brushes,
    aggregate_razors,
    aggregate_soaps,
)
from sotd.aggregate.save import get_aggregated_file_path, save_aggregated_data
from sotd.aggregate.user_aggregators import aggregate_user_blade_usage, aggregate_users
from sotd.aggregate.cli import parse_aggregate_args
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

        # Determine which specialized aggregations to run based on CLI flags
        run_specialized = getattr(args, "enable_specialized", False) or not getattr(
            args, "disable_specialized", False
        )
        run_cross_product = getattr(args, "enable_cross_product", False) or not getattr(
            args, "disable_cross_product", False
        )

        if args.debug:
            print("[DEBUG] Aggregation settings:")
            print(f"  Specialized aggregations: {'enabled' if run_specialized else 'disabled'}")
            print(f"  Cross-product analysis: {'enabled' if run_cross_product else 'disabled'}")

        # Initialize specialized aggregation results
        blackbird_plates = []
        christopher_bradley_plates = []
        game_changer_plates = []
        super_speed_tips = []
        straight_razor_specs = []
        razor_blade_combinations = []
        user_blade_usage = []

        # Perform specialized aggregations if enabled
        if run_specialized:
            if args.debug:
                print("[DEBUG] Running specialized aggregations...")
            blackbird_plates = aggregate_blackbird_plates(matched_records, debug=args.debug)
            christopher_bradley_plates = aggregate_christopher_bradley_plates(
                matched_records, debug=args.debug
            )
            game_changer_plates = aggregate_game_changer_plates(matched_records, debug=args.debug)
            super_speed_tips = aggregate_super_speed_tips(matched_records, debug=args.debug)
            straight_razor_specs = aggregate_straight_razor_specs(matched_records, debug=args.debug)

        # Perform cross-product analysis if enabled
        if run_cross_product:
            if args.debug:
                print("[DEBUG] Running cross-product analysis...")
            razor_blade_combinations = aggregate_razor_blade_combinations(
                matched_records, debug=args.debug
            )
            user_blade_usage = aggregate_user_blade_usage(matched_records, debug=args.debug)

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
                "blackbird_plates": blackbird_plates,
                "christopher_bradley_plates": christopher_bradley_plates,
                "game_changer_plates": game_changer_plates,
                "super_speed_tips": super_speed_tips,
                "straight_razor_specs": straight_razor_specs,
                "razor_blade_combinations": razor_blade_combinations,
                "user_blade_usage": user_blade_usage,
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
                "blackbird_plate_count": len(blackbird_plates),
                "christopher_bradley_plate_count": len(christopher_bradley_plates),
                "game_changer_plate_count": len(game_changer_plates),
                "super_speed_tip_count": len(super_speed_tips),
                "straight_razor_spec_count": len(straight_razor_specs),
                "razor_blade_combination_count": len(razor_blade_combinations),
                "user_blade_usage_count": len(user_blade_usage),
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


def run_benchmark(args: argparse.Namespace) -> None:
    """Run performance benchmarks on aggregate operations."""
    print("[INFO] Running performance benchmarks...")

    # Check if we have sample data to benchmark against
    sample_data_path = None
    if args.month:
        # Use existing enriched data if available
        year, month = map(int, args.month.split("-"))
        base_dir = Path(args.out_dir)
        sample_data_path = get_enriched_file_path(base_dir, year, month)

    if sample_data_path and sample_data_path.exists():
        print(f"[INFO] Using existing enriched data: {sample_data_path}")
        try:
            metadata, data = load_enriched_data(sample_data_path, debug=args.debug)
            if not data:
                print("[ERROR] No data found in enriched file")
                return
        except Exception as e:
            print(f"[ERROR] Failed to load enriched data: {e}")
            return
    else:
        print("[INFO] No existing data found, creating synthetic test data...")
        # Create synthetic test data for benchmarking
        data = _create_synthetic_test_data()

    # Run benchmarks
    results_dir = Path(args.out_dir) / "benchmarks" if args.save_results else None
    run_performance_benchmark(
        test_data=data, debug=args.debug, save_results=args.save_results, results_dir=results_dir
    )

    print("[INFO] Benchmark completed successfully!")


def _create_synthetic_test_data() -> List[Dict[str, Any]]:
    """Create synthetic test data for benchmarking."""
    import random

    # Generate realistic test data
    test_data = []
    users = [f"user_{i}" for i in range(1, 101)]
    razors = ["Merkur 34C", "Rockwell 6C", "Gillette Tech", "Blackland Blackbird"]
    blades = ["Astra SP", "Feather", "Gillette Silver Blue", "Personna"]
    soaps = ["Barrister and Mann Seville", "Declaration Grooming Original", "Noble Otter Barrbarr"]
    brushes = ["Simpson Chubby 2", "Declaration Grooming B8", "Omega 10049"]

    for i in range(1000):  # 1000 test records
        record = {
            "id": f"test_{i}",
            "author": random.choice(users),
            "razor": {
                "matched": {
                    "brand": random.choice(razors).split()[0],
                    "model": " ".join(random.choice(razors).split()[1:]),
                    "format": "DE",
                    "match_type": "exact",
                }
            },
            "blade": {
                "matched": {
                    "brand": random.choice(blades).split()[0],
                    "model": " ".join(random.choice(blades).split()[1:]),
                    "match_type": "exact",
                }
            },
            "soap": {
                "matched": {
                    "maker": random.choice(soaps).split()[0],
                    "scent": " ".join(random.choice(soaps).split()[1:]),
                    "match_type": "exact",
                }
            },
            "brush": {
                "matched": {
                    "brand": random.choice(brushes).split()[0],
                    "model": " ".join(random.choice(brushes).split()[1:]),
                    "fiber": "synthetic",
                    "knot_size_mm": random.choice([24, 26, 28, 30]),
                    "match_type": "exact",
                }
            },
        }
        test_data.append(record)

    return test_data


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the aggregate phase."""
    args = parse_aggregate_args(argv)
    try:
        if args.mode == "aggregate":
            run_aggregate(args)
        elif args.mode == "benchmark":
            run_benchmark(args)
        else:
            print(f"[ERROR] Unknown mode: {args.mode}")
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
