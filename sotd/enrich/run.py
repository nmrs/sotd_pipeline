import argparse
import json
import os
import logging

from sotd.cli_utils.date_span import _month_span
from sotd.enrich.enrich import enrich_entry

log = logging.getLogger(__name__)


def _process_month(year: int, month: int, out_dir: str, force: bool, debug: bool) -> None:
    in_path = f"data/extracted/{year:04d}-{month:02d}.json"
    out_path = f"{out_dir}/{year:04d}-{month:02d}.json"

    if not os.path.exists(in_path):
        if debug:
            log.debug(f"Skipping missing file: {in_path}")
        return

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(in_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    records = raw.get("data", [])

    enriched = [enrich_entry(record) for record in records]

    metadata = {}
    metadata["total_records"] = len(enriched)
    metadata["blade_enriched"] = sum(
        1 for record in enriched if record.get("blade_use") is not None
    )
    metadata["brush_enriched"] = sum(
        1
        for record in enriched
        if record.get("brush_fiber") is not None or record.get("brush_knot_mm") is not None
    )

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
    # Note: Ensure logging is configured appropriately when running this CLI.
    parser = argparse.ArgumentParser(description="Enrich extracted SOTD records")
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

    log.info("Enriching SOTD records...")

    for year, month in _month_span(args):
        _process_month(year, month, args.out_dir, args.force, args.debug)


if __name__ == "__main__":
    main()
