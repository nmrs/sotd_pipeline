from __future__ import annotations

# ruff: noqa: E402

"""
Phase-1 CLI: fetch threads & comments, merge, save, with overrides and a tqdm
progress bar during comment collection.
"""

import argparse
import calendar
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

from tqdm import tqdm  # progress bar

from sotd.fetch.merge import merge_records
from sotd.fetch.reddit import (
    fetch_top_level_comments,
    get_reddit,
    search_threads,
)
from sotd.fetch.save import load_month_file, write_month_file
from sotd.utils import parse_thread_date


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
def _parse_month(value: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(value, "%Y-%m")
        return dt.year, dt.month
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Month must be YYYY-MM") from exc


def _calc_missing(year: int, month: int, threads) -> list[_date]:
    last_day = calendar.monthrange(year, month)[1]
    expected: Set[_date] = {_date(year, month, d) for d in range(1, last_day + 1)}
    present: Set[_date] = {
        d for t in threads if (d := parse_thread_date(t.title, year)) is not None
    }
    return sorted(expected - present)


# --------------------------------------------------------------------------- #
# main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> None:
    p = argparse.ArgumentParser(description="Fetch & persist SOTD threads + comments")
    p.add_argument("--month", required=True, type=_parse_month)
    p.add_argument("--out-dir", default="data")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    year, month = args.month
    reddit = get_reddit()

    # --------- search + date-filter ---------------------------------------- #
    threads = search_threads("wetshaving", year, month, debug=args.debug)

    # --------- include / exclude overrides --------------------------------- #
    from sotd.fetch.overrides import apply_overrides, load_overrides

    inc, exc = load_overrides()
    if inc or exc:
        threads = apply_overrides(
            threads,
            inc,
            exc,
            reddit=reddit,
            year=year,
            month=month,
            debug=args.debug,
        )
        if args.debug:
            print(f"[DEBUG] After overrides:  {len(threads)} valid threads")

    # ---------------- output paths ----------------------------------------- #
    out = Path(args.out_dir)
    threads_path = out / "threads" / f"{year:04d}-{month:02d}.json"
    comments_path = out / "comments" / f"{year:04d}-{month:02d}.json"

    # ---------------- convert thread objects ------------------------------- #
    new_thread_records: list[dict] = []
    for sub in threads:
        new_thread_records.append(
            {
                "id": sub.id,
                "title": sub.title,
                "url": f"https://www.reddit.com{sub.permalink}",
                "author": str(sub.author) if sub.author else "[deleted]",
                "created_utc": datetime.utcfromtimestamp(sub.created_utc)
                .replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "num_comments": sub.num_comments,
                "flair": sub.link_flair_text,
            }
        )

    existing_threads = None if args.force else load_month_file(threads_path)
    if existing_threads is not None:
        merged_threads = merge_records(existing_threads[1], new_thread_records)
    else:
        merged_threads = sorted(new_thread_records, key=lambda r: r["created_utc"])

    # ---------------- fetch comments with progress bar --------------------- #
    new_comment_records: list[dict] = []
    for sub in tqdm(
        threads,
        desc="Fetching comments",
        unit="thread",
        disable=not args.debug,  # show only in debug mode
    ):
        for c in fetch_top_level_comments(sub):
            new_comment_records.append(
                {
                    "id": c.id,
                    "thread_id": sub.id,
                    "thread_title": sub.title,
                    "url": f"https://www.reddit.com{c.permalink}",
                    "author": str(c.author) if c.author else "[deleted]",
                    "created_utc": datetime.utcfromtimestamp(c.created_utc)
                    .replace(tzinfo=timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "body": c.body,
                }
            )

    existing_comments = None if args.force else load_month_file(comments_path)
    if existing_comments is not None:
        merged_comments = merge_records(existing_comments[1], new_comment_records)
    else:
        merged_comments = sorted(new_comment_records, key=lambda r: r["created_utc"])

    # ---------------- metadata & writes ------------------------------------ #
    missing = _calc_missing(year, month, threads)
    ts_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    threads_meta = {
        "month": f"{year:04d}-{month:02d}",
        "extracted_at": ts_iso,
        "thread_count": len(merged_threads),
        "expected_days": calendar.monthrange(year, month)[1],
        "missing_days": [d.isoformat() for d in missing],
    }
    write_month_file(threads_path, threads_meta, merged_threads)

    threads_with_comments = {c["thread_id"] for c in merged_comments}
    comments_meta = {
        "month": threads_meta["month"],
        "extracted_at": ts_iso,
        "comment_count": len(merged_comments),
        "thread_count_with_comments": len(threads_with_comments),
        "missing_days": threads_meta["missing_days"],
        "threads_missing_comments": [
            t["id"] for t in merged_threads if t["id"] not in threads_with_comments
        ],
    }
    write_month_file(comments_path, comments_meta, merged_comments)

    # ---------------- console summary -------------------------------------- #
    for sub in threads:
        print(f"{sub.id:>8}  {sub.title}")

    if args.debug:
        print(f"[DEBUG] Missing days: {', '.join(d.isoformat() for d in missing) or 'None'}")

    print(
        f"[INFO] SOTD fetch complete for {threads_meta['month']}: "
        f"{threads_meta['thread_count']} threads, "
        f"{comments_meta['comment_count']} comments, "
        f"{len(missing)} missing days ({', '.join(threads_meta['missing_days'])})"
    )


if __name__ == "__main__":
    main()
