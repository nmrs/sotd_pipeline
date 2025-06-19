#!/usr/bin/env python3
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
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

from tqdm import tqdm

from sotd.aggregate.benchmarks import run_performance_benchmark
from sotd.aggregate.cli import parse_aggregate_args
from sotd.aggregate.load import get_enriched_file_path, load_enriched_data
from sotd.aggregate.performance import get_memory_usage
from sotd.aggregate.processor import process_month
from sotd.cli_utils.date_span import month_span


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
