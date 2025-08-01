"""
Fetch one or many SOTD months.

CLI matrix
──────────
(no flags)                 → current month
--month YYYY-MM            → that single month
--year  YYYY               → Jan..Dec of that year
--start YYYY-MM            → that month (single) unless --end also given
--end   YYYY-MM            → that month (single) unless --start also given
--start A --end B          → inclusive span A…B
--range A:B                → shorthand for above (either side optional)
(conflicting combos)       → error
"""

# ruff: noqa: E402  # keep imports after docstring for clarity
from __future__ import annotations

import argparse
import calendar
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence, Set

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.fetch.audit import _audit_months, list_available_months
from sotd.fetch.cli import get_parser
from sotd.fetch.merge import merge_records
from sotd.fetch.reddit import (
    fetch_top_level_comments_parallel,
    get_reddit,
    search_threads,
)
from sotd.fetch.save import load_month_file, write_month_file
from sotd.utils import parse_thread_date

# --------------------------------------------------------------------------- #
# helper: find missing days in month                                         #
# --------------------------------------------------------------------------- #


def _calc_missing(year: int, month: int, threads) -> List[_date]:
    """Return any calendar days in *month* that lack a thread title date."""
    from datetime import datetime

    last_day = calendar.monthrange(year, month)[1]
    expected: Set[_date] = {_date(year, month, d) for d in range(1, last_day + 1)}

    present: Set[_date] = set()
    for t in threads:
        d = parse_thread_date(t.title, year)
        # --- CHANGED: Fallback to _override_date if present and title is unparsable ---
        if d is None and hasattr(t, "_override_date"):
            try:
                d = datetime.strptime(t._override_date, "%Y-%m-%d").date()
            except Exception:
                d = None
        if d is not None:
            present.add(d)

    return sorted(expected - present)


# --------------------------------------------------------------------------- #
# single-month processing (formerly main body)                                #
# --------------------------------------------------------------------------- #


def _process_month(
    year: int,
    month: int,
    args: argparse.Namespace,
    *,
    reddit,
) -> dict:
    """Fetch + merge + save for one calendar month."""
    threads = search_threads("wetshaving", year, month, debug=args.debug)

    if args.debug:
        print(f"[DEBUG] Found {len(threads)} valid threads")

    out = Path(args.out_dir)
    threads_path = out / "threads" / f"{year:04d}-{month:02d}.json"
    comments_path = out / "comments" / f"{year:04d}-{month:02d}.json"

    if args.force:
        if threads_path.exists():
            threads_path.unlink()
        if comments_path.exists():
            comments_path.unlink()

    # thread records
    new_thread_records = [
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
        for sub in threads
    ]

    existing_t = None if args.force else load_month_file(threads_path)
    merged_threads = (
        merge_records(existing_t[1], new_thread_records)
        if existing_t is not None
        else sorted(new_thread_records, key=lambda r: r["created_utc"])
    )

    if not merged_threads:
        print(f"[WARN] No threads found for {year:04d}-{month:02d}; skipping file writes.")
        missing = _calc_missing(year, month, threads)
        return {
            "year": year,
            "month": month,
            "threads": 0,
            "comments": 0,
            "missing_days": [d.isoformat() for d in missing],
        }

    # comment records with parallel processing
    print(f"[INFO] Fetching comments for {len(threads)} threads using parallel processing...")
    comment_results = fetch_top_level_comments_parallel(
        threads, max_workers=10, return_metrics=True
    )

    if isinstance(comment_results, tuple):
        new_comment_records, metrics = comment_results
        print(f"[INFO] Parallel processing metrics: {metrics}")
    else:
        new_comment_records = comment_results

    # Convert comment results to records
    comment_records = []
    for i, comments in enumerate(new_comment_records):
        sub = threads[i]
        for c in comments:
            comment_records.append(
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

    existing_c = None if args.force else load_month_file(comments_path)
    merged_comments = (
        merge_records(existing_c[1], comment_records)
        if existing_c is not None
        else sorted(comment_records, key=lambda r: r["created_utc"])
    )

    # metadata + write
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

    # summary dictionary return
    return {
        "year": year,
        "month": month,
        "threads": len(merged_threads),
        "comments": len(merged_comments),
        "missing_days": [d.isoformat() for d in missing],
    }


# --------------------------------------------------------------------------- #
# main                                                                        #
# --------------------------------------------------------------------------- #
def main(argv: Sequence[str] | None = None) -> int:  # easier to test
    try:
        parser = get_parser()
        args = parser.parse_args(argv)

        # If --list-months is set, list months and exit
        if args.list_months:
            months_found = list_available_months(args.out_dir)
            if months_found:
                for month in months_found:
                    print(month)
                return 0
            else:
                return 0

        # compute span
        months = month_span(args)

        if args.audit:
            missing_info = _audit_months(months, args.out_dir)
            any_missing = False
            # Print missing files
            for mf in missing_info.get("missing_files", []):
                print(f"[MISSING FILE] {mf}")
                any_missing = True
            # Print missing days per month
            for month_str, days in missing_info.get("missing_days", {}).items():
                for d in days:
                    print(f"{month_str}: {d}")
                    any_missing = True
            if not any_missing:
                print("[INFO] Audit successful: no missing files or days detected.")
                return 0
            else:
                return 1

        reddit = get_reddit()

        results = []
        for year, month in tqdm(months, desc="Months", unit="month", disable=False):
            result = _process_month(
                year,
                month,
                args,
                reddit=reddit,
            )
            results.append(result)

        # Filter out any None results (e.g., if _process_month is monkeypatched to do nothing)
        valid_results = [res for res in results if res is not None]

        if len(valid_results) == 1:
            res = valid_results[0]
            year = res["year"]
            month = res["month"]
            missing_days = res["missing_days"]
            if not (
                res["threads"] == 0 and len(missing_days) == calendar.monthrange(year, month)[1]
            ):
                for d in missing_days:
                    print(f"[WARN] Missing day: {d}")
            print(
                f"[INFO] SOTD fetch complete for {year:04d}-{month:02d}: "
                f"{res['threads']} threads, "
                f"{res['comments']} comments, "
                f"{len(missing_days)} missing day{'s' if len(missing_days) != 1 else ''}"
            )
        elif len(valid_results) > 1:
            # multiple months
            all_missing_days = sorted(
                d
                for res in valid_results
                for d in ([] if res.get("missing_days") is None else res["missing_days"])
            )
            for d in all_missing_days:
                print(f"[WARN] Missing day: {d}")
            start_ym = valid_results[0]["year"], valid_results[0]["month"]
            end_ym = valid_results[-1]["year"], valid_results[-1]["month"]
            total_threads = sum(res["threads"] for res in valid_results)
            total_comments = sum(res["comments"] for res in valid_results)
            total_missing = len(all_missing_days)

            print(
                f"[INFO] SOTD fetch complete for "
                f"{start_ym[0]:04d}-{start_ym[1]:02d}…{end_ym[0]:04d}-{end_ym[1]:02d}: "
                f"{total_threads} threads, "
                f"{total_comments} comments, "
                f"{total_missing} missing day{'s' if total_missing != 1 else ''}"
            )

        return 0  # Success
    except KeyboardInterrupt:
        print("\n[INFO] Fetch phase interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        print(f"[ERROR] Fetch phase failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
