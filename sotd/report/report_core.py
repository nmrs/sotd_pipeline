from pathlib import Path

from sotd.cli_utils.date_span import month_span
from sotd.utils.performance import PerformanceMonitor


def run_report(args) -> None:
    """Main report generation logic."""
    monitor = PerformanceMonitor("report")
    monitor.start_total_timing()

    # Determine which report types to generate
    if args.type == "all":
        report_types = ["hardware", "software"]
        print("Processing reports for date range (both hardware and software)...")
    else:
        report_types = [args.type]
        print(f"Processing {args.type} reports for date range...")

    if args.debug:
        print("[DEBUG] Report phase started")
        print(f"[DEBUG] Report type: {args.type}")
        print(f"[DEBUG] Report types to generate: {report_types}")
        print(f"[DEBUG] Data root: {args.data_root}")
        print(f"[DEBUG] Output directory: {args.out_dir}")
        print(f"[DEBUG] Force overwrite: {args.force}")

    # Convert data root and output directory to Path
    data_root = Path(args.data_root)
    out_dir = Path(args.out_dir)

    # Import modules needed for processing
    from . import load, process, save

    # Get months to process using month_span
    try:
        month_tuples = month_span(args)
        months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]
        if args.debug:
            print(f"[DEBUG] Processing months: {months}")
    except ValueError as e:
        raise ValueError(f"Invalid date specification: {e}")

    # Process each month
    total_reports_generated = 0
    for month in months:
        if args.debug:
            print(f"[DEBUG] Processing month: {month}")
        
        # Parse month to get year and month
        try:
            year_str, month_str = month.split("-")
            year = int(year_str)
            month_int = int(month_str)
        except ValueError:
            raise ValueError(f"Invalid month format: {month}. Expected YYYY-MM format.")

        # Load aggregated data for this month
        if args.debug:
            print(f"[DEBUG] Loading aggregated data for {month}")
        try:
            monitor.start_file_io_timing()
            aggregated_file_path = load.get_aggregated_file_path(data_root, year, month_int)
            metadata, data = load.load_aggregated_data(aggregated_file_path, args.debug)
            monitor.end_file_io_timing()
        except FileNotFoundError:
            monitor.end_file_io_timing()
            print(f"  {month}: aggregated data not found, skipping")
            continue
        except Exception as e:
            monitor.end_file_io_timing()
            print(f"  {month}: failed to load aggregated data: {e}")
            continue

        # Load historical data for delta calculations
        if args.debug:
            print(f"[DEBUG] Loading historical data for {month}")
        try:
            monitor.start_file_io_timing()
            comparison_data = load.load_comparison_data(
                data_root / "aggregated", year, month_int, args.debug
            )
            monitor.end_file_io_timing()
            if args.debug:
                print(f"[DEBUG] Loaded {len(comparison_data)} comparison periods for {month}")
        except Exception as e:
            monitor.end_file_io_timing()
            if args.debug:
                print(f"[DEBUG] Warning: Failed to load historical data for {month}: {e}")
            comparison_data = {}

        # Generate reports for each type
        for report_type in report_types:
            if args.debug:
                print(f"[DEBUG] Generating {report_type} report for {month}")
            
            # Check if output already exists and force is not set
            output_path = save.get_report_file_path(out_dir, year, month_int, report_type)
            if output_path.exists() and not args.force:
                print(f"  {month} {report_type}: output exists")
                continue

            try:
                report_content = process.generate_report_content(
                    report_type, metadata, data, comparison_data, args.debug
                )
            except Exception as e:
                print(f"  {month} {report_type}: failed to generate content: {e}")
                continue

            # Save report to file
            if args.debug:
                print(f"[DEBUG] Saving {report_type} report for {month}")
            try:
                monitor.start_file_io_timing()
                output_path = save.generate_and_save_report(
                    report_content, out_dir, year, month_int, report_type, args.force, args.debug
                )
                monitor.end_file_io_timing()
                print(f"  {month} {report_type}: {output_path.name}")
                total_reports_generated += 1
            except Exception as e:
                monitor.end_file_io_timing()
                print(f"  {month} {report_type}: failed to save: {e}")
                continue

    # Show completion message
    if total_reports_generated > 0:
        print(f"Generated {total_reports_generated} reports across {len(months)} months")
    else:
        print("No reports were generated")

    # End timing and show performance summary
    monitor.end_total_timing()
    if args.debug:
        print("[DEBUG] Report generation completed")
        print("[DEBUG] Performance summary:")
        monitor.print_summary()
