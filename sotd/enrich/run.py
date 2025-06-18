import argparse
from pathlib import Path
from typing import Optional, Sequence

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.enrich.enrich import enrich_comments
from sotd.enrich.save import calculate_enrichment_stats, load_matched_data, save_enriched_data


def _process_month(
    year: int, month: int, base_path: Path, debug: bool, force: bool
) -> Optional[dict]:
    """Process enrichment for a single month."""
    ym = f"{year:04d}-{month:02d}"
    in_path = base_path / "matched" / f"{year:04d}-{month:02d}.json"
    out_path = base_path / "enriched" / f"{year:04d}-{month:02d}.json"

    if not in_path.exists():
        if debug:
            print(f"Skipping missing input file: {in_path}")
        return None

    # Load matched data
    matched_result = load_matched_data(in_path)
    if matched_result is None:
        if debug:
            print(f"Failed to load matched data from: {in_path}")
        return None

    original_metadata, comments = matched_result

    # Extract original comment texts for enrichment
    original_comments = []
    for comment in comments:
        # Get the original comment text from the extracted field if available
        # This is the user's original input that we want to enrich from
        original_text = ""
        if "razor_extracted" in comment:
            original_text = comment["razor_extracted"]
        elif "blade_extracted" in comment:
            original_text = comment["blade_extracted"]
        elif "brush_extracted" in comment:
            original_text = comment["brush_extracted"]
        elif "soap_extracted" in comment:
            original_text = comment["soap_extracted"]
        original_comments.append(original_text)

    # Enrich the comments
    enriched_comments = enrich_comments(comments, original_comments)

    # Calculate enrichment statistics
    enrichment_stats = calculate_enrichment_stats(enriched_comments)

    # Save enriched data
    save_enriched_data(
        out_path, enriched_comments, original_metadata, enrichment_stats, force=force
    )

    if debug:
        print(f"Enriched {len(enriched_comments)} records for {ym}")
        print(f"  Blade enriched: {enrichment_stats['blade_enriched']}")
        print(f"  Razor enriched: {enrichment_stats['razor_enriched']}")
        print(f"  Brush enriched: {enrichment_stats['brush_enriched']}")
        print(f"  Soap enriched: {enrichment_stats['soap_enriched']}")

    return {
        "month": ym,
        "records_processed": len(enriched_comments),
        **enrichment_stats,
    }


def run(args: argparse.Namespace) -> None:
    """Run the enrich phase for the specified date range."""
    months = month_span(args)
    base_path = Path(args.out_dir)

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
    p = argparse.ArgumentParser(description="Enrich SOTD data with detailed specifications")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--month", type=str, help="e.g., 2025-04")
    g.add_argument("--year", type=int, help="e.g., 2025 (runs all months in that year)")
    g.add_argument("--range", type=str, help="Format: YYYY-MM:YYYY-MM (inclusive)")
    p.add_argument("--start", type=str, help="Optional: overrides start date (YYYY-MM)")
    p.add_argument("--end", type=str, help="Optional: overrides end date (YYYY-MM)")
    p.add_argument("--out-dir", default="data", help="Base directory for data files")
    p.add_argument("--debug", action="store_true", help="Enable debug output")
    p.add_argument("--force", action="store_true", help="Overwrite existing output files")
    args = p.parse_args(argv)

    run(args)


if __name__ == "__main__":
    main()
