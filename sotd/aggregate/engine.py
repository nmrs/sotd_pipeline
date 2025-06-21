from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from sotd.utils.performance import PerformanceMonitor, PipelineOutputFormatter

from .load import load_enriched_data
from .processor import aggregate_all
from .save import save_aggregated_data


def process_months(months: Sequence[str], data_dir: Path, debug: bool = False) -> None:
    """Main orchestration for aggregating SOTD data for one or more months."""
    # Show progress bar for processing
    print(f"Processing {len(months)} month{'s' if len(months) != 1 else ''}...")

    results = []
    for month in tqdm(months, desc="Months", unit="month"):
        monitor = PerformanceMonitor("aggregate")
        monitor.start_total_timing()
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
            print(f"[WARN] {e}")
        except Exception as e:
            print(f"[ERROR] Failed to process {month}: {e}")

    # Print summary using standardized formatter
    if len(months) == 1:
        # Single month summary
        month = months[0]
        if results:
            stats = results[0]
            summary = PipelineOutputFormatter.format_single_month_summary("aggregate", month, stats)
            print(summary)
    else:
        # Multi-month summary
        start_month = months[0]
        end_month = months[-1]

        total_stats = {
            "total_records": sum(r["record_count"] for r in results),
        }
        summary = PipelineOutputFormatter.format_multi_month_summary(
            "aggregate", start_month, end_month, total_stats
        )
        print(summary)
