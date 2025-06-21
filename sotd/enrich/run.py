import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.enrich.cli import get_parser
from sotd.enrich.enrich import enrich_comments, setup_enrichers
from sotd.enrich.save import calculate_enrichment_stats, load_matched_data, save_enriched_data
from sotd.utils.performance import PerformanceMonitor


def _process_month(
    year: int, month: int, base_path: Path, debug: bool, force: bool
) -> Optional[dict]:
    """Process enrichment for a single month."""
    ym = f"{year:04d}-{month:02d}"
    monitor = PerformanceMonitor("enrich")
    monitor.start_total_timing()
    in_path = base_path / "matched" / f"{year:04d}-{month:02d}.json"
    out_path = base_path / "enriched" / f"{year:04d}-{month:02d}.json"

    if not in_path.exists():
        if debug:
            print(f"Skipping missing input file: {in_path}")
        return None

    monitor.start_file_io_timing()
    try:
        original_metadata, comments = load_matched_data(in_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as e:
        monitor.end_file_io_timing()
        if debug:
            print(f"Failed to load matched data from {in_path}: {e}")
        return None
    monitor.end_file_io_timing()

    # Extract original comment texts for enrichment - optimized version
    original_comments = []
    for comment in comments:
        # Get the original comment text from the extracted field if available
        # This is the user's original input that we want to enrich from
        original_text = (
            comment.get("razor_extracted")
            or comment.get("blade_extracted")
            or comment.get("brush_extracted")
            or comment.get("soap_extracted")
            or ""
        )
        original_comments.append(original_text)

    # Enrich the comments
    enriched_comments = enrich_comments(comments, original_comments)

    # Calculate enrichment statistics
    enrichment_stats = calculate_enrichment_stats(enriched_comments)

    monitor.set_record_count(len(enriched_comments))
    monitor.set_file_sizes(in_path, out_path)

    monitor.start_file_io_timing()
    save_enriched_data(
        out_path, enriched_comments, original_metadata, enrichment_stats, force=force
    )
    monitor.end_file_io_timing()
    monitor.end_total_timing()

    if debug:
        monitor.print_summary()
        print(f"Enriched {len(enriched_comments)} records for {ym}")
        print(f"  Blade enriched: {enrichment_stats['blade_enriched']}")
        print(f"  Razor enriched: {enrichment_stats['razor_enriched']}")
        print(f"  Brush enriched: {enrichment_stats['brush_enriched']}")
        print(f"  Soap enriched: {enrichment_stats['soap_enriched']}")

    return {
        "month": ym,
        "records_processed": len(enriched_comments),
        **enrichment_stats,
        "performance": monitor.get_summary(),
    }


def run(args: argparse.Namespace) -> None:
    """Run the enrich phase for the specified date range."""
    months = month_span(args)
    base_path = Path(args.out_dir)

    # Set up enrichers once at the start - this is a major performance optimization
    setup_enrichers()

    results = []
    for year, month in tqdm(months, desc="Enriching months", unit="month"):
        result = _process_month(year, month, base_path, debug=args.debug, force=args.force)
        if result:
            results.append(result)

    if args.debug and results:
        print("\nEnrichment Summary:")
        total_records = sum(r["records_processed"] for r in results)
        total_enriched = sum(r["total_enriched"] for r in results)
        print(f"  Total records processed: {total_records}")
        print(f"  Total records enriched: {total_enriched}")


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point for the enrich phase."""
    parser = get_parser()
    args = parser.parse_args(argv)

    run(args)


if __name__ == "__main__":
    main()
