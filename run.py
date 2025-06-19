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
        phase: Phase name (fetch, extract, match, enrich, aggregate)
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

Examples:
  # Run individual phases
  python run.py fetch --month 2025-01
  python run.py extract --month 2025-01
  python run.py match --month 2025-01
  python run.py enrich --month 2025-01
  python run.py aggregate --month 2025-01
  
  # Run complete pipeline
  python run.py pipeline --month 2025-01
  
  # Run with debug logging
  python run.py pipeline --month 2025-01 --debug
  
  # Run specific phase range
  python run.py pipeline --month 2025-01 --phases extract,match,enrich
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Individual phase commands
    for phase in ["fetch", "extract", "match", "enrich", "aggregate"]:
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

    # Pipeline arguments
    pipeline_parser.add_argument(
        "--phases",
        default="fetch,extract,match,enrich,aggregate",
        help="Comma-separated list of phases to run (default: all phases)",
    )

    # Common arguments for pipeline
    pipeline_parser.add_argument("--month", help="Process specific month (YYYY-MM format)")
    pipeline_parser.add_argument("--year", type=int, help="Process entire year (YYYY format)")
    pipeline_parser.add_argument("--start", help="Start month for range (YYYY-MM format)")
    pipeline_parser.add_argument("--end", help="End month for range (YYYY-MM format)")
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
            # Parse phases
            phases = [p.strip() for p in args.phases.split(",")]
            valid_phases = {"fetch", "extract", "match", "enrich", "aggregate"}

            invalid_phases = set(phases) - valid_phases
            if invalid_phases:
                print(f"[ERROR] Invalid phases: {', '.join(invalid_phases)}")
                print(f"[INFO] Valid phases: {', '.join(valid_phases)}")
                return 1

            # Build common arguments
            common_args = []
            if args.month:
                common_args.extend(["--month", args.month])
            if args.year:
                common_args.extend(["--year", str(args.year)])
            if args.start:
                common_args.extend(["--start", args.start])
            if args.end:
                common_args.extend(["--end", args.end])
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
