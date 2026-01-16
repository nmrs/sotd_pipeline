"""
Pipeline orchestration entry-point.

This module provides a unified interface for running the SOTD pipeline phases.
Individual phases can be run separately or as part of a complete pipeline workflow.
"""

import argparse
import datetime
import io
import re
import sys
import time
from contextlib import redirect_stdout
from typing import Any, Dict, List, Optional, Tuple


def validate_month(value: str) -> str:
    """Validate month format (YYYY-MM) and ensure month is 01-12."""
    import re

    if not re.match(r"^\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(f"Invalid month format: {value} (expected YYYY-MM)")

    # Validate month value
    year, month = value.split("-")
    if not (1 <= int(month) <= 12):
        raise argparse.ArgumentTypeError(f"Invalid month value: {value} (month must be 01-12)")

    # All validation passed, return the value
    # Type checker sees exceptions as non-return paths, but they're valid control flow
    return value  # type: ignore[return-value]


def validate_range(value: str) -> str:
    """Validate range format (YYYY-MM:YYYY-MM or YYYY:YYYY for annual).

    Supports both monthly range format (YYYY-MM:YYYY-MM) and annual range format (YYYY:YYYY).
    """
    import re

    # Check if this is an annual range (YYYY:YYYY format)
    if ":" in value and len(value.split(":")) == 2:
        start, end = value.split(":")
        if len(start) == 4 and start.isdigit() and len(end) == 4 and end.isdigit():
            # This is a valid annual range format
            return value

    # Validate monthly range format (YYYY-MM:YYYY-MM)
    if not re.match(r"^\d{4}-\d{2}:\d{4}-\d{2}$", value):
        raise argparse.ArgumentTypeError(
            f"Invalid range format: {value} (expected YYYY-MM:YYYY-MM or YYYY:YYYY for annual)"
        )

    # Validate month values in range
    start, end = value.split(":")
    for v in (start, end):
        year, month = v.split("-")
        if not (1 <= int(month) <= 12):
            raise argparse.ArgumentTypeError(
                f"Invalid month value in range: {v} (month must be 01-12)"
            )

    return value


def get_default_month() -> str:
    """Get the default month (previous month) in YYYY-MM format."""
    now = datetime.datetime.now()
    # Calculate previous month
    if now.month == 1:
        prev_year = now.year - 1
        prev_month = 12
    else:
        prev_year = now.year
        prev_month = now.month - 1

    return f"{prev_year:04d}-{prev_month:02d}"


def calculate_delta_months(args) -> list[str]:
    """
    Calculate delta months for comparison: current month(s) + 1 month ago, 1 year ago, 5 years ago.

    Args:
        args: Parsed command line arguments

    Returns:
        List of months in YYYY-MM format to process
    """
    delta_months = set()  # Use set to avoid duplicates

    # Get current month(s) from args
    if args.month:
        delta_months.add(args.month)
    elif args.year:
        # For year, add first and last month of the year
        delta_months.add(f"{args.year}-01")
        delta_months.add(f"{args.year}-12")
    elif args.start and args.end:
        # For range, add start and end months
        delta_months.add(args.start)
        delta_months.add(args.end)
    elif args.range:
        # For range format, expand the full range and add all months
        start, end = args.range.split(":")
        start_year, start_month = map(int, start.split("-"))
        end_year, end_month = map(int, end.split("-"))

        # Expand the range to include all months
        current_year, current_month = start_year, start_month
        while (current_year, current_month) <= (end_year, end_month):
            delta_months.add(f"{current_year:04d}-{current_month:02d}")
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
    elif args.ytd:
        # For YTD, add all months from January to current month
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        # Add all months from January to current month
        for month in range(1, current_month + 1):
            delta_months.add(f"{current_year:04d}-{month:02d}")
    else:
        # Default to previous month
        default_month = get_default_month()
        delta_months.add(default_month)

        # Add historical comparison months
    if args.ytd:
        # For YTD mode, use the cleaner approach:
        # 1. Start with YTD months (Jan to current month)
        # 2. For each YTD month, add month-1, month-1year, month-5years if not already present

        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        # YTD months are already in delta_months (Jan to current month)
        # Now add historical comparison months for each YTD month
        ytd_months = list(delta_months)  # Copy to avoid modification during iteration

        for month_str in ytd_months:
            year, month = map(int, month_str.split("-"))

            # Month - 1 month
            if month == 1:
                one_month_ago = f"{year - 1}-12"
            else:
                one_month_ago = f"{year}-{month - 1:02d}"

            if one_month_ago not in delta_months:
                delta_months.add(one_month_ago)

            # Month - 1 year
            one_year_ago = f"{year - 1}-{month:02d}"
            if one_year_ago not in delta_months:
                delta_months.add(one_year_ago)

            # Month - 5 years
            five_years_ago = f"{year - 5}-{month:02d}"
            if five_years_ago not in delta_months:
                delta_months.add(five_years_ago)
    else:
        # For non-YTD mode, use the original logic
        for month_str in list(
            delta_months
        ):  # Convert to list to avoid modification during iteration
            year, month = map(int, month_str.split("-"))

            # 1 month ago
            if month == 1:
                one_month_ago = f"{year - 1}-12"
            else:
                one_month_ago = f"{year}-{month - 1:02d}"
            delta_months.add(one_month_ago)

            # 1 year ago
            one_year_ago = f"{year - 1}-{month:02d}"
            delta_months.add(one_year_ago)

            # 5 years ago
            five_years_ago = f"{year - 5}-{month:02d}"
            delta_months.add(five_years_ago)

    # Sort months chronologically
    return sorted(list(delta_months))


def calculate_months_from_args(args: List[str]) -> List[str]:
    """
    Calculate months from date arguments in args list.

    Args:
        args: List of command line arguments

    Returns:
        List of months in YYYY-MM format
    """

    # Parse args into a simple namespace-like structure
    class Args:
        month: Optional[str] = None
        year: Optional[int] = None
        start: Optional[str] = None
        end: Optional[str] = None
        range: Optional[str] = None
        delta_months: Optional[str] = None
        ytd: bool = False

    parsed_args = Args()

    # Parse arguments from list
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--month" and i + 1 < len(args):
            parsed_args.month = args[i + 1]
            i += 2
        elif arg == "--year" and i + 1 < len(args):
            try:
                parsed_args.year = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif arg == "--start" and i + 1 < len(args):
            parsed_args.start = args[i + 1]
            i += 2
        elif arg == "--end" and i + 1 < len(args):
            parsed_args.end = args[i + 1]
            i += 2
        elif arg == "--range" and i + 1 < len(args):
            parsed_args.range = args[i + 1]
            i += 2
        elif arg == "--delta-months" and i + 1 < len(args):
            parsed_args.delta_months = args[i + 1]
            i += 2
        elif arg == "--ytd":
            parsed_args.ytd = True
            i += 1
        else:
            i += 1

    # Use similar logic to month_span() from date_span.py
    if parsed_args.delta_months:
        # Handle delta months (comma-separated list)
        months = []
        for month_str in parsed_args.delta_months.split(","):
            month_str = month_str.strip()
            if month_str:
                months.append(month_str)
        return months

    if parsed_args.month:
        return [parsed_args.month]

    if parsed_args.year:
        return [f"{parsed_args.year}-{m:02d}" for m in range(1, 13)]

    if parsed_args.range:
        try:
            start_str, end_str = parsed_args.range.split(":")
            start_year, start_month = map(int, start_str.split("-"))
            end_year, end_month = map(int, end_str.split("-"))

            months = []
            current_year, current_month = start_year, start_month
            while (current_year, current_month) <= (end_year, end_month):
                months.append(f"{current_year:04d}-{current_month:02d}")
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            return months
        except (ValueError, AttributeError):
            pass

    if parsed_args.start and parsed_args.end:
        try:
            start_year, start_month = map(int, parsed_args.start.split("-"))
            end_year, end_month = map(int, parsed_args.end.split("-"))

            months = []
            current_year, current_month = start_year, start_month
            while (current_year, current_month) <= (end_year, end_month):
                months.append(f"{current_year:04d}-{current_month:02d}")
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            return months
        except (ValueError, AttributeError):
            pass

    if parsed_args.ytd:
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month
        return [f"{current_year}-{m:02d}" for m in range(1, current_month + 1)]

    # Default to previous month if no date arguments
    return [get_default_month()]


def parse_record_count_from_output(output: str, phase: str) -> Optional[int]:
    """
    Parse record count from phase output.

    Args:
        output: Captured stdout output from phase execution
        phase: Phase name for context-specific parsing

    Returns:
        Record count if found, None otherwise
    """
    if not output:
        return None

    # Patterns to match different output formats
    patterns = [
        # Match: "Total Records: 70,306" (from parallel processor summary)
        r"Total Records:\s*([\d,]+)",
        # Enrich: "Total Records: 70,306" (from parallel processor summary)
        # Aggregate: "70306 records processed" (from engine output)
        r"(\d[\d,]*)\s+records processed",
        # Alternative format: "records processed: 70,306"
        r"records processed[:\s]+([\d,]+)",
        # Alternative format: "Total records: 70,306"
        r"Total records[:\s]+([\d,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            # Extract number and remove commas
            number_str = match.group(1).replace(",", "")
            try:
                return int(number_str)
            except ValueError:
                continue

    return None


def print_pipeline_summary(
    phase_results: List[Dict[str, Any]],
    total_time: float,
    args: List[str],
    phases_failed: bool = False,
) -> None:
    """
    Print comprehensive pipeline summary with timing and statistics.

    Args:
        phase_results: List of phase execution results with name, duration, exit_code,
                       records_processed, and records_per_second
        total_time: Total wall clock time for the pipeline
        args: Command line arguments used
        phases_failed: Whether the pipeline failed partway through
    """
    # Calculate months processed
    months = calculate_months_from_args(args)
    months_count = len(months)
    months_per_second = months_count / total_time if total_time > 0 else 0.0

    # Get record counts from phases (they may differ as records drop out)
    # Track first and last phase counts
    first_phase_records = None
    last_phase_records = None

    for result in phase_results:
        records = result.get("records_processed")
        if records is not None:
            if first_phase_records is None:
                first_phase_records = records
            last_phase_records = records

    print(f"\n{'=' * 60}")
    print("PIPELINE SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Wall Time: {total_time:.2f}s")
    print(f"Months Processed: {months_count}")
    print(f"Throughput: {months_per_second:.2f} months/s")
    if first_phase_records is not None:
        print(f"Records In: {first_phase_records:,}")
    if last_phase_records is not None and last_phase_records != first_phase_records:
        print(f"Records Out: {last_phase_records:,}")
    elif last_phase_records is not None:
        # If they're the same, just show one
        print(f"Records: {last_phase_records:,}")

    if phase_results:
        print("\nPhase Breakdown:")
        for i, result in enumerate(phase_results, 1):
            phase_name = result["name"]
            phase_duration = result["duration"]
            phase_status = "✓" if result["exit_code"] == 0 else "✗"
            records = result.get("records_processed")
            records_per_sec = result.get("records_per_second")

            # Calculate months/s for this phase (only if multiple months)
            months_per_sec_phase = None
            if months_count > 1 and phase_duration > 0:
                months_per_sec_phase = months_count / phase_duration

            # Build phase line
            phase_line = f"  Phase {i} ({phase_name}): {phase_duration:6.2f}s {phase_status}"
            if records is not None:
                phase_line += f" | {records:,} records"
            if records_per_sec is not None:
                phase_line += f" | {records_per_sec:,.0f} records/s"
            if months_per_sec_phase is not None:
                phase_line += f" | {months_per_sec_phase:.2f} months/s"
            print(phase_line)

    if phases_failed:
        print("\nNote: Pipeline failed partway through. Summary shows completed phases only.")

    print(f"{'=' * 60}\n")


def run_phase(phase: str, args: List[str], debug: bool = False) -> Tuple[int, str]:
    """
    Run a specific pipeline phase.

    Args:
        phase: Phase name (fetch, extract, match, enrich, aggregate, report)
        args: Command line arguments to pass to the phase
        debug: Whether debug mode is enabled

    Returns:
        Tuple of (exit_code, captured_output)
    """
    phase_modules = {
        "fetch": "sotd.fetch.run",
        "extract": "sotd.extract.run",
        "match": "sotd.match.run",
        "enrich": "sotd.enrich.run",
        "aggregate": "sotd.aggregate.run",
        "report": "sotd.report.run",
    }

    if phase not in phase_modules:
        print(f"[ERROR] Unknown phase: {phase}")
        print(f"[INFO] Available phases: {', '.join(phase_modules.keys())}")
        return 1

    try:
        module_name = phase_modules[phase]
        module = __import__(module_name, fromlist=["main"])

        # Filter arguments based on phase requirements
        # Each phase has different argument support, so we need to filter appropriately
        phase_args = []
        i = 0

        while i < len(args):
            arg = args[i]

            # Handle arguments that take values
            if arg.startswith("--delta-months"):
                # Only pass delta-months to phases that support it
                if phase in ["fetch", "extract", "match", "enrich", "aggregate"]:
                    phase_args.append(arg)
                    # Add the value too (next argument)
                    if i + 1 < len(args):
                        phase_args.append(args[i + 1])
                        i += 1  # Skip the value in next iteration
                # If phase doesn't support it, skip both flag and value
                i += 1
                continue

            elif arg.startswith("--max-workers"):
                # Only pass max-workers to phases that support parallel processing
                if phase in ["extract", "match", "enrich", "aggregate", "report"]:
                    phase_args.append(arg)
                    # Add the value too (next argument)
                    if i + 1 < len(args):
                        phase_args.append(args[i + 1])
                        i += 1  # Skip the value in next iteration
                    i += 1  # Skip the flag
                else:
                    # If phase doesn't support it, skip both flag and value
                    if i + 1 < len(args):
                        i += 2  # Skip both flag and value
                    else:
                        i += 1  # Skip just the flag if no value
                continue

            elif arg.startswith("--type"):
                # Only pass type to report phase
                if phase == "report":
                    phase_args.append(arg)
                    # Add the value too (next argument)
                    if i + 1 < len(args):
                        phase_args.append(args[i + 1])
                        i += 1  # Skip the value in next iteration
                # If phase doesn't support it, skip both flag and value
                i += 1
                continue

            elif arg.startswith("--annual"):
                # Pass annual to both aggregate and report phases
                if phase in ["aggregate", "report"]:
                    phase_args.append(arg)
                # If phase doesn't support it, skip it
                i += 1
                continue

            # Pass through all other arguments (date args, out-dir, debug, force)
            phase_args.append(arg)
            i += 1

        # Debug output to see what arguments are being passed
        if debug:
            print(f"[DEBUG] {phase} phase args: {phase_args}")

        # Capture stdout during phase execution
        output_buffer = io.StringIO()
        try:
            with redirect_stdout(output_buffer):
                # Run the phase with filtered arguments and capture exit code
                exit_code = module.main(phase_args)
                exit_code = exit_code if exit_code is not None else 0
        finally:
            # Always restore stdout and get captured output
            captured_output = output_buffer.getvalue()
            # Print captured output to maintain normal behavior
            print(captured_output, end="")

        return (exit_code, captured_output)

    except ImportError as e:
        print(f"[ERROR] Failed to import {phase} phase: {e}")
        return (1, "")
    except Exception as e:
        print(f"[ERROR] Failed to run {phase} phase: {e}")
        return (1, "")


def run_pipeline(phases: List[str], args: List[str], debug: bool = False) -> int:
    """
    Run multiple pipeline phases in sequence.

    Args:
        phases: List of phases to run in order
        args: Base arguments to pass to each phase
        debug: Enable debug logging

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if debug:
        print(f"[DEBUG] Running pipeline phases: {', '.join(phases)}")
        print(f"[DEBUG] Base arguments: {args}")

    # Track pipeline timing and results
    pipeline_start_time = time.time()
    phase_results: List[Dict[str, Any]] = []

    # Add visual separation for multi-phase runs
    if len(phases) > 1:
        print(f"\n{'=' * 60}")
        print(f"RUNNING PIPELINE: {len(phases)} phases")
        print(f"Phases: {' → '.join(phases)}")
        print(f"{'=' * 60}\n")

    for i, phase in enumerate(phases):
        # Add clear phase header
        if len(phases) > 1:
            print(f"\n{'=' * 50}")
            print(f"PHASE {i + 1}/{len(phases)}: {phase.upper()}")
            print(f"{'=' * 50}")
        elif debug:
            print(f"\n[DEBUG] Running phase {i + 1}/{len(phases)}: {phase}")

        # Track phase timing
        phase_start_time = time.time()
        exit_code, captured_output = run_phase(phase, args, debug=debug)
        phase_duration = time.time() - phase_start_time

        # Parse record count from output
        records_processed = parse_record_count_from_output(captured_output, phase)
        records_per_second = (
            records_processed / phase_duration if records_processed and phase_duration > 0 else None
        )

        # Record phase result
        phase_results.append(
            {
                "name": phase,
                "duration": phase_duration,
                "exit_code": exit_code,
                "records_processed": records_processed,
                "records_per_second": records_per_second,
            }
        )

        if exit_code != 0:
            print(f"\n{'=' * 60}")
            print(f"PIPELINE FAILED: Phase {phase} failed with exit code {exit_code}")
            print(f"Completed phases: {', '.join(phases[:i])}")
            print(f"Failed phase: {phase}")
            print(f"Remaining phases: {', '.join(phases[i + 1 :])}")
            print(f"{'=' * 60}\n")
            # Show summary up to failure point
            if len(phases) > 1:
                total_time = time.time() - pipeline_start_time
                print_pipeline_summary(phase_results, total_time, args, phases_failed=True)
            return exit_code

        if debug:
            print(f"[DEBUG] Phase {phase} completed successfully")

    # Calculate total pipeline time
    total_time = time.time() - pipeline_start_time

    # Add completion summary for multi-phase runs
    if len(phases) > 1:
        print(f"\n{'=' * 60}")
        print(f"PIPELINE COMPLETE: {len(phases)} phases finished successfully")
        print(f"{'=' * 60}\n")
        # Print comprehensive summary
        print_pipeline_summary(phase_results, total_time, args)

    return 0


def get_phase_range(phase_range: str) -> List[str]:
    """
    Parse a phase range string and return the list of phases to run.

    Args:
        phase_range: Phase range string in format:
            - "phase" (single phase)
            - "phase1:phase2" (inclusive range)
            - "phase:" (from phase to end)
            - ":phase" (from beginning to phase)
            - "" (all phases)

    Returns:
        List of phases to run in order
    """
    all_phases = ["fetch", "extract", "match", "enrich", "aggregate", "report"]

    if not phase_range:
        return all_phases

    if ":" not in phase_range:
        # Single phase
        if phase_range not in all_phases:
            raise ValueError(f"Invalid phase: {phase_range}. Valid phases: {', '.join(all_phases)}")
        return [phase_range]

    # Parse range
    parts = phase_range.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid phase range format: {phase_range}. Expected format: phase1:phase2"
        )

    start_phase, end_phase = parts

    if not start_phase and not end_phase:
        return all_phases

    if not start_phase:
        # :phase - from beginning to phase
        if end_phase not in all_phases:
            raise ValueError(
                f"Invalid end phase: {end_phase}. Valid phases: {', '.join(all_phases)}"
            )
        end_idx = all_phases.index(end_phase)
        return all_phases[: end_idx + 1]

    if not end_phase:
        # phase: - from phase to end
        if start_phase not in all_phases:
            raise ValueError(
                f"Invalid start phase: {start_phase}. Valid phases: {', '.join(all_phases)}"
            )
        start_idx = all_phases.index(start_phase)
        return all_phases[start_idx:]

    # phase1:phase2 - inclusive range
    if start_phase not in all_phases:
        raise ValueError(
            f"Invalid start phase: {start_phase}. Valid phases: {', '.join(all_phases)}"
        )
    if end_phase not in all_phases:
        raise ValueError(f"Invalid end phase: {end_phase}. Valid phases: {', '.join(all_phases)}")

    start_idx = all_phases.index(start_phase)
    end_idx = all_phases.index(end_phase)

    if start_idx > end_idx:
        raise ValueError(f"Start phase '{start_phase}' comes after end phase '{end_phase}'")

    return all_phases[start_idx : end_idx + 1]


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the SOTD pipeline.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="SOTD Pipeline - Shave of the Day Data Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Phases:
  fetch      - Fetch SOTD threads from Reddit
  extract    - Extract product mentions from comments
  match      - Match products to catalog data
  enrich     - Enrich matched data with additional information
  aggregate  - Generate statistical summaries
  report     - Generate hardware and software reports

Examples:
  # Run individual phases (defaults to previous month)
  python run.py fetch
  python run.py extract
  python run.py match
  python run.py enrich
  python run.py aggregate
  python run.py report --type hardware
  
  # Run with specific month
  python run.py fetch --month 2025-01
  python run.py extract --month 2025-01
  python run.py match --month 2025-01
  python run.py enrich --month 2025-01
  python run.py aggregate --month 2025-01
  python run.py report --month 2025-01 --type hardware
  
  # Run complete pipeline (all phases, defaults to previous month)
  python run.py
  
  # Run specific phase ranges (defaults to previous month)
  python run.py extract:enrich
  python run.py match:
  python run.py :aggregate
  python run.py fetch:match
  
  # Run with debug logging
  python run.py --debug --force
        """,
    )

    # Phase or phase range argument (positional)
    parser.add_argument(
        "phase_range",
        nargs="?",
        default="",
        help=(
            "Phase or phase range to run (e.g., fetch, extract:enrich, match:, :aggregate). "
            "Default: all phases"
        ),
    )

    # Common arguments for all phases
    parser.add_argument(
        "--month",
        type=validate_month,
        help="Process specific month (YYYY-MM format, default: previous month)",
    )
    parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    parser.add_argument(
        "--start", type=validate_month, help="Start month for range (YYYY-MM format)"
    )
    parser.add_argument("--end", type=validate_month, help="End month for range (YYYY-MM format)")
    parser.add_argument(
        "--range",
        type=validate_range,
        help="Date range (YYYY-MM:YYYY-MM for monthly, YYYY:YYYY for annual)",
    )
    parser.add_argument("--out-dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum parallel workers for month processing (default: 8)",
    )
    parser.add_argument(
        "--delta",
        action="store_true",
        help=("Process delta months: current month(s) + 1 month ago, 1 year ago, and 5 years ago"),
    )
    parser.add_argument(
        "--ytd",
        action="store_true",
        help=(
            "Process year-to-date: from January 1st of current year to current month "
            "(equivalent to --range 2025-01:2025-08 for August 2025)"
        ),
    )
    # Report-specific arguments
    parser.add_argument(
        "--type",
        choices=["hardware", "software", "all"],
        help="Report type: hardware, software, or all (only applies to report phase)",
    )
    parser.add_argument(
        "--annual",
        action="store_true",
        help="Generate annual reports (only applies to report phase, requires --year or --range)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show INFO messages during pipeline execution",
    )

    args = parser.parse_args(argv)

    # Validate mutually exclusive date arguments
    # Note: args.ytd is False when not specified (not None), so we need to check for truthy values
    date_args = [
        args.month if args.month else None,
        args.year if args.year else None,
        args.start if args.start else None,
        args.end if args.end else None,
        args.range if args.range else None,
        args.ytd if args.ytd else None,
    ]
    active_date_args = [arg for arg in date_args if arg is not None]

    if len(active_date_args) > 1:
        # Check for specific conflicts
        if args.month and args.ytd:
            print("[ERROR] Cannot use --month and --ytd together. Use one or the other.")
            return 1
        if args.month and args.range:
            print("[ERROR] Cannot use --month and --range together. Use one or the other.")
            return 1
        if args.year and args.ytd:
            print("[ERROR] Cannot use --year and --ytd together. Use one or the other.")
            return 1
        if args.year and args.range:
            print("[ERROR] Cannot use --year and --range together. Use one or the other.")
            return 1
        if args.ytd and args.range:
            print("[ERROR] Cannot use --ytd and --range together. Use one or the other.")
            return 1
        if args.ytd and (args.start or args.end):
            print("[ERROR] Cannot use --ytd with --start/--end. Use one or the other.")
            return 1
        if args.range and (args.start or args.end):
            print("[ERROR] Cannot use --range with --start/--end. Use one or the other.")
            return 1

        # Generic error for other combinations
        print(f"[ERROR] Multiple conflicting date arguments specified: {active_date_args}")
        print("Use only one of: --month, --year, --range, --start/--end, or --ytd")
        return 1

    try:
        # Determine phases to run
        try:
            phases = get_phase_range(args.phase_range)
        except ValueError as e:
            print(f"[ERROR] {e}")
            return 1

        if not phases:
            print("[ERROR] No phases specified to run")
            return 1

        if args.debug:
            print(f"[DEBUG] Running phases: {', '.join(phases)}")

        # Build common arguments
        common_args = []

        # Handle date arguments - if none provided, default to previous month
        has_date_args = bool(
            args.month or args.year or args.start or args.end or args.range or args.ytd
        )

        if args.delta:
            # Delta mode: process current month(s) + historical comparison months
            delta_months = calculate_delta_months(args)
            if args.debug:
                print(
                    f"[DEBUG] Delta mode: processing {len(delta_months)} months: "
                    f"{', '.join(delta_months)}"
                )
            # Pass delta-months to all phases - they will filter as needed
            common_args.extend(["--delta-months", ",".join(delta_months)])

            # Also add the original date arguments for analysis phases (aggregate, report)
            # These phases will ignore delta-months and use the original date args
            if args.month:
                common_args.extend(["--month", args.month])
            elif args.year:
                common_args.extend(["--year", str(args.year)])
            elif args.start:
                common_args.extend(["--start", args.start])
            elif args.end:
                common_args.extend(["--end", args.end])
            elif args.range:
                common_args.extend(["--range", args.range])
        elif args.ytd:
            # YTD mode: process from January 1st of current year to current month
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            ytd_start = f"{current_year}-01"
            ytd_end = f"{current_year}-{current_month:02d}"
            if args.debug:
                print(f"[DEBUG] YTD mode: processing range {ytd_start} to {ytd_end}")
            common_args.extend(["--start", ytd_start, "--end", ytd_end])
        elif args.month:
            common_args.extend(["--month", args.month])
        elif args.year:
            common_args.extend(["--year", str(args.year)])
        elif args.start:
            common_args.extend(["--start", args.start])
        elif args.end:
            common_args.extend(["--end", args.end])
        elif args.range:
            common_args.extend(["--range", args.range])
        elif not has_date_args:
            # Default to previous month if no date arguments provided
            default_month = get_default_month()
            common_args.extend(["--month", default_month])
            if args.debug:
                print(f"[DEBUG] No date arguments provided, defaulting to: {default_month}")

        if args.out_dir:
            common_args.extend(["--out-dir", args.out_dir])
        if args.debug:
            common_args.append("--debug")
        if args.force:
            common_args.append("--force")
        if args.verbose:
            common_args.append("--verbose")
        if args.max_workers:
            common_args.extend(["--max-workers", str(args.max_workers)])
        if args.type:
            common_args.extend(["--type", args.type])
        if args.annual:
            common_args.append("--annual")

        return run_pipeline(phases, common_args, debug=args.debug)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
