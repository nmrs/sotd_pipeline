"""
Shared parallel processing utilities for SOTD Pipeline phases.

This module provides standardized parallel month processing functionality
to eliminate code duplication across extract, match, enrich, and other phases.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Tuple

from tqdm import tqdm


class ParallelMonthProcessor:
    """
    Utility class for parallel month processing across pipeline phases.

    Provides standardized parallel processing logic that can be used by
    extract, match, enrich, aggregate, and other phases.
    """

    def __init__(self, phase_name: str):
        """
        Initialize the parallel processor.

        Args:
            phase_name: Name of the phase (e.g., "extract", "match", "enrich")
        """
        self.phase_name = phase_name

    def should_use_parallel(
        self, months: List[Tuple[int, int]], args: Any, debug: bool = False
    ) -> bool:
        """
        Determine if parallel processing should be used.

        Args:
            months: List of (year, month) tuples
            args: CLI arguments object
            debug: Whether debug mode is enabled

        Returns:
            True if parallel processing should be used
        """
        if hasattr(args, "sequential") and args.sequential:
            return False
        elif hasattr(args, "parallel") and args.parallel:
            return True
        else:
            return len(months) > 1 and not debug

    def get_max_workers(self, months: List[Tuple[int, int]], args: Any, default: int = 4) -> int:
        """
        Get the maximum number of workers for parallel processing.

        Args:
            months: List of (year, month) tuples
            args: CLI arguments object
            default: Default max workers if not specified

        Returns:
            Maximum number of workers
        """
        return min(len(months), getattr(args, "max_workers", default))

    def process_months_parallel(
        self,
        months: List[Tuple[int, int]],
        process_func: Callable,
        process_args: Tuple[Any, ...],
        max_workers: int,
        desc: str = "Processing",
    ) -> List[Dict[str, Any]]:
        """
        Process multiple months in parallel using ProcessPoolExecutor.

        Args:
            months: List of (year, month) tuples
            process_func: Function to call for each month
            process_args: Additional arguments to pass to process_func
            max_workers: Maximum number of parallel workers
            desc: Description for progress bar

        Returns:
            List of results from processing each month
        """
        print(f"Processing {len(months)} months in parallel...")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all month processing tasks
            future_to_month = {
                executor.submit(process_func, year, month, *process_args): f"{year:04d}-{month:02d}"
                for year, month in months
            }

            # Process results as they complete
            results = []
            for future in tqdm(
                as_completed(future_to_month), total=len(future_to_month), desc=desc
            ):
                month = future_to_month[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error processing {month}: {e}")
                    results.append({"month": month, "error": str(e)})

        return results

    def process_months_sequential(
        self,
        months: List[Tuple[int, int]],
        process_func: Callable,
        process_args: Tuple[Any, ...],
        desc: str = "Months",
    ) -> List[Dict[str, Any]]:
        """
        Process multiple months sequentially.

        Args:
            months: List of (year, month) tuples
            process_func: Function to call for each month
            process_args: Additional arguments to pass to process_func
            desc: Description for progress bar

        Returns:
            List of results from processing each month
        """
        print(f"Processing {len(months)} month{'s' if len(months) != 1 else ''}...")

        results = []
        for year, month in tqdm(months, desc=desc, unit="month"):
            result = process_func(year, month, *process_args)
            if result:
                results.append(result)

        return results

    def print_parallel_summary(self, results: List[Dict[str, Any]], phase_name: str) -> None:
        """
        Print a standardized summary for parallel processing results.

        Args:
            results: List of processing results
            phase_name: Name of the phase for display
        """
        completed = [r for r in results if "error" not in r]
        errors = [r for r in results if "error" in r]

        print("\nParallel processing summary:")
        print(f"  Completed: {len(completed)} months")
        print(f"  Errors: {len(errors)} months")

        if completed:
            # Print phase-specific summary
            self._print_phase_summary(completed, phase_name)

    def _print_phase_summary(
        self, completed_results: List[Dict[str, Any]], phase_name: str
    ) -> None:
        """
        Print phase-specific summary information.

        Args:
            completed_results: List of completed results (no errors)
            phase_name: Name of the phase
        """
        if phase_name == "extract":
            total_shaves = sum(r.get("shave_count", 0) for r in completed_results)
            total_missing = sum(r.get("missing_count", 0) for r in completed_results)
            total_skipped = sum(r.get("skipped_count", 0) for r in completed_results)

            print("\nExtraction Summary:")
            print(f"  Total Shaves: {total_shaves:,}")
            print(f"  Total Missing: {total_missing:,}")
            print(f"  Total Skipped: {total_skipped:,}")

        elif phase_name == "enrich":
            total_records = sum(r.get("records_processed", 0) for r in completed_results)
            total_enriched = sum(r.get("total_enriched", 0) for r in completed_results)

            print("\nEnrichment Summary:")
            print(f"  Total Records: {total_records:,}")
            print(f"  Total Enriched: {total_enriched:,}")

        elif phase_name == "match":
            total_records = sum(r.get("records_processed", 0) for r in completed_results)
            total_time = sum(
                r.get("performance", {}).get("total_processing_time_seconds", 0)
                for r in completed_results
            )
            avg_records_per_sec = total_records / total_time if total_time > 0 else 0

            print("\nPerformance Summary:")
            print(f"  Total Records: {total_records:,}")
            print(f"  Total Processing Time: {total_time:.2f}s")
            print(f"  Average Throughput: {avg_records_per_sec:.0f} records/sec")


def create_parallel_processor(phase_name: str) -> ParallelMonthProcessor:
    """
    Factory function to create a parallel processor for a specific phase.

    Args:
        phase_name: Name of the phase (e.g., "extract", "match", "enrich")

    Returns:
        Configured ParallelMonthProcessor instance
    """
    return ParallelMonthProcessor(phase_name)
