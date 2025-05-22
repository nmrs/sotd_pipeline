from __future__ import annotations

# ruff: noqa: E402  # keep imports after docstring for clarity

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

import argparse
import calendar
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence, Set, Tuple

from tqdm import tqdm

from sotd.fetch.merge import merge_records
from sotd.fetch.reddit import (
    fetch_top_level_comments,
    get_reddit,
    search_threads,
)
from sotd.fetch.save import load_month_file, write_month_file
from sotd.utils import parse_thread_date

# --------------------------------------------------------------------------- #
# helpers - parsing                                                           #
# --------------------------------------------------------------------------- #


def _parse_ym(text: str) -> Tuple[int, int]:
    """Convert ``YYYY-MM`` string → ``(year, month)`` tuple."""
    try:
        y, m = text.split("-")
        y_i, m_i = int(y), int(m)
        if not (1 <= m_i <= 12):
            raise ValueError
        return y_i, m_i
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid month format: {text!r}") from None


def _iter_months(
    y1: int,
    m1: int,
    y2: int,
    m2: int,
) -> List[Tuple[int, int]]:
    """Inclusive iterator of (year, month) tuples from (y1,m1) → (y2,m2) ascending."""
    months: List[Tuple[int, int]] = []
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        months.append((y, m))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
    return months


def _current_ym() -> Tuple[int, int]:
    today = _date.today()
    return today.year, today.month


# --------------------------------------------------------------------------- #
# helper: find missing days in month                                         #
# --------------------------------------------------------------------------- #


def _calc_missing(year: int, month: int, threads) -> List[_date]:
    """Return any calendar days in *month* that lack a thread title date."""
    last_day = calendar.monthrange(year, month)[1]
    expected: Set[_date] = {_date(year, month, d) for d in range(1, last_day + 1)}
    present: Set[_date] = {
        d for t in threads if (d := parse_thread_date(t.title, year)) is not None
    }
    return sorted(expected - present)


# --------------------------------------------------------------------------- #
# arg-normaliser                                                              #
# --------------------------------------------------------------------------- #


def _month_span(args: argparse.Namespace) -> List[Tuple[int, int]]:
    """Normalize CLI args into an ordered list of months to fetch."""
    # 0. Mutually‑exclusive flag conflict detection
    supplied = sum(bool(x) for x in (args.month, args.year, args.range))
    if supplied > 1:
        raise argparse.ArgumentTypeError("Choose only one of --month, --year, or --range")

    # expand --range → start/end
    if args.range:
        try:
            s_raw, e_raw = (part or None for part in args.range.split(":"))
        except ValueError:
            raise argparse.ArgumentTypeError("--range must be START:END") from None
        if s_raw:
            args.start = s_raw
        if e_raw:
            args.end = e_raw

    # expand --month / --year
    if args.month:
        args.start = args.end = args.month
    if args.year:
        args.start, args.end = f"{args.year}-01", f"{args.year}-12"

    # default: current month
    if args.start is None and args.end is None:
        cur_y, cur_m = _current_ym()
        ym = f"{cur_y:04d}-{cur_m:02d}"
        args.start = args.end = ym
    elif args.end is None:
        args.end = args.start
    elif args.start is None:
        args.start = args.end

    start_y, start_m = _parse_ym(args.start)
    end_y, end_m = _parse_ym(args.end)
    if (end_y, end_m) < (start_y, start_m):
        raise argparse.ArgumentTypeError("--end precedes --start")

    return _iter_months(start_y, start_m, end_y, end_m)


# --------------------------------------------------------------------------- #
# single-month processing (formerly main body)                                #
# --------------------------------------------------------------------------- #


def _process_month(
    year: int,
    month: int,
    args: argparse.Namespace,
    *,
    reddit,
    include_overrides,
    exclude_overrides,
) -> dict:
    """Fetch + merge + save for one calendar month."""
    threads = search_threads("wetshaving", year, month, debug=args.debug)

    from sotd.fetch.overrides import apply_overrides

    threads = apply_overrides(
        threads,
        include_overrides,
        exclude_overrides,
        reddit=reddit,
        year=year,
        month=month,
        debug=args.debug,
    )
    if args.debug:
        print(f"[DEBUG] After overrides:  {len(threads)} valid threads")

    out = Path(args.out_dir)
    threads_path = out / "threads" / f"{year:04d}-{month:02d}.json"
    comments_path = out / "comments" / f"{year:04d}-{month:02d}.json"

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

    # comment records with inner progress bar
    new_comment_records: List[dict] = []
    for sub in tqdm(
        threads,
        desc=f"Comments {year}-{month:02d}",
        unit="thread",
        disable=False,
        leave=False,
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

    existing_c = None if args.force else load_month_file(comments_path)
    merged_comments = (
        merge_records(existing_c[1], new_comment_records)
        if existing_c is not None
        else sorted(new_comment_records, key=lambda r: r["created_utc"])
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
def main(argv: Sequence[str] | None = None) -> None:  # easier to test
    p = argparse.ArgumentParser(description="Fetch & persist SOTD data")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--month")
    g.add_argument("--year")
    g.add_argument("--range")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--out-dir", default="data")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument(
        "--list-months",
        action="store_true",
        help="List months with existing threads or comments files",
    )
    args = p.parse_args(argv)

    # If --list-months is set, list months and exit
    if args.list_months:
        from sotd.fetch.audit import list_available_months

        months_found = list_available_months(args.out_dir)
        for month in months_found:
            print(month)
        exit(0)

    # compute span
    months = _month_span(args)

    if args.audit:
        from sotd.fetch.audit import _audit_months

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
            exit(0)
        else:
            exit(1)

    reddit = get_reddit()
    from sotd.fetch.overrides import load_overrides

    inc_over, exc_over = load_overrides()

    results = []
    for year, month in tqdm(months, desc="Months", unit="month", disable=False):
        result = _process_month(
            year,
            month,
            args,
            reddit=reddit,
            include_overrides=inc_over,
            exclude_overrides=exc_over,
        )
        results.append(result)

    # Filter out any None results (e.g., if _process_month is monkeypatched to do nothing)
    valid_results = [res for res in results if res is not None]

    if len(valid_results) == 1:
        res = valid_results[0]
        year = res["year"]
        month = res["month"]
        missing_days = res["missing_days"]
        if not (res["threads"] == 0 and len(missing_days) == calendar.monthrange(year, month)[1]):
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
            for days in ([] if res.get("missing_days") is None else res["missing_days"])
            for d in days
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


if __name__ == "__main__":
    main()
