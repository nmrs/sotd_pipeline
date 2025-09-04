import json
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from sotd.cli_utils.date_span import month_span
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.cli import get_parser
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.types import MatchResult
from sotd.match.utils.performance import PerformanceMonitor
from sotd.match.utils import calculate_match_statistics, format_match_statistics_for_display
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
    brush_matcher: "BrushMatcher",  # type: ignore
    monitor: PerformanceMonitor,
    debug: bool = False,
    enable_razor: bool = True,
    enable_blade: bool = True,
    enable_soap: bool = True,
    enable_brush: bool = True,
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

    if "razor" in result and enable_razor:
        if debug:
            print(f"  🔪 Processing razor: {result['razor'].get('original', 'Unknown')[:50]}...")
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
            if debug:
                print("    ⏭️  Razor filtered, skipping")
        else:
            razor_result = razor_matcher.match(normalized_text, result["razor"]["original"])
            # Use MatchResult consistently
            if razor_result is not None and razor_result.matched:
                # Update the MatchResult to include normalized field
                razor_result.normalized = result["razor"]["normalized"]
                result["razor"] = razor_result
                if debug:
                    brand = razor_result.matched.get("brand", "Unknown")
                    model = razor_result.matched.get("model", "Unknown")
                    print(f"    ✅ Razor matched: {brand} {model}")
            elif razor_result is not None:
                # Matcher returned a result but it's not matched
                razor_result.normalized = result["razor"]["normalized"]
                result["razor"] = razor_result
                if debug:
                    print("    ❌ Razor no match")
            else:
                result["razor"] = MatchResult(
                    original=result["razor"]["original"],
                    normalized=result["razor"]["normalized"],
                    matched=None,
                    match_type=None,
                    pattern=None,
                )
                if debug:
                    print("    ❌ Razor no match")
        monitor.record_matcher_timing("razor", time.time() - start_time)

    if "blade" in result and enable_blade:
        if debug:
            print(f"  🪒 Processing blade: {result['blade'].get('original', 'Unknown')[:50]}...")
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
            if debug:
                print("    ⏭️  Blade filtered, skipping")
        else:
            # Check razor format and handle blade matching accordingly
            razor_result = result.get("razor")
            if isinstance(razor_result, MatchResult) and razor_result.matched:
                razor_format = razor_result.matched.get("format", "").upper()

                # Handle Cartridge/Disposable razors - auto-match to Cartridge/Disposable blade
                if razor_format in ["CARTRIDGE/DISPOSABLE", "CARTRIDGE", "DISPOSABLE"]:
                    blade_result = blade_matcher.match_cartridge_auto(normalized_text)
                    # Update the MatchResult to include normalized field
                    blade_result.normalized = result["blade"]["normalized"]
                    result["blade"] = blade_result
                    if debug:
                        print(
                            f"    ✅ Blade auto-matched to Cartridge/Disposable for {razor_format}"
                        )

                # Handle other irrelevant formats - clear blade info
                elif razor_format in ["SHAVETTE (DISPOSABLE)", "STRAIGHT"]:
                    result["blade"] = MatchResult(
                        original=result["blade"]["original"],
                        normalized=result["blade"]["normalized"],
                        matched=None,
                        match_type="irrelevant_razor_format",
                        pattern=None,
                    )
                    if debug:
                        print(f"    ⏭️  Blade irrelevant for {razor_format}")

                # For other formats, use context-aware matching to ensure correct format
                else:
                    blade_result = blade_matcher.match_with_context(
                        normalized_text, razor_format, result["blade"]["original"]
                    )
                    # Update the MatchResult to include normalized field
                    if blade_result is not None:
                        blade_result.normalized = result["blade"]["normalized"]
                        result["blade"] = blade_result
                        if debug:
                            if blade_result.matched:
                                print(
                                    f"    ✅ Blade matched: {blade_result.matched.get('brand', 'Unknown')} {blade_result.matched.get('model', 'Unknown')}"
                                )
                            else:
                                print(f"    ❌ Blade no match")
                    else:
                        result["blade"] = MatchResult(
                            original=result["blade"]["original"],
                            normalized=result["blade"]["normalized"],
                            matched=None,
                            match_type=None,
                            pattern=None,
                        )
                        if debug:
                            print(f"    ❌ Blade no match")
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
                        if debug:
                            print(f"    ⏭️  Blade irrelevant for {razor_format}")
                    else:
                        # For other formats, use context-aware matching to ensure correct format
                        blade_result = blade_matcher.match_with_context(
                            normalized_text, razor_format, result["blade"]["original"]
                        )
                        result["blade"] = blade_result
                        if debug:
                            if blade_result and blade_result.matched:
                                print(
                                    f"    ✅ Blade matched: {blade_result.matched.get('brand', 'Unknown')} {blade_result.matched.get('model', 'Unknown')}"
                                )
                            else:
                                print(f"    ❌ Blade no match")
                else:
                    # No razor context, use basic matching
                    blade_result = blade_matcher.match(normalized_text, result["blade"]["original"])
                    result["blade"] = blade_result
                    if debug:
                        if blade_result and blade_result.matched:
                            print(
                                f"    ✅ Blade matched: {blade_result.matched.get('brand', 'Unknown')} {blade_result.matched.get('model', 'Unknown')}"
                            )
                        else:
                            print(f"    ❌ Blade no match")
        monitor.record_matcher_timing("blade", time.time() - start_time)

    if "soap" in result and enable_soap:
        if debug:
            print(f"  🧼 Processing soap: {result['soap'].get('original', 'Unknown')[:50]}...")
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
            if debug:
                print(f"    ⏭️  Soap filtered, skipping")
        else:
            soap_result = soap_matcher.match(normalized_text, result["soap"]["original"])
            result["soap"] = soap_result
            if debug:
                if soap_result and soap_result.matched:
                    print(
                        f"    ✅ Soap matched: {soap_result.matched.get('brand', 'Unknown')} {soap_result.matched.get('model', 'Unknown')}"
                    )
                else:
                    print(f"    ❌ Soap no match")
        monitor.record_matcher_timing("soap", time.time() - start_time)

    if "brush" in result and enable_brush:
        if debug:
            print(f"  🖌️  Processing brush: {result['brush'].get('original', 'Unknown')[:50]}...")
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
            if debug:
                print(f"    ⏭️  Brush filtered, skipping")
        else:
            if debug:
                print(f"    🎯 Running brush matcher strategies...")
            brush_result = brush_matcher.match(normalized_text)
            # Convert MatchResult to dict for consistency
            if brush_result is not None:
                result["brush"] = {
                    "original": brush_result.original,
                    "normalized": result["brush"]["normalized"],  # Preserve normalized field
                    "matched": brush_result.matched,
                    "match_type": brush_result.match_type,
                    "pattern": brush_result.pattern,
                }
                if debug:
                    if brush_result.matched:
                        print(
                            f"    ✅ Brush matched: {brush_result.matched.get('brand', 'Unknown')} {brush_result.matched.get('model', 'Unknown')} (strategy: {getattr(brush_result, 'strategy', 'unknown')})"
                        )
                    else:
                        print(f"    ❌ Brush no match")
            else:
                result["brush"] = {
                    "original": result["brush"]["original"],
                    "normalized": result["brush"]["normalized"],  # Preserve normalized field
                    "matched": None,
                    "match_type": None,
                    "pattern": None,
                }
                if debug:
                    print(f"    ❌ Brush no match")
        monitor.record_matcher_timing("brush", time.time() - start_time)

    return result


