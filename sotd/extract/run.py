import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from sotd.cli_utils.date_span import month_span
from sotd.utils.data_dir import get_data_dir
from sotd.utils.logging_config import setup_pipeline_logging
from sotd.utils.parallel_processor import create_parallel_processor
from sotd.utils.performance import PerformanceMonitor, PipelineOutputFormatter

from .cli import get_parser
from .comment import run_extraction_for_month
from .override_manager import OverrideManager
from .save import save_month_file

logger = logging.getLogger(__name__)


def _process_month(
    year: int,
    month: int,
    base_path: Path,
    debug: bool,
    force: bool,
    override_manager: Optional[OverrideManager] = None,
) -> Optional[dict]:
    ym = f"{year:04d}-{month:02d}"
    monitor = PerformanceMonitor("extract")
    monitor.start_total_timing()

    monitor.start_file_io_timing()
    all_comments = run_extraction_for_month(
        ym, base_path=str(base_path), override_manager=override_manager
    )
    monitor.end_file_io_timing()
    if all_comments is None:
        if debug:
            logger.warning("Skipped missing input file: %s/comments/%s.json", base_path, ym)
        return None

    extracted = []
    missing = []
    skipped = []

    for c in all_comments.get("data", []):
        has_field = any(k in c for k in ("razor", "blade", "brush", "soap"))
        if has_field:
            extracted.append(c)
        else:
            missing.append(c)

    skipped = all_comments.get("skipped", [])

    result = {
        "meta": {
            "month": ym,
            "extracted_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            "shave_count": len(extracted),
            "missing_count": len(missing),
            "skipped_count": len(skipped),
        },
        "data": extracted,
        "missing": missing,
        "skipped": skipped,
    }
    out_path = base_path / "extracted" / f"{year:04d}-{month:02d}.json"
    monitor.set_record_count(len(extracted))
    monitor.set_file_sizes(base_path / "comments" / f"{ym}.json", out_path)
    if force and out_path.exists():
        out_path.unlink()
    monitor.start_file_io_timing()
    save_month_file(month=ym, result=result, out_dir=base_path / "extracted")
    monitor.end_file_io_timing()
    monitor.end_total_timing()
    if debug:
        monitor.print_summary()
    return result


def run(args) -> None:
    """Run the extract phase with the given arguments."""
    months = list(month_span(args))
    base_path = get_data_dir(args.data_dir)

    # Override file is always relative to data directory
    override_file_path = base_path / "extract_overrides.yaml"

    # Initialize override manager
    override_manager = None
    try:
        override_manager = OverrideManager(override_file_path)
        override_manager.load_overrides()
        if override_manager.has_overrides():
            logger.debug("Loaded overrides from: %s", override_file_path)
        else:
            logger.debug("No overrides found in: %s", override_file_path)
    except Exception as e:
        error_msg = f"Failed to load overrides from {override_file_path}: {e}"
        logger.error(error_msg)
        if args.debug:
            import traceback

            logger.error("Full traceback:\n%s", traceback.format_exc())
        raise

    # Create parallel processor for extract phase
    processor = create_parallel_processor("extract")

    # Determine if we should use parallel processing
    use_parallel = processor.should_use_parallel(months, args, args.debug)

    if use_parallel:
        # Get max workers for parallel processing
        max_workers = processor.get_max_workers(months, args, default=8)

        # Process months in parallel
        results = processor.process_months_parallel(
            months,
            _process_month,
            (base_path, args.debug, args.force, override_manager),
            max_workers,
            "Processing",
        )

        # Print parallel processing summary
        processor.print_parallel_summary(results, "extract")

    else:
        # Process months sequentially
        results = processor.process_months_sequential(
            months, _process_month, (base_path, args.debug, args.force, override_manager), "Months"
        )

    # Convert results to expected format for summary
    summary_results = []
    for result in results:
        if "error" not in result and result:
            summary_results.append(
                {
                    "month": result["meta"]["month"],
                    "shave_count": result["meta"]["shave_count"],
                    "missing_count": result["meta"]["missing_count"],
                    "skipped_count": result["meta"]["skipped_count"],
                }
            )

    # Print summary using standardized formatter
    if len(months) == 1:
        # Single month summary
        year, month = months[0]
        month_str = f"{year:04d}-{month:02d}"
        if summary_results:
            stats = summary_results[0]
            summary = PipelineOutputFormatter.format_single_month_summary(
                "extract", month_str, stats
            )
            logger.info(summary)
    else:
        # Multi-month summary
        start_year, start_month = months[0]
        end_year, end_month = months[-1]
        start_str = f"{start_year:04d}-{start_month:02d}"
        end_str = f"{end_year:04d}-{end_month:02d}"

        total_stats = {
            "total_records": sum(r["shave_count"] for r in summary_results),
            "total_missing": sum(r["missing_count"] for r in summary_results),
            "total_skipped": sum(r["missing_count"] for r in summary_results),
        }
        summary = PipelineOutputFormatter.format_multi_month_summary(
            "extract", start_str, end_str, total_stats
        )
        logger.info(summary)


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the extract phase."""
    # Setup logging with timestamp format matching shell script
    setup_pipeline_logging(level=logging.INFO)

    try:
        parser = get_parser()
        args = parser.parse_args(argv)

        # Update logging level if debug is enabled
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        run(args)
        return 0  # Success
    except KeyboardInterrupt:
        logger.info("Extract phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        error_msg = f"Extract phase failed: {e}"
        logger.error(error_msg)
        # Show more context for ValueError (validation errors)
        if isinstance(e, ValueError):
            logger.error(f"Details: {type(e).__name__}: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
