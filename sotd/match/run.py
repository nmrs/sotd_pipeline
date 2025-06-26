import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.cli import get_parser
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.utils.performance import PerformanceMonitor


def is_razor_matched(record: dict) -> bool:
    return (
        isinstance(record.get("razor"), dict)
        and isinstance(record["razor"].get("matched"), dict)
        and bool(record["razor"]["matched"].get("manufacturer"))
    )


def is_blade_matched(record: dict) -> bool:
    return (
        isinstance(record.get("blade"), dict)
        and isinstance(record["blade"].get("matched"), dict)
        and bool(record["blade"]["matched"].get("brand"))
    )


def is_soap_matched(record: dict) -> bool:
    return (
        isinstance(record.get("soap"), dict)
        and isinstance(record["soap"].get("matched"), dict)
        and bool(record["soap"]["matched"].get("maker"))
    )


def is_brush_matched(record: dict) -> bool:
    return (
        isinstance(record.get("brush"), dict)
        and isinstance(record["brush"].get("matched"), dict)
        and bool(record["brush"]["matched"].get("brand"))
    )


def match_record(
    record: dict,
    razor_matcher: RazorMatcher,
    blade_matcher: BladeMatcher,
    soap_matcher: SoapMatcher,
    brush_matcher: BrushMatcher,
    monitor: PerformanceMonitor,
) -> dict:
    result = record.copy()

    if "razor" in result:
        start_time = time.time()
        result["razor"] = razor_matcher.match(result["razor"])
        monitor.record_matcher_timing("razor", time.time() - start_time)

    if "blade" in result:
        start_time = time.time()
        # Check if razor is cartridge/disposable/straight and clear blade if so
        razor_matched = result.get("razor", {}).get("matched", {})
        if razor_matched:
            razor_format = razor_matched.get("format", "").upper()
            irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

            if razor_format in irrelevant_formats:
                # Clear blade info since it's irrelevant for these razor formats
                result["blade"] = {"original": result["blade"], "matched": None, "match_type": None}
            else:
                # For other formats, match normally
                result["blade"] = blade_matcher.match(result["blade"])
        else:
            # No razor context, match blade normally
            result["blade"] = blade_matcher.match(result["blade"])
        monitor.record_matcher_timing("blade", time.time() - start_time)

    if "soap" in result:
        start_time = time.time()
        result["soap"] = soap_matcher.match(result["soap"])
        monitor.record_matcher_timing("soap", time.time() - start_time)
    if "brush" in result:
        start_time = time.time()
        result["brush"] = brush_matcher.match(result["brush"])
        monitor.record_matcher_timing("brush", time.time() - start_time)
    return result


def process_month(
    month: str,
    base_path: Path,
    force: bool = False,
    debug: bool = False,
    max_workers: int = 1,
) -> dict:
    """Process a single month of data."""
    try:
        # Initialize performance monitor
        monitor = PerformanceMonitor("match", max_workers)
        monitor.start_total_timing()

        # Load extracted data
        extracted_path = base_path / "extracted" / f"{month}.json"
        if not extracted_path.exists():
            return {"status": "skipped", "month": month, "reason": "missing input file"}

        # Check if output already exists and force is not set
        matched_path = base_path / "matched" / f"{month}.json"
        if matched_path.exists() and not force:
            return {"status": "skipped", "month": month, "reason": "output exists"}

        # Load data
        monitor.start_file_io_timing()
        with open(extracted_path) as f:
            data = json.load(f)
        monitor.end_file_io_timing()

        # Set file sizes
        monitor.set_file_sizes(extracted_path, matched_path)

        # Initialize matchers
        monitor.start_processing_timing()
        blade_matcher = BladeMatcher()
        brush_matcher = BrushMatcher()
        razor_matcher = RazorMatcher()
        soap_matcher = SoapMatcher()

        # Process records
        records = data.get("data", [])
        monitor.set_record_count(len(records))

        for i, record in enumerate(records):
            # Use the match_record function that includes blade clearing logic
            matched_record = match_record(
                record, razor_matcher, blade_matcher, soap_matcher, brush_matcher, monitor
            )
            # Update the record in the list
            records[i] = matched_record

        monitor.end_processing_timing()

        # Save results
        monitor.start_file_io_timing()
        matched_path.parent.mkdir(exist_ok=True)
        with open(matched_path, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "month": month,
                        "record_count": len(records),
                        "performance": monitor.get_summary(),
                    },
                    "data": records,
                },
                f,
                indent=2,
            )
        monitor.end_file_io_timing()

        # End timing and get performance summary
        monitor.end_total_timing()
        performance = monitor.get_summary()

        if debug:
            monitor.print_summary()

        return {
            "status": "completed",
            "month": month,
            "records_processed": len(records),
            "performance": performance,
        }

    except Exception as e:
        return {
            "status": "error",
            "month": month,
            "error": str(e),
        }