def process_month(
    month: str,
    base_path: Path,
    force: bool = False,
    debug: bool = False,
    max_workers: int = 1,
    correct_matches_path: Optional[Path] = None,
) -> dict:
    """Process a single month of data."""
    try:
        # Initialize performance monitor
        monitor = PerformanceMonitor("match", max_workers)
        monitor.start_total_timing()

        # Initialize simple data manager
        from sotd.match.simple_data_manager import SimpleDataManager

        data_manager = SimpleDataManager(base_path)

        # Load extracted data
        extracted_path = base_path / "extracted" / f"{month}.json"
        if not extracted_path.exists():
            return {"status": "skipped", "month": month, "reason": "missing input file"}

        # Check if output already exists and force is not set
        if data_manager.file_exists(month) and not force:
            return {"status": "skipped", "month": month, "reason": "output exists"}

        # Load data
        monitor.start_file_io_timing()
        with open(extracted_path) as f:
            data = json.load(f)
        monitor.end_file_io_timing()

        # Initialize matchers
        monitor.start_processing_timing()
        blade_matcher = BladeMatcher(correct_matches_path=correct_matches_path)

        # Initialize brush matcher using the new multi-strategy scoring system
        brush_matcher = BrushMatcher(
            correct_matches_path=correct_matches_path,
            debug=debug,
        )

        razor_matcher = RazorMatcher(correct_matches_path=correct_matches_path)
        soap_matcher = SoapMatcher(correct_matches_path=correct_matches_path)

        # Process records
        records = data.get("data", [])
        monitor.set_record_count(len(records))

        if debug:
            print(f"🎯 Processing {len(records)} records...")

        for i, record in enumerate(records):
            if debug:
                print(f"\n📝 Record {i + 1}/{len(records)}")
                comment_id = record.get("comment_id", "unknown")
                print(f"   Comment ID: {comment_id}")

            # Use the match_record function that includes blade clearing logic
            matched_record = match_record(
                record,
                razor_matcher,
                blade_matcher,
                soap_matcher,
                brush_matcher,
                monitor,
                debug,
                enable_razor=True,
                enable_blade=True,
                enable_soap=True,
                enable_brush=True,
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

                    # Base fields for all product types
                    base_fields = {
                        "original": original_text,
                        "normalized": normalized_text,
                        "matched": value.matched,
                        "match_type": value.match_type,
                        "pattern": value.pattern,
                        "strategy": getattr(value, "strategy", None),
                    }

                    # Add brush-specific strategy scoring fields only for brush records
                    if key == "brush":
                        base_fields.update(
                            {
                                "all_strategies": getattr(value, "all_strategies", None),
                            }
                        )

                    converted_record[key] = base_fields
                else:
                    converted_record[key] = value
            # Update the record in the list
            records[i] = converted_record

        monitor.end_processing_timing()

        # Record cache statistics
        brush_cache_stats = brush_matcher.get_cache_stats()
        monitor.record_cache_stats("brush_matcher", brush_cache_stats)

        # Calculate enhanced match statistics
        match_statistics = calculate_match_statistics(records)

        # Save results using parallel data manager
        monitor.start_file_io_timing()

        data_manager.create_directories()

        output_data = {
            "metadata": {
                "month": month,
                "record_count": len(records),
                "performance": monitor.get_summary(),
                "match_statistics": match_statistics,
            },
            "data": records,
        }

        output_path = data_manager.save_data(month, output_data)
        monitor.end_file_io_timing()

        if debug:
            print(f"Saved data to: {output_path}")

        # End timing and get performance summary
        monitor.end_total_timing()
        performance = monitor.get_summary()

        # Add match statistics to performance data
        performance["match_statistics"] = match_statistics

        if debug:
            monitor.print_summary()

            # Display enhanced match statistics
            print("\n" + format_match_statistics_for_display(match_statistics))

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

    # Create parallel processor for match phase
    from sotd.utils.parallel_processor import create_parallel_processor

    processor = create_parallel_processor("match")

    # Determine if we should use parallel processing
    use_parallel = processor.should_use_parallel(months, args, args.debug)

    if use_parallel:
        # Get max workers for parallel processing
        max_workers = processor.get_max_workers(months, args, default=8)

        # Process months in parallel using common processor
        results = processor.process_months_parallel(
            months,
            _process_month_for_parallel,
            (base_path, args.force, args.debug, max_workers, None),
            max_workers,
            "Processing",
        )

        # Print parallel processing summary
        processor.print_parallel_summary(results, "match")

    else:
        # Process months sequentially
        results = processor.process_months_sequential(
            months,
            _process_month_for_sequential,
            (base_path, args.force, args.debug, None),
            "Months",
        )

    # Display error details for failed months
    errors = [r for r in results if "error" in r]
    if errors:
        print("\nError Details:")
        for error_result in errors:
            month = error_result.get("month", "unknown")
            error_msg = error_result.get("error", "unknown error")
            print(f"  {month}: {error_msg}")


def _process_month_for_parallel(
    year: int,
    month: int,
    base_path: Path,
    force: bool,
    debug: bool,
    max_workers: int,
    correct_matches_path: Optional[Path],
) -> dict:
    """Process a single month for parallel processing."""
    month_str = f"{year:04d}-{month:02d}"
    return process_month(month_str, base_path, force, debug, max_workers, correct_matches_path)


def _process_month_for_sequential(
    year: int,
    month: int,
    base_path: Path,
    force: bool,
    debug: bool,
    correct_matches_path: Optional[Path],
) -> dict:
    """Process a single month for sequential processing."""
    month_str = f"{year:04d}-{month:02d}"
    return process_month(month_str, base_path, force, debug, 1, correct_matches_path)


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
