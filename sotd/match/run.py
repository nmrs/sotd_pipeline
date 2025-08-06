import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint
from sotd.match.cli import get_parser
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.types import MatchResult
from sotd.match.utils.performance import PerformanceMonitor
from sotd.utils.filtered_entries import load_filtered_entries

# Load filtered entries at module level for performance
_filtered_entries_manager = None


def _get_filtered_entries_manager():
    """Get or create filtered entries manager."""
    global _filtered_entries_manager
    if _filtered_entries_manager is None:
        filtered_file = Path("data/intentionally_unmatched.yaml")
        try:
            _filtered_entries_manager = load_filtered_entries(filtered_file)
        except Exception:
            # If filtered file doesn't exist or is corrupted, create empty manager
            from sotd.utils.filtered_entries import FilteredEntriesManager

            _filtered_entries_manager = FilteredEntriesManager(filtered_file)
            _filtered_entries_manager.load()
    return _filtered_entries_manager


def is_razor_matched(record: dict) -> bool:
    razor_result = record.get("razor")
    if isinstance(razor_result, MatchResult):
        return bool(razor_result.matched and razor_result.matched.get("manufacturer"))
    return (
        isinstance(razor_result, dict)
        and isinstance(razor_result.get("matched"), dict)
        and bool(razor_result["matched"].get("manufacturer"))
    )


def is_blade_matched(record: dict) -> bool:
    blade_result = record.get("blade")
    if isinstance(blade_result, MatchResult):
        return bool(blade_result.matched and blade_result.matched.get("brand"))
    return (
        isinstance(blade_result, dict)
        and isinstance(blade_result.get("matched"), dict)
        and bool(blade_result["matched"].get("brand"))
    )


def is_soap_matched(record: dict) -> bool:
    soap_result = record.get("soap")
    if isinstance(soap_result, MatchResult):
        return bool(soap_result.matched and soap_result.matched.get("maker"))
    return (
        isinstance(soap_result, dict)
        and isinstance(soap_result.get("matched"), dict)
        and bool(soap_result["matched"].get("maker"))
    )


def is_brush_matched(record: dict) -> bool:
    brush_result = record.get("brush")
    if isinstance(brush_result, MatchResult):
        return bool(brush_result.matched and brush_result.matched.get("brand"))
    return (
        isinstance(brush_result, dict)
        and isinstance(brush_result.get("matched"), dict)
        and bool(brush_result["matched"].get("brand"))
    )