def run_match(args):
    base_path = Path(args.out_dir)
    months = list(month_span(args))

    # Determine if we should use parallel processing
    if args.sequential:
        use_parallel = False
    elif args.parallel:
        use_parallel = True
    else:
        use_parallel = len(months) > 1 and not args.debug

    if use_parallel:
        print(f"Processing {len(months)} months in parallel...")

        # Use ProcessPoolExecutor for month-level parallelization
        max_workers = min(len(months), args.max_workers)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all month processing tasks
            future_to_month = {
                executor.submit(
                    process_month,
                    f"{year:04d}-{month:02d}",
                    base_path,
                    args.force,
                    args.debug,
                    max_workers,
                ): f"{year:04d}-{month:02d}"
                for year, month in months
            }

            # Process results as they complete
            results = []
            for future in tqdm(
                as_completed(future_to_month), total=len(future_to_month), desc="Processing"
            ):
                month = future_to_month[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"status": "error", "month": month, "error": str(e)})

        # Print summary of parallel processing
        completed = [r for r in results if r["status"] == "completed"]
        skipped = [r for r in results if r["status"] == "skipped"]
        errors = [r for r in results if r["status"] == "error"]

        print("\nParallel processing summary:")
        print(f"  Completed: {len(completed)} months")
        print(f"  Skipped: {len(skipped)} months")
        print(f"  Errors: {len(errors)} months")

        if completed:
            total_records = sum(r.get("records_processed", 0) for r in completed)
            total_time = sum(
                r.get("performance", {}).get("total_processing_time_seconds", 0) for r in completed
            )
            avg_records_per_sec = total_records / total_time if total_time > 0 else 0

            print("\nPerformance Summary:")
            print(f"  Total Records: {total_records:,}")
            print(f"  Total Processing Time: {total_time:.2f}s")
            print(f"  Average Throughput: {avg_records_per_sec:.0f} records/sec")

            # Print detailed performance for first completed month as example
            if completed:
                example = completed[0]
                performance = example.get("performance", {})
                print(f"\nExample month ({example['month']}) performance:")
                print(f"  Records: {example.get('records_processed', 0):,}")
                processing_time = performance.get("total_processing_time_seconds", 0)
                print(f"  Processing Time: {processing_time:.2f}s")
                records_per_sec = performance.get("records_per_second", 0)
                print(f"  Throughput: {records_per_sec:.0f} records/sec")

                if args.debug:
                    print("\nDetailed Performance Summary:")
                    print(f"  File I/O: {performance.get('file_io_time_seconds', 0):.2f}s")
                    print(f"  Processing: {performance.get('processing_time_seconds', 0):.2f}s")
                    avg_time_per_record = performance.get("avg_time_per_record_seconds", 0) * 1000
                    print(f"  Average Time per Record: {avg_time_per_record:.1f}ms")

                    # Print matcher performance if available
                    matcher_times = performance.get("matcher_times", {})
                    if matcher_times:
                        print("\nMatcher Performance:")
                        for matcher, stats in matcher_times.items():
                            avg_time = stats.get("avg_time_seconds", 0) * 1000
                            count = stats.get("count", 0)
                            print(f"  {matcher}: {avg_time:.1f}ms avg ({count} calls)")

    else:
        # Sequential processing
        print(f"Processing {len(months)} months sequentially...")

        for year, month in tqdm(months, desc="Months", unit="month"):
            result = process_month(f"{year:04d}-{month:02d}", base_path, args.force, args.debug, 1)

            if result["status"] == "completed":
                print(f"  {result['month']}: {result['records_processed']:,} records")
            elif result["status"] == "skipped":
                print(f"  {result['month']}: {result['reason']}")
            else:
                print(f"  {result['month']}: ERROR - {result['error']}")


def run_analysis(args):
    for year, month in month_span(args):
        matched_path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if matched_path.exists():
            subprocess.run(
                ["python", "sotd/match/tools/analyze_unmatched_razors.py", str(matched_path)],
                check=True,
            )
        elif args.debug:
            print(f"Skipping missing file: {matched_path}")


def main(argv=None) -> int:
    """Main entry point for the match phase."""
    try:
        parser = get_parser()
        args = parser.parse_args(argv)

        if args.mode == "match":
            run_match(args)
        elif args.mode == "analyze_unmatched_razors":
            run_analysis(args)

        return 0  # Success
    except KeyboardInterrupt:
        print("\n[INFO] Match phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        print(f"[ERROR] Match phase failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
