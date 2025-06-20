"""
Pipeline orchestration entry-point.

This module provides a unified interface for running the SOTD pipeline phases.
Individual phases can be run separately or as part of a complete pipeline workflow.
"""

import argparse
import sys
from typing import List, Optional


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

        # Run the phase with provided arguments
        module.main(args)
        return 0

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

    for i, phase in enumerate(phases):
        if debug:
            print(f"\n[DEBUG] Running phase {i + 1}/{len(phases)}: {phase}")

        exit_code = run_phase(phase, args)
        if exit_code != 0:
            print(f"[ERROR] Phase {phase} failed with exit code {exit_code}")
            return exit_code

        if debug:
            print(f"[DEBUG] Phase {phase} completed successfully")

    if debug:
        print(f"\n[DEBUG] All {len(phases)} phases completed successfully")

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
  # Run individual phases
  python run.py fetch --month 2025-01
  python run.py extract --month 2025-01
  python run.py match --month 2025-01
  python run.py enrich --month 2025-01
  python run.py aggregate --month 2025-01
  python run.py report --month 2025-01 --type hardware
  
  # Run complete pipeline
  python run.py pipeline --month 2025-01
  
  # Run with debug logging
  python run.py pipeline --month 2025-01 --debug
  
  # Run specific phase range
  python run.py pipeline --month 2025-01 extract:enrich
  
  # Run single phase
  python run.py pipeline --month 2025-01 match
  
  # Run from phase to end
  python run.py pipeline --month 2025-01 match:
  
  # Run from beginning to phase
  python run.py pipeline --month 2025-01 :enrich
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Individual phase commands
    for phase in ["fetch", "extract", "match", "enrich", "aggregate", "report"]:
        phase_parser = subparsers.add_parser(
            phase,
            help=f"Run {phase} phase",
            description=f"Run the {phase} phase of the SOTD pipeline",
        )
        phase_parser.add_argument(
            "phase_args", nargs=argparse.REMAINDER, help=f"Arguments to pass to {phase} phase"
        )

    # Pipeline command
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run complete pipeline or phase subset",
        description="Run multiple pipeline phases in sequence",
    )

    # Phase range argument (optional, defaults to all phases)
    pipeline_parser.add_argument(
        "phase_range",
        nargs="?",
        default="",
        help="Phase range to run (e.g., extract:enrich, match:, :aggregate). Default: all phases",
    )

    # Common arguments for pipeline
    pipeline_parser.add_argument("--month", help="Process specific month (YYYY-MM format)")
    pipeline_parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    pipeline_parser.add_argument("--start-month", help="Start month for range (YYYY-MM format)")
    pipeline_parser.add_argument("--end-month", help="End month for range (YYYY-MM format)")
    pipeline_parser.add_argument("--range", help="Month range (YYYY-MM:YYYY-MM format)")
    pipeline_parser.add_argument(
        "--out-dir", default="data", help="Output directory (default: data)"
    )
    pipeline_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    pipeline_parser.add_argument(
        "--force", action="store_true", help="Force overwrite existing files"
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "pipeline":
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
            if args.month:
                common_args.extend(["--month", args.month])
            if args.year:
                common_args.extend(["--year", str(args.year)])
            if args.start_month:
                common_args.extend(["--start", args.start_month])
            if args.end_month:
                common_args.extend(["--end", args.end_month])
            if args.range:
                common_args.extend(["--range", args.range])
            if args.out_dir:
                common_args.extend(["--out-dir", args.out_dir])
            if args.debug:
                common_args.append("--debug")
            if args.force:
                common_args.append("--force")

            return run_pipeline(phases, common_args, debug=args.debug)

        else:
            # Individual phase
            phase_args = getattr(args, "phase_args", [])
            return run_phase(args.command, phase_args)

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