def match_record(
    record: dict,
    razor_matcher: RazorMatcher,
    blade_matcher: BladeMatcher,
    soap_matcher: SoapMatcher,
    brush_matcher: "BrushMatcher | BrushScoringMatcher | BrushMatcherEntryPoint",  # type: ignore
    monitor: PerformanceMonitor,
) -> dict:
    result = record.copy()
    filtered_manager = _get_filtered_entries_manager()

    # Helper function to extract normalized text from structured data
    def extract_text(input_data: Any) -> str:
        if isinstance(input_data, dict) and "normalized" in input_data:
            # Structured data from extraction phase - return only normalized string
            return str(input_data["normalized"])
        else:
            # Fail fast - we expect structured data format
            raise ValueError(
                f"Expected structured data format with 'normalized' field, got: {type(input_data)}"
            )

    if "razor" in result:
        start_time = time.time()
        # Extract normalized and original text
        normalized_text = extract_text(result["razor"])

        # Check if razor is filtered (use normalized text)
        if filtered_manager.is_filtered("razor", normalized_text):
            # Mark as intentionally unmatched
            result["razor"] = MatchResult(
                original=result["razor"]["original"],
                matched=None,
                match_type="filtered",
                pattern=None,
            )
        else:
            razor_result = razor_matcher.match(normalized_text, result["razor"]["original"])
            result["razor"] = razor_result
        monitor.record_matcher_timing("razor", time.time() - start_time)

    if "blade" in result:
        start_time = time.time()
        # Extract normalized and original text
        normalized_text = extract_text(result["blade"])

        # Check if blade is filtered (use normalized text)
        if filtered_manager.is_filtered("blade", normalized_text):
            # Mark as intentionally unmatched
            result["blade"] = MatchResult(
                original=result["blade"]["original"],
                matched=None,
                match_type="filtered",
                pattern=None,
            )
        else:
            # Check if razor is cartridge/disposable/straight and clear blade if so
            razor_result = result.get("razor")
            if isinstance(razor_result, MatchResult) and razor_result.matched:
                razor_format = razor_result.matched.get("format", "").upper()
                irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

                if razor_format in irrelevant_formats:
                    # Clear blade info since it's irrelevant for these razor formats
                    result["blade"] = MatchResult(
                        original=result["blade"]["original"],
                        matched=None,
                        match_type="irrelevant_razor_format",
                        pattern=None,
                    )
                else:
                    # For other formats, use context-aware matching to ensure correct format
                    blade_result = blade_matcher.match_with_context(
                        normalized_text, razor_format, result["blade"]["original"]
                    )
                    result["blade"] = blade_result
            else:
                # Handle legacy dict format for razor
                razor_matched = (
                    result.get("razor", {}).get("matched", {})
                    if isinstance(result.get("razor"), dict)
                    else {}
                )
                if razor_matched:
                    razor_format = razor_matched.get("format", "").upper()
                    irrelevant_formats = ["SHAVETTE (DISPOSABLE)", "CARTRIDGE", "STRAIGHT"]

                    if razor_format in irrelevant_formats:
                        # Clear blade info since it's irrelevant for these razor formats
                        result["blade"] = MatchResult(
                            original=result["blade"]["original"],
                            matched=None,
                            match_type="irrelevant_razor_format",
                            pattern=None,
                        )
                    else:
                        # For other formats, use context-aware matching to ensure correct format
                        blade_result = blade_matcher.match_with_context(
                            normalized_text, razor_format, result["blade"]["original"]
                        )
                        result["blade"] = blade_result
                else:
                    # No razor context, match blade normally
                    blade_result = blade_matcher.match(normalized_text, result["blade"]["original"])
                    result["blade"] = blade_result
        monitor.record_matcher_timing("blade", time.time() - start_time)

    if "soap" in result:
        start_time = time.time()
        # Extract normalized and original text
        normalized_text = extract_text(result["soap"])

        # Check if soap is filtered (use normalized text)
        if filtered_manager.is_filtered("soap", normalized_text):
            # Mark as intentionally unmatched
            result["soap"] = MatchResult(
                original=result["soap"]["original"],
                matched=None,
                match_type="filtered",
                pattern=None,
            )
        else:
            soap_result = soap_matcher.match(normalized_text, result["soap"]["original"])
            result["soap"] = soap_result
        monitor.record_matcher_timing("soap", time.time() - start_time)

    if "brush" in result:
        start_time = time.time()
        # Extract normalized and original text
        normalized_text = extract_text(result["brush"])

        # Check if brush is filtered (use normalized text)
        if filtered_manager.is_filtered("brush", normalized_text):
            # Mark as intentionally unmatched
            result["brush"] = MatchResult(
                original=result["brush"]["original"],
                matched=None,
                match_type="filtered",
                pattern=None,
            )
        else:
            brush_result = brush_matcher.match(normalized_text)
            result["brush"] = brush_result
        monitor.record_matcher_timing("brush", time.time() - start_time)

    return result


