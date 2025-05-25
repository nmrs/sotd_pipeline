import argparse
from pathlib import Path
from typing import Sequence, Optional
from warnings import warn
import logging

logger = logging.getLogger()
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
from sotd.cli_utils.date_span import _month_span

from .comment import run_extraction_for_month
from .save import save_month_file


def _process_month(
    year: int, month: int, base_path: Path, force: bool, debug: bool
) -> Optional[dict]:
    ym = f"{year:04d}-{month:02d}"
    all_comments = run_extraction_for_month(ym, base_path=str(base_path))
    if all_comments is None:
        if debug:
            logging.warning(f"Skipped missing input file: {base_path}/comments/{ym}.json")
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
    if debug:
        logging.debug(f"Saving extraction result to: {base_path}/extracted/{ym}.json")
    save_month_file(month=ym, result=result, out_dir=base_path / "extracted")
    return result


def run(args: argparse.Namespace) -> None:
    months = _month_span(args)
    base_path = Path(args.out_dir)

    for year, month in months:
        _process_month(year, month, base_path, force=args.force, debug=args.debug)


def main(argv: Sequence[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Extract SOTD data")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--month")
    g.add_argument("--year")
    g.add_argument("--range")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--out-dir", default="data")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    run(args)


if __name__ == "__main__":
    main()
