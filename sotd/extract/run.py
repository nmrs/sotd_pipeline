import logging
from pathlib import Path
from typing import Optional, Sequence

from sotd.cli_utils.date_span import month_span
from sotd.utils.parallel_processor import create_parallel_processor
from sotd.utils.performance import PerformanceMonitor, PipelineOutputFormatter

from .cli import get_parser
from .comment import run_extraction_for_month
from .override_manager import OverrideManager
from .save import save_month_file

logger = logging.getLogger()
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


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
            logging.warning("Skipped missing input file: %s/comments/%s.json", base_path, ym)
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
    base_path = Path(args.out_dir)

    # Initialize override manager if override file is specified
    override_manager = None
    if hasattr(args, 'override_file') and args.override_file:
        try:
            override_manager = OverrideManager(args.override_file)
            override_manager.load_overrides()
            if override_manager.has_overrides():
                logger.info("Loaded overrides from: %s", args.override_file)
            else:
                logger.info("No overrides found in: %s", args.override_file)
        except Exception as e:
            logger.error("Failed to load overrides from %s: %s", args.override_file, e)
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
            print(summary)
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
        print(summary)


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the extract phase."""
    try:
        parser = get_parser()
        args = parser.parse_args(argv)
        run(args)
        return 0  # Success
    except KeyboardInterrupt:
        print("\n[INFO] Extract phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        print(f"[ERROR] Extract phase failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
