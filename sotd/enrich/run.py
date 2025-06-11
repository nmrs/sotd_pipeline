import argparse
import json
import logging
import os

from sotd.cli_utils.date_span import _month_span
from sotd.enrich.brush_enricher import BrushEnricher

log = logging.getLogger(__name__)


def enrich_entry(record: dict, brush_enricher: BrushEnricher) -> dict:
    result = record.copy()
    brush = result.get("brush")
    if isinstance(brush, dict) and "original" in brush:
        enrichment = brush_enricher.enrich(brush["original"], brush.get("matched"))
        brush["enriched"] = enrichment
    return result


def _process_month(year: int, month: int, out_dir: str, force: bool, debug: bool) -> None:
    in_path = f"data/matched/{year:04d}-{month:02d}.json"
    out_path = f"{out_dir}/{year:04d}-{month:02d}.json"

    if not os.path.exists(in_path):
        if debug:
            log.debug(f"Skipping missing file: {in_path}")
        return

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(in_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    records = raw.get("data", [])

    brush_enricher = BrushEnricher()
    enriched = [enrich_entry(record, brush_enricher) for record in records]

    metadata = {
        "total_records": len(enriched),
        "brush_enriched": sum(
            1 for record in enriched if record.get("brush", {}).get("enriched") is not None
        ),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"metadata": metadata, "data": enriched},
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

    if debug:
        log.debug(f"Enriched {len(enriched)} records → {out_path}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Enrich matched SOTD records")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--month")
    group.add_argument("--year")
    group.add_argument("--range")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--out-dir", default="data/enriched")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    log.info("Enriching matched records...")

    for year, month in _month_span(args):
        _process_month(year, month, args.out_dir, args.force, args.debug)


if __name__ == "__main__":
    main()
