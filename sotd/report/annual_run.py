#!/usr/bin/env python3
"""
Annual report generation integration module.

This module wires together the annual report components to provide
a complete annual report generation workflow.
"""

import logging
from pathlib import Path
from typing import Sequence

from sotd.report.report_core import run_report  # Import run_report from new module
from sotd.utils.performance import PerformanceMonitor

from . import cli
from .annual_generator import generate_annual_report  # noqa: F401

logger = logging.getLogger(__name__)


def run_annual_report(args) -> None:
    """Main annual report generation logic with performance monitoring."""
    monitor = PerformanceMonitor("annual_run")
    monitor.start_total_timing()

    # Initialize variables to avoid linter errors
    years: list[str] = []
    years_successful = 0
    years_failed = 0
    total_report_size_chars = 0

    try:
        if args.debug:
            logger.info("Annual report phase started")
            print("[DEBUG] Annual report phase started")
            logger.info(f"Annual: {args.annual}")
            print(f"[DEBUG] Annual: {args.annual}")
            logger.info(f"Year: {args.year}")
            print(f"[DEBUG] Year: {args.year}")
            logger.info(f"Range: {args.range}")
            print(f"[DEBUG] Range: {args.range}")
            logger.info(f"Report type: {args.type}")
            print(f"[DEBUG] Report type: {args.type}")
            logger.info(f"Data root: {args.data_root}")
            print(f"[DEBUG] Data root: {args.data_root}")
            logger.info(f"Output directory: {args.out_dir}")
            print(f"[DEBUG] Output directory: {args.out_dir}")
            logger.info(f"Force overwrite: {args.force}")
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
            logger.info(f"Processing years: {years}")
            print(f"[DEBUG] Processing years: {years}")

        # Process each year in the range
        for year in years:
            if args.debug:
                logger.info(f"Generating annual {args.type} report for {year}")
                print(f"[DEBUG] Generating annual {args.type} report for {year}")

            try:
                # Generate annual report content
                report_content = generate_annual_report(
                    args.type, year, data_root, args.debug, None
                )
                total_report_size_chars += len(report_content)
            except FileNotFoundError as e:
                years_failed += 1
                print(
                    f"[ERROR] Annual data not found for {year}. "
                    f"Run the aggregate phase first with --annual --year {year} "
                    f"to generate the required data."
                )
                raise FileNotFoundError(
                    f"Annual data not found for {year}. "
                    f"Run the aggregate phase first with --annual --year {year} "
                    f"to generate the required data."
                ) from e
            except Exception as e:
                years_failed += 1
                print(f"[ERROR] Failed to generate annual report content: {e}")
                raise RuntimeError(f"Failed to generate annual report content: {e}") from e

            try:
                # Save report to file
                if args.debug:
                    logger.info(f"Saving annual report for {year}")
                    print(f"[DEBUG] Saving annual report for {year}")
                monitor.start_file_io_timing()
                output_path = save_annual_report(
                    report_content, out_dir, year, args.type, args.force, args.debug
                )
                monitor.end_file_io_timing()
                years_successful += 1
            except OSError:
                monitor.end_file_io_timing()
                years_failed += 1
                print(f"[ERROR] Failed to save annual report for {year}")
                raise
            except Exception as e:
                monitor.end_file_io_timing()
                years_failed += 1
                print(f"[ERROR] Failed to save annual report: {e}")
                raise RuntimeError(f"Failed to save annual report: {e}") from e

            # Success message for this year
            print(f"[INFO] Successfully generated {args.type} report for {year}")
            print(f"[INFO] Report saved to: {output_path}")
            logger.info(f"Successfully generated {args.type} report for {year}")
            logger.info(f"Report saved to: {output_path}")

        # Final success message
        if len(years) == 1:
            print(f"[INFO] Annual report generation completed for {years[0]}")
            logger.info(f"Annual report generation completed for {years[0]}")
        else:
            print(
                f"[INFO] Annual report generation completed for {len(years)} years: "
                f"{', '.join(years)}"
            )
            logger.info(
                f"Annual report generation completed for {len(years)} years: {', '.join(years)}"
            )

        # Update final metrics
        monitor.metrics.record_count = years_successful

    finally:
        monitor.end_total_timing()
        if args.debug:
            print("\n=== Annual Run Performance Summary ===")
            print(f"Total Processing Time: {monitor.metrics.total_processing_time:.2f}s")
            print(f"File I/O Time: {monitor.metrics.file_io_time:.2f}s")
            print(f"Years Processed: {len(years)}")
            print(f"Years Successful: {years_successful}")
            print(f"Years Failed: {years_failed}")
            print(f"Report Type: {args.type}")
            print(f"Total Report Size: {total_report_size_chars:,} characters")
            print(f"Peak Memory Usage: {monitor.metrics.peak_memory_mb:.1f}MB")


def save_annual_report(
    report_content: str,
    out_dir: Path,
    year: str,
    report_type: str,
    force: bool = False,
    debug: bool = False,
) -> Path:
    """Save annual report content to file with unified file I/O patterns.

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
        logger.info(f"Saving annual {report_type} report for {year}")
        print(f"[DEBUG] Saving annual {report_type} report for {year}")
        logger.info(f"Output directory: {out_dir}")
        print(f"[DEBUG] Output directory: {out_dir}")

    # Create output directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    output_filename = f"{year}-{report_type}.md"
    output_path = out_dir / output_filename

    if debug:
        logger.info(f"Output file: {output_path}")
        print(f"[DEBUG] Output file: {output_path}")

    # Check if file exists and handle force flag
    if output_path.exists() and not force:
        print(f"[ERROR] Report file already exists: {output_path}")
        raise FileExistsError(f"Report file already exists: {output_path}")

    # Write report content to file using unified file I/O
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
    except OSError as e:
        print(f"[ERROR] Failed to write report file {output_path}: {e}")
        raise OSError(f"Failed to write report file {output_path}: {e}") from e

    if debug:
        logger.info(f"Successfully saved report to: {output_path}")
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
        logger.info("Report generation interrupted by user")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        logger.error(f"Report generation failed: {e}")


if __name__ == "__main__":
    main()
