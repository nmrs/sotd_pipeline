#!/usr/bin/env python3
"""
Annual report generation integration module.

This module wires together the annual report components to provide
a complete annual report generation workflow.
"""

from pathlib import Path
from typing import Sequence

from sotd.report.report_core import run_report  # Import run_report from new module
from sotd.utils.performance import PerformanceMonitor

from . import cli
from .annual_generator import generate_annual_report  # noqa: F401


def run_annual_report(args) -> None:
    """Main annual report generation logic."""
    monitor = PerformanceMonitor("annual_report")
    monitor.start_total_timing()
    if args.debug:
        print("[DEBUG] Annual report phase started")
        print(f"[DEBUG] Annual: {args.annual}")
        print(f"[DEBUG] Year: {args.year}")
        print(f"[DEBUG] Range: {args.range}")
        print(f"[DEBUG] Report type: {args.type}")
        print(f"[DEBUG] Data root: {args.data_root}")
        print(f"[DEBUG] Output directory: {args.out_dir}")
        print(f"[DEBUG] Force overwrite: {args.force}")

    # Convert data root and output directory to Path
    data_root = Path(args.data_root)
    out_dir = Path(args.out_dir)

    # Determine years to process
    if args.year:
        years = [args.year]
    elif args.range:
        # Parse year range for annual mode
        start_year, end_year = args.range.split(":")
        start_year_int, end_year_int = int(start_year), int(end_year)
        # Ensure start_year <= end_year for proper range generation
        actual_start = min(start_year_int, end_year_int)
        actual_end = max(start_year_int, end_year_int)
        years = [str(year) for year in range(actual_start, actual_end + 1)]
    else:
        raise ValueError("Annual reports require either --year or --range")

    if args.debug:
        print(f"[DEBUG] Processing years: {years}")

    # Process each year in the range
    for year in years:
        if args.debug:
            print(f"[DEBUG] Generating annual {args.type} report for {year}")

        try:
            # Generate annual report content
            report_content = generate_annual_report(args.type, year, data_root, args.debug, None)
        except FileNotFoundError as e:
            monitor.end_file_io_timing()
            raise FileNotFoundError(
                f"Annual data not found for {year}. "
                f"Run the aggregate phase first with --annual --year {year} "
                f"to generate the required data."
            ) from e
        except Exception as e:
            monitor.end_file_io_timing()
            raise RuntimeError(f"Failed to generate annual report content: {e}") from e

        try:
            # Save report to file
            if args.debug:
                print(f"[DEBUG] Saving annual report for {year}")
            monitor.start_file_io_timing()
            output_path = save_annual_report(
                report_content, out_dir, year, args.type, args.force, args.debug
            )
            monitor.end_file_io_timing()
        except OSError:
            monitor.end_file_io_timing()
            raise
        except Exception as e:
            monitor.end_file_io_timing()
            raise RuntimeError(f"Failed to save annual report: {e}") from e

        # Success message for this year
        print(f"[INFO] Successfully generated {args.type} report for {year}")
        print(f"[INFO] Report saved to: {output_path}")

    monitor.end_total_timing()
    if args.debug:
        monitor.print_summary()

    # Final success message
    if len(years) == 1:
        print(f"[INFO] Annual report generation completed for {years[0]}")
    else:
        print(
            f"[INFO] Annual report generation completed for {len(years)} years: {', '.join(years)}"
        )


def save_annual_report(
    report_content: str,
    out_dir: Path,
    year: str,
    report_type: str,
    force: bool = False,
    debug: bool = False,
) -> Path:
    """Save annual report content to file.

    Args:
        report_content: The report content to save
        out_dir: Output directory for the report file
        year: Year for the report (YYYY format)
        report_type: Type of report ('hardware' or 'software')
        force: Whether to force overwrite existing files
        debug: Enable debug logging

    Returns:
        Path to the saved report file

    Raises:
        FileExistsError: If file exists and force=False
        OSError: If there are file system errors
    """
    if debug:
        print(f"[DEBUG] Saving annual {report_type} report for {year}")
        print(f"[DEBUG] Output directory: {out_dir}")

    # Create output directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    output_filename = f"{year}-{report_type}.md"
    output_path = out_dir / output_filename

    if debug:
        print(f"[DEBUG] Output file: {output_path}")

    # Check if file exists and handle force flag
    if output_path.exists() and not force:
        raise FileExistsError(f"Report file already exists: {output_path}")

    # Write report content to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
    except OSError as e:
        raise OSError(f"Failed to write report file {output_path}: {e}") from e

    if debug:
        print(f"[DEBUG] Successfully saved report to: {output_path}")

    return output_path


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the annual report phase."""
    try:
        parser = cli.get_parser()
        args = parser.parse_args(argv)
        cli.validate_args(args)

        # Route to appropriate function based on annual flag
        if args.annual:
            run_annual_report(args)
        else:
            run_report(args)
    except KeyboardInterrupt:
        print("\n[INFO] Report generation interrupted by user")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")


if __name__ == "__main__":
    main()
