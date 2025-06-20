from pathlib import Path
from typing import Sequence

from tqdm import tqdm

from sotd.utils.performance import PerformanceMonitor

from .load import load_enriched_data
from .processor import aggregate_all
from .save import save_aggregated_data


def process_months(months: Sequence[str], data_dir: Path, debug: bool = False) -> None:
    """Main orchestration for aggregating SOTD data for one or more months."""
    for month in tqdm(months, desc="Aggregating months"):
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
            aggregated_data = aggregate_all(records, month)

            monitor.start_file_io_timing()
            save_aggregated_data(aggregated_data, month, data_dir)
            monitor.end_file_io_timing()

            monitor.end_total_timing()
            if debug:
                monitor.print_summary()
                print(f"Saved aggregated data for {month}")

        except FileNotFoundError as e:
            print(f"[WARN] {e}")
        except Exception as e:
            print(f"[ERROR] Failed to process {month}: {e}")
