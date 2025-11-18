import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from sotd.utils.performance import PerformanceMonitor, PipelineOutputFormatter

from .load import load_enriched_data
from .processor import aggregate_all
from .save import save_aggregated_data


def process_months(
    months: Sequence[str], data_dir: Path, debug: bool = False, force: bool = False
) -> bool:
    """Main orchestration for aggregating SOTD data for one or more months."""
    # Show progress bar for processing
    print(f"Processing {len(months)} month{'s' if len(months) != 1 else ''}...")

    results = []
    for month in tqdm(months, desc="Months", unit="month"):
        monitor = PerformanceMonitor("aggregate")
        monitor.start_total_timing()

        # Check if output already exists and force is not set
        output_path = data_dir / "aggregated" / f"{month}.json"
        if output_path.exists() and not force:
            print(f"  {month}: output exists")
            continue

        try:
            monitor.start_file_io_timing()
            records = load_enriched_data(month, data_dir)
            monitor.end_file_io_timing()

            if debug:
                print(f"Loaded {len(records)} records for {month}")

            monitor.set_record_count(len(records))

            # Aggregate all categories
            aggregated_data = aggregate_all(records, month, debug=debug)

            monitor.start_file_io_timing()
            save_aggregated_data(aggregated_data, month, data_dir)
            monitor.end_file_io_timing()

            monitor.end_total_timing()
            if debug:
                monitor.print_summary()
                print(f"Saved aggregated data for {month}")

            # Collect results for summary
            results.append(
                {
                    "month": month,
                    "record_count": len(records),
                    "performance": monitor.get_summary(),
                }
            )

        except FileNotFoundError as e:
            results.append(
                {
                    "status": "error",
                    "month": month,
                    "error": f"{e}. Run enrich phase first.",
                }
            )
        except Exception as e:
            results.append(
                {
                    "status": "error",
                    "month": month,
                    "error": f"Failed to process {month}: {e}",
                }
            )

    # Filter results and check for errors
    errors = [r for r in results if "error" in r]
    completed = [r for r in results if "error" not in r]

    # Display error details for failed months
    if errors:
        print("\n❌ Error Details:")
        for error_result in errors:
            month = error_result.get("month", "unknown")
            error_msg = error_result.get("error", "unknown error")
            print(f"  {month}: {error_msg}")

    # Print summary using standardized formatter
    if len(months) == 1:
        # Single month summary
        month = months[0]
        if completed:
            stats = completed[0]
            summary = PipelineOutputFormatter.format_single_month_summary("aggregate", month, stats)
            print(summary)
    else:
        # Multi-month summary
        start_month = months[0]
        end_month = months[-1]

        total_stats = {
            "total_records": sum(r.get("record_count", 0) for r in completed),
        }
        summary = PipelineOutputFormatter.format_multi_month_summary(
            "aggregate", start_month, end_month, total_stats
        )
        print(summary)

    # Return True if there were errors, False otherwise
    return len(errors) > 0


def process_months_parallel(
    months: Sequence[str],
    data_dir: Path,
    debug: bool = False,
    force: bool = False,
    max_workers: int = 8,
) -> bool:
    """Process multiple months in parallel using ProcessPoolExecutor."""
    print(f"Processing {len(months)} months in parallel...")

    # Start wall clock timing
    wall_clock_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all month processing tasks
        future_to_month = {
            executor.submit(process_single_month, month, data_dir, debug, force): month
            for month in months
        }

        # Process results as they complete
        results = []
        for future in tqdm(
            as_completed(future_to_month), total=len(months), desc="Processing", unit="month"
        ):
            month = future_to_month[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[ERROR] Failed to process {month}: {e}")

    # Filter results and check for errors
    errors = [r for r in results if r and "error" in r]
    completed = [r for r in results if r and "error" not in r]

    # Display error details for failed months
    if errors:
        print("\n❌ Error Details:")
        for error_result in errors:
            month = error_result.get("month", "unknown")
            error_msg = error_result.get("error", "unknown error")
            print(f"  {month}: {error_msg}")

    # Print summary
    wall_clock_time = time.time() - wall_clock_start
    total_records = sum(r.get("record_count", 0) for r in completed)

    if completed:
        print(
            f"[INFO] SOTD aggregate complete for {months[0]}…{months[-1]}: "
            f"{total_records} records processed"
        )
    print(f"Parallel processing completed in {wall_clock_time:.2f}s")

    # Return True if there were errors, False otherwise
    return len(errors) > 0


def process_single_month(
    month: str, data_dir: Path, debug: bool = False, force: bool = False
) -> dict | None:
    """Process a single month for parallel processing."""
    try:
        monitor = PerformanceMonitor("aggregate")
        monitor.start_total_timing()

        # Check if output already exists and force is not set
        output_path = data_dir / "aggregated" / f"{month}.json"
        if output_path.exists() and not force:
            return None

        monitor.start_file_io_timing()
        records = load_enriched_data(month, data_dir)
        monitor.end_file_io_timing()

        if debug:
            print(f"Loaded {len(records)} records for {month}")

        monitor.set_record_count(len(records))

        # Aggregate all categories
        aggregated_data = aggregate_all(records, month, debug=debug)

        monitor.start_file_io_timing()
        save_aggregated_data(aggregated_data, month, data_dir)
        monitor.end_file_io_timing()

        monitor.end_total_timing()

        return {
            "month": month,
            "record_count": len(records),
            "performance": monitor.get_summary(),
        }

    except FileNotFoundError as e:
        return {
            "status": "error",
            "month": month,
            "error": f"{e}. Run enrich phase first.",
        }
    except Exception as e:
        return {
            "status": "error",
            "month": month,
            "error": f"Failed to process {month}: {e}",
        }
