from pathlib import Path

from sotd.utils.performance import PerformanceMonitor


def run_report(args) -> None:
    """Main report generation logic."""
    monitor = PerformanceMonitor("report")
    monitor.start_total_timing()

    # Determine which report types to generate
    if args.type == "all":
        report_types = ["hardware", "software"]
        print(f"Processing reports for {args.month} (both hardware and software)...")
    else:
        report_types = [args.type]
        print(f"Processing {args.type} report for {args.month}...")

    if args.debug:
        print("[DEBUG] Report phase started")
        print(f"[DEBUG] Month: {args.month}")
        print(f"[DEBUG] Report type: {args.type}")
        print(f"[DEBUG] Report types to generate: {report_types}")
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

    # Import modules needed for processing
    from . import load, process, save

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
        # Pass the aggregated directory since load_comparison_data expects the base
        # aggregated directory
        comparison_data = load.load_comparison_data(
            data_root / "aggregated", year, month, args.debug
        )
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

    # Generate reports for each type
    for report_type in report_types:
        if args.debug:
            print(f"[DEBUG] Generating {report_type} report content")
        
        # Check if output already exists and force is not set
        output_path = save.get_report_file_path(out_dir, year, month, report_type)
        if output_path.exists() and not args.force:
            print(f"  {args.month} {report_type}: output exists")
            continue

        try:
            report_content = process.generate_report_content(
                report_type, metadata, data, comparison_data, args.debug
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate {report_type} report content: {e}") from e

        # Save report to file (output always goes to out_dir)
        if args.debug:
            print(f"[DEBUG] Saving {report_type} report to file")
        try:
            monitor.start_file_io_timing()
            output_path = save.generate_and_save_report(
                report_content, out_dir, year, month, report_type, args.force, args.debug
            )
            monitor.end_file_io_timing()
            print(f"  {args.month} {report_type}: {output_path.name}")
        except Exception as e:
            monitor.end_file_io_timing()
            raise RuntimeError(f"Failed to save {report_type} report: {e}") from e

    # Show completion message
    if len(report_types) > 1:
        print(f"Generated {len(report_types)} reports for {args.month}")
    else:
        print(f"Generated {report_types[0]} report for {args.month}")

    # End timing and show performance summary
    monitor.end_total_timing()
    if args.debug:
        print("[DEBUG] Report generation completed")
        print("[DEBUG] Performance summary:")
        monitor.print_summary()
