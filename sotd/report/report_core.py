from pathlib import Path

from sotd.cli_utils.date_span import month_span
from sotd.utils.parallel_processor import create_parallel_processor
from sotd.utils.performance import PerformanceMonitor


def _process_month(
    year: int,
    month: int,
    data_root: Path,
    out_dir: Path,
    report_types: list[str],
    force: bool,
    debug: bool,
    delta: bool,
) -> dict:
    """Process a single month for report generation."""
    month_str = f"{year:04d}-{month:02d}"

    if debug:
        print(f"[DEBUG] Processing month: {month_str}")

    # Import modules needed for processing
    from . import load, process, save

    # Load aggregated data for this month
    if debug:
        print(f"[DEBUG] Loading aggregated data for {month_str}")
    try:
        aggregated_file_path = load.get_aggregated_file_path(data_root, year, month)
        metadata, data = load.load_aggregated_data(aggregated_file_path, debug)
    except FileNotFoundError:
        return {
            "month": month_str,
            "status": "skipped",
            "reason": "aggregated data not found",
            "reports_generated": 0,
        }
    except Exception as e:
        return {
            "month": month_str,
            "status": "error",
            "error": f"failed to load aggregated data: {e}",
            "reports_generated": 0,
        }

    # Load historical data for delta calculations
    if debug:
        print(f"[DEBUG] Loading historical data for {month_str}")
    try:
        comparison_data = load.load_comparison_data(data_root / "aggregated", year, month, debug)
        if debug:
            print(f"[DEBUG] Loaded {len(comparison_data)} comparison periods for {month_str}")
    except Exception as e:
        if debug:
            print(f"[DEBUG] Warning: Failed to load historical data for {month_str}: {e}")
        comparison_data = {}

    # Generate reports for each type
    reports_generated = 0
    for report_type in report_types:
        if debug:
            print(f"[DEBUG] Generating {report_type} report for {month_str}")

        # Check if output already exists and force is not set
        output_path = save.get_report_file_path(out_dir, year, month, report_type)
        if output_path.exists() and not force:
            if debug:
                print(f"  {month_str} {report_type}: output exists")
            continue

        try:
            report_content = process.generate_report_content(
                report_type, metadata, data, comparison_data, debug
            )
        except Exception as e:
            if debug:
                print(f"  {month_str} {report_type}: failed to generate content: {e}")
            continue

        # Save report to file
        if debug:
            print(f"[DEBUG] Saving {report_type} report for {month_str}")
        try:
            output_path = save.generate_and_save_report(
                report_content, out_dir, year, month, report_type, force, debug
            )
            if debug:
                print(f"  {month_str} {report_type}: {output_path.name}")
            reports_generated += 1
        except Exception as e:
            if debug:
                print(f"  {month_str} {report_type}: failed to save: {e}")
            continue

    return {"month": month_str, "status": "success", "reports_generated": reports_generated}


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

    # Get months to process using month_span
    try:
        month_tuples = month_span(args)
        months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]
        if args.debug:
            print(f"[DEBUG] Processing months: {months}")
    except ValueError as e:
        raise ValueError(f"Invalid date specification: {e}")

    # Create parallel processor for report phase
    processor = create_parallel_processor("report")

    # Determine if we should use parallel processing
    use_parallel = processor.should_use_parallel(month_tuples, args, args.debug)

    if use_parallel:
        # Get max workers for parallel processing
        max_workers = processor.get_max_workers(month_tuples, args, default=8)

        # Process months in parallel
        process_args = (
            data_root,
            out_dir,
            report_types,
            args.force,
            args.debug,
            getattr(args, "delta", False),
        )
        results = processor.process_months_parallel(
            month_tuples, _process_month, process_args, max_workers, "Processing"
        )

        # Print parallel processing summary
        processor.print_parallel_summary(results, "report")

    else:
        # Process months sequentially
        process_args = (
            data_root,
            out_dir,
            report_types,
            args.force,
            args.debug,
            getattr(args, "delta", False),
        )
        results = processor.process_months_sequential(
            month_tuples, _process_month, process_args, "Months"
        )

    # Process results and show completion message
    total_reports_generated = 0
    successful_months = 0

    for result in results:
        if result and result.get("status") == "success":
            total_reports_generated += result["reports_generated"]
            successful_months += 1
        elif result and result.get("status") == "skipped":
            print(f"  {result['month']}: {result['reason']}")
        elif result and result.get("status") == "error":
            print(f"  {result['month']}: {result['error']}")

    # Show completion message
    if total_reports_generated > 0:
        print(f"Generated {total_reports_generated} reports across {successful_months} months")
    else:
        print("No reports were generated")

    # End timing and show performance summary
    monitor.end_total_timing()
    if args.debug:
        print("[DEBUG] Report generation completed")
        print("[DEBUG] Performance summary:")
        monitor.print_summary()