def process_month(
    month: str,
    base_path: Path,
    force: bool = False,
    debug: bool = False,
    max_workers: int = 1,
    correct_matches_path: Optional[Path] = None,
    brush_system: str = "current",
) -> dict:
    """Process a single month of data."""
    try:
        # Initialize performance monitor
        monitor = PerformanceMonitor("match", max_workers)
        monitor.start_total_timing()

        # Initialize parallel data manager
        from sotd.match.brush_parallel_data_manager import BrushParallelDataManager

        data_manager = BrushParallelDataManager(base_path)

        # Load extracted data
        extracted_path = base_path / "extracted" / f"{month}.json"
        if not extracted_path.exists():
            return {"status": "skipped", "month": month, "reason": "missing input file"}

        # Check if output already exists and force is not set
        if data_manager.file_exists(month, brush_system) and not force:
            return {"status": "skipped", "month": month, "reason": "output exists"}

        # Load data
        monitor.start_file_io_timing()
        with open(extracted_path) as f:
            data = json.load(f)
        monitor.end_file_io_timing()

        # Initialize matchers
        monitor.start_processing_timing()
        blade_matcher = BladeMatcher(correct_matches_path=correct_matches_path)

        # Initialize brush matcher using entry point for system selection
        use_scoring_system = brush_system == "new"
        brush_matcher = BrushMatcherEntryPoint(
            use_scoring_system=use_scoring_system,
            correct_matches_path=correct_matches_path,
            debug=debug,
        )

        # Attach monitor for strategy timing if using legacy system
        if not use_scoring_system:
            # Only legacy BrushMatcher has monitor attribute
            if hasattr(brush_matcher.matcher, "monitor"):
                brush_matcher.matcher.monitor = monitor  # type: ignore

        razor_matcher = RazorMatcher(correct_matches_path=correct_matches_path)
        soap_matcher = SoapMatcher(correct_matches_path=correct_matches_path)

        # Process records
        records = data.get("data", [])
        monitor.set_record_count(len(records))

        for i, record in enumerate(records):
            # Use the match_record function that includes blade clearing logic
            matched_record = match_record(
                record, razor_matcher, blade_matcher, soap_matcher, brush_matcher, monitor
            )
            # Convert MatchResult objects to dicts for JSON serialization
            converted_record = {}
            for key, value in matched_record.items():
                if hasattr(value, "original"):  # Check if it's a MatchResult
                    # Get the original structured data from the input record
                    original_structured_data = record.get(key, {})

                    # Extract original and normalized text from the structured data
                    if (
                        isinstance(original_structured_data, dict)
                        and "normalized" in original_structured_data
                    ):
                        original_text = original_structured_data["original"]
                        normalized_text = original_structured_data["normalized"]
                    else:
                        # Fallback to the MatchResult original field
                        original_text = value.original
                        normalized_text = value.original

                    converted_record[key] = {
                        "original": original_text,
                        "normalized": normalized_text,
                        "matched": value.matched,
                        "match_type": value.match_type,
                        "pattern": value.pattern,
                    }
                else:
                    converted_record[key] = value
            # Update the record in the list
            records[i] = converted_record

        monitor.end_processing_timing()

        # Record cache statistics
        brush_cache_stats = brush_matcher.get_cache_stats()
        monitor.record_cache_stats("brush_matcher", brush_cache_stats)

        # Save results using parallel data manager
        monitor.start_file_io_timing()

        data_manager.create_directories()

        output_data = {
            "metadata": {
                "month": month,
                "record_count": len(records),
                "performance": monitor.get_summary(),
                "brush_system": brush_system,
            },
            "data": records,
        }

        output_path = data_manager.save_data(month, output_data, brush_system)
        monitor.end_file_io_timing()

        if debug:
            print(f"Saved data to: {output_path}")

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
        # Provide more detailed error information for debugging
        import traceback

        error_msg = str(e)
        full_traceback = traceback.format_exc()

        # Add context for brush matching errors
        if "No handle patterns matched for brand" in error_msg:
            error_msg = (
                f"Brush matching error: {error_msg}. This means the brand has "
                f"handle_matching enabled in brushes.yaml but no corresponding handle "
                f"patterns were found in handles.yaml. Check that the brand name "
                f"matches exactly between the two files."
            )
        elif "handle_matching enabled but no handle patterns found" in error_msg:
            error_msg = (
                f"Brush configuration error: {error_msg}. Add handle patterns for "
                f"this brand to handles.yaml or set handle_matching: false in "
                f"brushes.yaml."
            )
        elif "'NoneType' object has no attribute 'get'" in error_msg:
            error_msg = (
                f"Data structure error: {error_msg}. This usually indicates a "
                f"missing or malformed YAML file, or a bug in the matching logic. "
                f"Check that all required YAML files exist and have valid structure. "
                f"Full traceback: {full_traceback}"
            )

        return {
            "status": "error",
            "month": month,
            "error": error_msg,
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
                    None,  # correct_matches_path
                    args.brush_system,
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
            result = process_month(
                f"{year:04d}-{month:02d}",
                base_path,
                args.force,
                args.debug,
                1,
                None,  # correct_matches_path
                args.brush_system,
            )

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
