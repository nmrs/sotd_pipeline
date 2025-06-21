import logging
from pathlib import Path
from typing import Optional, Sequence

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.utils.performance import PerformanceMonitor, PipelineOutputFormatter

from .cli import get_parser
from .comment import run_extraction_for_month
from .save import save_month_file

logger = logging.getLogger()
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _process_month(
    year: int, month: int, base_path: Path, debug: bool, force: bool
) -> Optional[dict]:
    ym = f"{year:04d}-{month:02d}"
    monitor = PerformanceMonitor("extract")
    monitor.start_total_timing()

    monitor.start_file_io_timing()
    all_comments = run_extraction_for_month(ym, base_path=str(base_path))
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
    if debug:
        logging.debug("Saving extraction result to: %s", out_path)
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

    # Show progress bar for processing
    print(f"Processing {len(months)} month{'s' if len(months) != 1 else ''}...")

    results = []
    for year, month in tqdm(months, desc="Months", unit="month"):
        result = _process_month(year, month, base_path, debug=args.debug, force=args.force)
        if result:
            results.append(
                {
                    "month": f"{year:04d}-{month:02d}",
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
        if results:
            stats = results[0]
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
            "total_records": sum(r["shave_count"] for r in results),
            "total_missing": sum(r["missing_count"] for r in results),
            "total_skipped": sum(r["skipped_count"] for r in results),
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
