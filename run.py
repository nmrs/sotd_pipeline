"""
Pipeline orchestration entry-point.

This module provides a unified interface for running the SOTD pipeline phases.
Individual phases can be run separately or as part of a complete pipeline workflow.
"""

import argparse
import datetime
import sys
from typing import List, Optional


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
    else:
        # Default to previous month
        default_month = get_default_month()
        delta_months.add(default_month)

    # Add historical comparison months
    for month_str in list(delta_months):  # Convert to list to avoid modification during iteration
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


def run_phase(phase: str, args: List[str]) -> int:
    """
    Run a specific pipeline phase.

    Args:
        phase: Phase name (fetch, extract, match, enrich, aggregate, report)
        args: Command line arguments to pass to the phase

    Returns:
        Exit code (0 for success, non-zero for failure)
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

        # Run the phase with provided arguments and capture exit code
        exit_code = module.main(args)
        return exit_code if exit_code is not None else 0

    except ImportError as e:
        print(f"[ERROR] Failed to import {phase} phase: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to run {phase} phase: {e}")
        return 1


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

        exit_code = run_phase(phase, args)
        if exit_code != 0:
            print(f"\n{'=' * 60}")
            print(f"PIPELINE FAILED: Phase {phase} failed with exit code {exit_code}")
            print(f"Completed phases: {', '.join(phases[:i])}")
            print(f"Failed phase: {phase}")
            print(f"Remaining phases: {', '.join(phases[i + 1 :])}")
            print(f"{'=' * 60}\n")
            return exit_code

        if debug:
            print(f"[DEBUG] Phase {phase} completed successfully")

    # Add completion summary for multi-phase runs
    if len(phases) > 1:
        print(f"\n{'=' * 60}")
        print(f"PIPELINE COMPLETE: {len(phases)} phases finished successfully")
        print(f"{'=' * 60}\n")

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
        "--month", help="Process specific month (YYYY-MM format, default: previous month)"
    )
    parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    parser.add_argument("--start", help="Start month for range (YYYY-MM format)")
    parser.add_argument("--end", help="End month for range (YYYY-MM format)")
    parser.add_argument("--range", help="Month range (YYYY-MM:YYYY-MM format)")
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

    args = parser.parse_args(argv)

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
        has_date_args = bool(args.month or args.year or args.start or args.end or args.range)

        if args.delta:
            # Delta mode: process current month(s) + historical comparison months
            delta_months = calculate_delta_months(args)
            if args.debug:
                print(
                    f"[DEBUG] Delta mode: processing {len(delta_months)} months: "
                    f"{', '.join(delta_months)}"
                )
            common_args.extend(["--delta-months", ",".join(delta_months)])
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
        if args.max_workers:
            common_args.extend(["--max-workers", str(args.max_workers)])

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
