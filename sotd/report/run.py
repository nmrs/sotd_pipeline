#!/usr/bin/env python3
"""
Generate statistical analysis reports from aggregated SOTD data.

CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--type hardware|software   → report type (default: hardware)
--data-root DIR            → root directory for all input data (default: data)
--out-dir DIR              → output directory for report file (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
"""

from pathlib import Path
from typing import Sequence

from sotd.utils.performance import PerformanceMonitor

from . import cli, load, process, save


def run_report(args) -> None:
    """Main report generation logic."""
    monitor = PerformanceMonitor("report")
    monitor.start_total_timing()
    if args.debug:
        print("[DEBUG] Report phase started")
        print(f"[DEBUG] Month: {args.month}")
        print(f"[DEBUG] Report type: {args.type}")
        print(f"[DEBUG] Data root: {args.data_root}")
        print(f"[DEBUG] Output directory: {args.out_dir}")
        print(f"[DEBUG] Force overwrite: {args.force}")

    # Parse month to get year and month
    try:
        year_str, month_str = args.month.split("-")
        year = int(year_str)
        month = int(month_str)
    except ValueError:
        raise ValueError(f"Invalid month format: {args.month}. Expected YYYY-MM format.")

    # Convert data root and output directory to Path
    data_root = Path(args.data_root)
    out_dir = Path(args.out_dir)

    # Load aggregated data (always from data_root/aggregated)
    if args.debug:
        print(f"[DEBUG] Loading aggregated data for {args.month}")
    try:
        monitor.start_file_io_timing()
        aggregated_file_path = load.get_aggregated_file_path(data_root, year, month)
        metadata, data = load.load_aggregated_data(aggregated_file_path, args.debug)
        monitor.end_file_io_timing()
    except FileNotFoundError as e:
        monitor.end_file_io_timing()
        raise FileNotFoundError(
            f"Aggregated data not found for {args.month}. "
            f"Run the aggregate phase first to generate the required data."
        ) from e
    except Exception as e:
        monitor.end_file_io_timing()
        raise RuntimeError(f"Failed to load aggregated data: {e}") from e

    # Load historical data for delta calculations (always from data_root/aggregated)
    if args.debug:
        print("[DEBUG] Loading historical data for delta calculations")
    try:
        monitor.start_file_io_timing()
        comparison_data = load.load_comparison_data(data_root, year, month, args.debug)
        monitor.end_file_io_timing()
        if args.debug:
            print(f"[DEBUG] Loaded {len(comparison_data)} comparison periods")
            for period, (period_meta, _) in comparison_data.items():
                print(f"[DEBUG] {period}: {period_meta['month']}")
    except Exception as e:
        monitor.end_file_io_timing()
        if args.debug:
            print(f"[DEBUG] Warning: Failed to load historical data: {e}")
        comparison_data = {}

    # Generate report content
    if args.debug:
        print(f"[DEBUG] Generating {args.type} report content")
    try:
        report_content = process.generate_report_content(
            args.type, metadata, data, comparison_data, args.debug
        )
    except Exception as e:
        raise RuntimeError(f"Failed to generate report content: {e}") from e

    # Save report to file (output always goes to out_dir)
    if args.debug:
        print("[DEBUG] Saving report to file")
    try:
        monitor.start_file_io_timing()
        output_path = save.generate_and_save_report(
            report_content, out_dir, year, month, args.type, args.force, args.debug
        )
        monitor.end_file_io_timing()
    except FileExistsError as e:
        monitor.end_file_io_timing()
        raise FileExistsError(f"Report file already exists. Use --force to overwrite: {e}") from e
    except Exception as e:
        monitor.end_file_io_timing()
        raise RuntimeError(f"Failed to save report: {e}") from e

    monitor.end_total_timing()
    if args.debug:
        monitor.print_summary()

    # Success message
    print(f"[INFO] Successfully generated {args.type} report for {args.month}")
    print(f"[INFO] Report saved to: {output_path}")


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the report phase."""
    try:
        parser = cli.get_parser()
        args = parser.parse_args(argv)
        cli.validate_args(args)
        run_report(args)
    except KeyboardInterrupt:
        print("\n[INFO] Report generation interrupted by user")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        # Note: args might not be defined if parse_report_args fails
        # We'll handle this in the exception handler


if __name__ == "__main__":
    main()
