import logging
from pathlib import Path

from sotd.cli_utils.date_span import month_span
from sotd.utils.data_dir import get_data_dir
from sotd.utils.parallel_processor import create_parallel_processor
from sotd.utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)


def _process_month(
    year: int,
    month: int,
    data_root: Path,
    out_dir: Path,
    report_types: list[str],
    force: bool,
    debug: bool,
    delta: bool,
    output_format: str = "markdown",
) -> dict:
    """Process a single month for report generation."""
    month_str = f"{year:04d}-{month:02d}"

    if debug:
        logger.debug(f"Processing month: {month_str}")

    # Import modules needed for processing
    from . import load, process, save

    # Load aggregated data for this month
    if debug:
        logger.debug(f"Loading aggregated data for {month_str}")
    try:
        aggregated_file_path = load.get_aggregated_file_path(data_root, year, month)
        metadata, data = load.load_aggregated_data(aggregated_file_path, debug)
    except FileNotFoundError as e:
        return {
            "month": month_str,
            "status": "error",
            "error": f"Missing aggregated data file. Run aggregate phase first. ({e})",
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
        logger.debug(f"Loading historical data for {month_str}")
    try:
        comparison_data = load.load_comparison_data(data_root / "aggregated", year, month, debug)
        if debug:
            logger.debug(f"Loaded {len(comparison_data)} comparison periods for {month_str}")
    except Exception as e:
        if debug:
            logger.debug(f"Warning: Failed to load historical data for {month_str}: {e}")
        comparison_data = {}

    # Generate reports for each type
    reports_generated = 0
    for report_type in report_types:
        if debug:
            logger.debug(f"Generating {report_type} report for {month_str}")

        # Check if output already exists and force is not set
        # Check markdown file if markdown or both is requested
        should_check_markdown = output_format in ["markdown", "both"]
        should_check_json = output_format in ["json", "both"]

        skip_month = False
        if should_check_markdown:
            markdown_path = save.get_report_file_path(out_dir, year, month, report_type)
            if markdown_path.exists() and not force:
                if debug:
                    logger.debug(f"  {month_str} {report_type}: markdown output exists")
                if not should_check_json:
                    skip_month = True
        if should_check_json and not skip_month:
            json_path = save.get_json_report_file_path(out_dir, year, month, report_type)
            if json_path.exists() and not force:
                if debug:
                    logger.debug(f"  {month_str} {report_type}: JSON output exists")
                if not should_check_markdown:
                    skip_month = True

        if skip_month:
            continue

        # Create generator for both markdown and JSON generation
        # Construct template path from data_root (templates are in data_root/report_templates)
        template_path = str(data_root / "report_templates")
        generator = process.create_report_generator(
            report_type, metadata, data, comparison_data, debug, template_path
        )

        # Generate and save markdown if requested
        if output_format in ["markdown", "both"]:
            try:
                report_content = generator.generate_report()
            except Exception as e:
                # Fail fast: re-raise the exception with clear context
                error_msg = f"Failed to generate {report_type} markdown report for {month_str}: {e}"
                if debug:
                    logger.debug(error_msg)
                raise RuntimeError(error_msg) from e

            # Save markdown report to file
            if debug:
                logger.debug(f"Saving {report_type} markdown report for {month_str}")
            try:
                output_path = save.generate_and_save_report(
                    report_content, out_dir, year, month, report_type, force, debug
                )
                if debug:
                    logger.debug(f"  {month_str} {report_type}: {output_path.name}")
                reports_generated += 1
            except Exception as e:
                # Fail fast: re-raise the exception with clear context
                error_msg = f"Failed to save {report_type} markdown report for {month_str}: {e}"
                if debug:
                    logger.debug(error_msg)
                raise RuntimeError(error_msg) from e

        # Generate and save JSON if requested
        if output_format in ["json", "both"]:
            try:
                structured_data = generator.get_structured_data()
            except Exception as e:
                # Fail fast: re-raise the exception with clear context
                error_msg = f"Failed to generate {report_type} JSON report for {month_str}: {e}"
                if debug:
                    logger.debug(error_msg)
                raise RuntimeError(error_msg) from e

            # Save JSON report to file
            if debug:
                logger.debug(f"Saving {report_type} JSON report for {month_str}")
            try:
                output_path = save.generate_and_save_json_report(
                    structured_data, out_dir, year, month, report_type, force, debug
                )
                if debug:
                    logger.debug(f"  {month_str} {report_type}: {output_path.name}")
                reports_generated += 1
            except Exception as e:
                # Fail fast: re-raise the exception with clear context
                error_msg = f"Failed to save {report_type} JSON report for {month_str}: {e}"
                if debug:
                    logger.debug(error_msg)
                raise RuntimeError(error_msg) from e

    return {"month": month_str, "status": "success", "reports_generated": reports_generated}


def run_report(args) -> bool:
    """Main report generation logic."""
    monitor = PerformanceMonitor("report")
    monitor.start_total_timing()

    # Determine which report types to generate
    if args.type == "all":
        report_types = ["hardware", "software"]
        logger.info("Processing reports for date range (both hardware and software)...")
    else:
        report_types = [args.type]
        logger.info(f"Processing {args.type} reports for date range...")

    if args.debug:
        logger.debug("Report phase started")
        logger.debug(f"Report type: {args.type}")
        logger.debug(f"Report types to generate: {report_types}")
        logger.debug(f"Output directory: {args.data_dir}")
        logger.debug(f"Output format: {args.format}")
        logger.debug(f"Force overwrite: {args.force}")

    # Convert output directory to Path
    # For consistency with other phases, use data_dir for both input (aggregated data) and output (reports)
    # (Other phases: match reads from data_dir/extracted/, writes to data_dir/matched/)
    out_dir = get_data_dir(args.data_dir)
    data_root = out_dir  # Use data_dir for reading aggregated data, consistent with other phases

    # Get months to process using month_span
    try:
        month_tuples = month_span(args)
        months = [f"{year:04d}-{month:02d}" for year, month in month_tuples]
        if args.debug:
            logger.debug(f"Processing months: {months}")
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
            args.format,
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
            args.format,
        )
        results = processor.process_months_sequential(
            month_tuples, _process_month, process_args, "Months"
        )

    # Filter results and check for errors
    valid_results = [r for r in results if r is not None]
    errors = [r for r in valid_results if "error" in r]
    skipped = [r for r in valid_results if r.get("status") == "skipped"]
    successful = [r for r in valid_results if r.get("status") == "success"]

    # Display error details for failed months
    if errors:
        logger.error("\n❌ Error Details:")
        for error_result in errors:
            month = error_result.get("month", "unknown")
            error_msg = error_result.get("error", "unknown error")
            logger.error(f"  {month}: {error_msg}")

    if skipped:
        logger.warning("\n⚠️  Skipped Months:")
        for skipped_result in skipped:
            month = skipped_result.get("month", "unknown")
            reason = skipped_result.get("reason", "unknown reason")
            logger.warning(f"  {month}: {reason}")

    # Show completion message
    total_reports_generated = sum(r.get("reports_generated", 0) for r in successful)
    if total_reports_generated > 0:
        logger.info(f"Generated {total_reports_generated} reports across {len(successful)} months")
    elif not errors and not skipped:
        logger.info("No reports were generated")

    # End timing and show performance summary
    monitor.end_total_timing()
    if args.debug:
        logger.debug("Report generation completed")
        logger.debug("Performance summary:")
        monitor.print_summary()

    # Return True if there were errors, False otherwise
    return len(errors) > 0
