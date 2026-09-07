"""Per-shave validation queries against enriched SOTD data.

``data/enriched/YYYY-MM.json`` holds one record per shave comment — the inputs
the aggregate phase rolls up. These records carry author handles and dates that
aggregated files anonymize, so this tool answers the who-used-what questions
the aggregate CLI cannot: who used a product, how many times, and on which
days (double-shave days, single-user attributions, per-user streaks).

Exit codes: 0 success, 1 on query errors (unknown month, no match, ambiguity).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

CATEGORIES = ("razor", "blade", "soap", "brush")


class QueryError(Exception):
    """Raised for deterministic, user-facing query failures."""


def default_data_dir() -> str:
    """Return the artifact root from the environment or the repo default."""
    return os.environ.get("SOTD_DATA_DIR", "data")


def build_parser() -> argparse.ArgumentParser:
    """Build the enriched_query argument parser."""
    parser = argparse.ArgumentParser(
        prog="enriched_query",
        description="Per-shave validation queries against data/enriched monthly files.",
    )
    parser.add_argument("--data-dir", default=default_data_dir(), help="Artifact root directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of aligned text")
    sub = parser.add_subparsers(dest="command", required=True)

    schema = sub.add_parser(
        "schema", help="Record count, record keys, and per-category subobject shapes"
    )
    schema.add_argument("--month", required=True, help="Month (YYYY-MM)")

    user = sub.add_parser("user", help="One user's shaves: dates plus matched products")
    user.add_argument("--month", required=True, help="Month (YYYY-MM)")
    user.add_argument("--name", required=True, help="Reddit author handle")
    user.add_argument("--category", choices=CATEGORIES, help="Restrict to a product category")
    user.add_argument(
        "--product",
        help="With --category: only entries using this matched product name",
    )

    usage = sub.add_parser("usage", help="Who used a product: per-shave rows or per-user counts")
    usage.add_argument("--month", required=True, help="Month (YYYY-MM)")
    usage.add_argument("--category", choices=CATEGORIES, required=True, help="Product category")
    usage.add_argument("--name", required=True, help="Matched product name (case-insensitive)")
    usage.add_argument(
        "--contains", action="store_true", help="Match by case-insensitive substring"
    )
    usage.add_argument("--by-user", action="store_true", help="Aggregate to per-author counts")

    timeline = sub.add_parser(
        "timeline",
        help="Adoption timeline for a product across a month window "
        "(per-month counts, per-day spikes, per-user first/last + new/returning)",
    )
    timeline.add_argument("--months", required=True, help="Window YYYY-MM:YYYY-MM (inclusive)")
    timeline.add_argument("--category", choices=CATEGORIES, required=True, help="Product category")
    timeline.add_argument("--name", required=True, help="Matched product name (case-insensitive)")
    timeline.add_argument(
        "--contains", action="store_true", help="Match by case-insensitive substring"
    )
    timeline.add_argument("--by-day", action="store_true", help="Add per-day shave counts")
    timeline.add_argument(
        "--by-user",
        action="store_true",
        help="Add per-user rows (shaves, first/last dates, new/returning status)",
    )
    timeline.add_argument(
        "--since",
        help="Bound the lookback used to classify new vs returning users (YYYY-MM); "
        "default is the earliest enriched month on disk",
    )

    return parser


def _load_records(data_dir: Path, month: str) -> list[dict[str, Any]]:
    """Load enriched records for a month, raising QueryError if unusable."""
    path = data_dir / "enriched" / f"{month}.json"
    try:
        with path.open(encoding="utf-8") as handle:
            doc = json.load(handle)
    except FileNotFoundError as exc:
        raise QueryError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise QueryError(f"invalid JSON in {path}: {exc}") from exc
    records = doc.get("data") if isinstance(doc, dict) else doc
    if not isinstance(records, list):
        raise QueryError(f"unexpected structure in {path}")
    return [record for record in records if isinstance(record, dict)]


def _product_label(matched: Any, category: str) -> str:
    """Compose an aggregate-style display name from a matched dict.

    soap -> 'Brand - Scent'; others -> 'Brand Model' (matching report table
    names so validation targets read the same everywhere). Empty string when
    the entry has no matched brand.
    """
    if not isinstance(matched, dict):
        return ""
    brand = matched.get("brand") if isinstance(matched.get("brand"), str) else None
    if not brand:
        return ""
    if category == "soap":
        scent = matched.get("scent") if isinstance(matched.get("scent"), str) else None
        return f"{brand} - {scent}" if scent else brand
    model = matched.get("model") if isinstance(matched.get("model"), str) else None
    return f"{brand} {model}" if model else brand


def _record_label(record: dict[str, Any], category: str) -> str:
    """Return the composed matched label for one record's category object."""
    category_obj = record.get(category)
    if not isinstance(category_obj, dict):
        return ""
    return _product_label(category_obj.get("matched"), category)


def _entry_date(record: dict[str, Any]) -> str:
    """Return the YYYY-MM-DD date of a record, or a placeholder."""
    created = record.get("created_utc")
    return created[:10] if isinstance(created, str) and len(created) >= 10 else "?"


def query_schema(args: argparse.Namespace) -> dict[str, Any]:
    """Return record count, record keys, and per-category subobject shape unions."""
    data_dir = Path(args.data_dir)
    records = _load_records(data_dir, args.month)
    record_keys = sorted({key for record in records for key in record})
    categories: dict[str, Any] = {}
    for category in CATEGORIES:
        objs = [
            obj for record in records for obj in [record.get(category)] if isinstance(obj, dict)
        ]
        matched_keys = sorted(
            {
                key
                for obj in objs
                for matched in [obj.get("matched")]
                if isinstance(matched, dict)
                for key in matched
            }
        )
        enriched_keys = sorted(
            {
                key
                for obj in objs
                for enriched in [obj.get("enriched")]
                if isinstance(enriched, dict)
                for key in enriched
            }
        )
        info: dict[str, Any] = {
            "present": len(objs),
            "keys": sorted({key for obj in objs for key in obj}),
            "matched_keys": matched_keys,
        }
        if enriched_keys:
            info["enriched_keys"] = enriched_keys
        categories[category] = info
    return {
        "month": args.month,
        "record_count": len(records),
        "record_keys": record_keys,
        "categories": categories,
    }


def _month_labels(start: str, end: str) -> list[str]:
    """Return every YYYY-MM label between start and end inclusive."""
    start_year, start_month = int(start[:4]), int(start[5:7])
    end_year, end_month = int(end[:4]), int(end[5:7])
    labels: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        labels.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return labels


def _available_enriched_months(data_dir: Path) -> list[str]:
    """Sorted list of enriched month labels present on disk."""
    return sorted(path.stem for path in (data_dir / "enriched").glob("????-??.json"))


def query_timeline(args: argparse.Namespace) -> dict[str, Any]:
    """Adoption timeline for one matched product across a bounded month window.

    Scans the lookback months (all on disk before the window start, bounded by
    --since) to establish each user's first use of the product, then reports
    per-month counts with new/returning splits, optional per-day and per-user
    detail. Future months are never read: the window's end bounds the scan.
    """
    data_dir = Path(args.data_dir)
    parts = args.months.split(":")
    if len(parts) != 2:
        raise QueryError(f"Window must be YYYY-MM:YYYY-MM (got: {args.months})")
    start, end = parts
    for value in (start, end):
        if not re.match(r"^\d{4}-\d{2}$", value):
            raise QueryError(f"invalid month {value!r}; expected YYYY-MM")
    if start > end:
        raise QueryError(f"Window start {start} is after end {end}")
    if args.since:
        if not re.match(r"^\d{4}-\d{2}$", args.since):
            raise QueryError(f"invalid --since {args.since!r}; expected YYYY-MM")
        if args.since > start:
            raise QueryError(f"--since {args.since} is after window start {start}")

    window = _month_labels(start, end)
    lookback = [m for m in _available_enriched_months(data_dir) if start > m >= (args.since or "")]
    present_window = [m for m in window if (data_dir / "enriched" / f"{m}.json").is_file()]
    skipped = [m for m in window if m not in present_window]

    target = str(args.name).casefold()
    scanned: dict[str, list[dict[str, Any]]] = {}
    for month in lookback + present_window:
        records = _load_records(data_dir, month)
        if args.contains:
            scanned[month] = [
                r for r in records if target in _record_label(r, args.category).casefold()
            ]
        else:
            scanned[month] = [
                r for r in records if _record_label(r, args.category).casefold() == target
            ]

    if args.contains:
        labels = {_record_label(r, args.category) for hits in scanned.values() for r in hits}
        if len(labels) > 1:
            raise QueryError(
                f"ambiguous name {args.name!r} in {args.category}; "
                f"candidates: {', '.join(sorted(labels))}"
            )
    window_hits = [r for m in present_window for r in scanned[m]]
    if not window_hits:
        raise QueryError(f"no {args.category} entries matching {args.name!r} in {start}:{end}")

    first_month: dict[str, str] = {}
    prior_users: set[str] = set()
    for month in lookback:
        for record in scanned[month]:
            author = str(record.get("author", ""))
            prior_users.add(author)
            first_month.setdefault(author, month)

    months_rows: list[dict[str, Any]] = []
    for month in present_window:
        hits = scanned[month]
        users_this = {str(r.get("author", "")) for r in hits}
        for record in hits:
            first_month.setdefault(str(record.get("author", "")), month)
        new_users = sum(1 for user in users_this if first_month[user] == month)
        months_rows.append(
            {
                "month": month,
                "shaves": len(hits),
                "unique_users": len(users_this),
                "new_users": new_users,
                "returning_users": len(users_this) - new_users,
            }
        )

    result: dict[str, Any] = {
        "category": args.category,
        "name": args.name,
        "window": [start, end],
        "baseline": {
            "since": lookback[0] if lookback else None,
            "through": lookback[-1] if lookback else None,
            "prior_users": len(prior_users),
        },
        "months": months_rows,
        "skipped": skipped,
    }

    if args.by_day:
        days: dict[str, list[str]] = {}
        for record in window_hits:
            days.setdefault(_entry_date(record), []).append(str(record.get("author", "")))
        result["by_day"] = [
            {"date": date, "shaves": len(authors), "users": len(set(authors))}
            for date, authors in sorted(days.items())
        ]

    if args.by_user:
        grouped: dict[str, list[str]] = {}
        for record in window_hits + [r for m in lookback for r in scanned[m]]:
            grouped.setdefault(str(record.get("author", "")), []).append(_entry_date(record))
        result["users"] = [
            {
                "author": author,
                "shaves": len(dates),
                "first": min(dates),
                "last": max(dates),
                "status": "new" if first_month[author] >= start else "returning",
            }
            for author, dates in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        ]
    return result


def query_user(args: argparse.Namespace) -> dict[str, Any]:
    """Return one user's shaves (optionally filtered to a product)."""
    data_dir = Path(args.data_dir)
    records = _load_records(data_dir, args.month)
    user_records = sorted(
        (r for r in records if r.get("author") == args.name),
        key=lambda r: str(r.get("created_utc", "")),
    )
    if not user_records:
        raise QueryError(f"no entries by author {args.name!r} in {args.month}")
    if args.category:
        user_records = [
            r
            for r in user_records
            if _record_label(r, args.category).casefold() == str(args.product).casefold()
        ]
        if not user_records:
            raise QueryError(
                f"no {args.category} entries matching {args.product!r} for {args.name!r}"
            )
    rows = [
        {
            "date": _entry_date(r),
            "razor": _record_label(r, "razor") or "-",
            "blade": _record_label(r, "blade") or "-",
            "soap": _record_label(r, "soap") or "-",
            "brush": _record_label(r, "brush") or "-",
        }
        for r in user_records
    ]
    dates = [row["date"] for row in rows]
    multi = sorted({d for d in set(dates) if dates.count(d) > 1})
    return {
        "month": args.month,
        "author": args.name,
        "total_entries": len(rows),
        "distinct_dates": len(set(dates)),
        "multi_shave_dates": multi,
        "rows": rows,
    }


def query_usage(args: argparse.Namespace) -> dict[str, Any]:
    """Return per-shave rows or per-user counts for one matched product."""
    data_dir = Path(args.data_dir)
    records = _load_records(data_dir, args.month)
    if args.contains:
        target = str(args.name).casefold()
        matched = [r for r in records if target in _record_label(r, args.category).casefold()]
        labels = {_record_label(r, args.category) for r in matched}
        if len(labels) > 1:
            raise QueryError(
                f"ambiguous name {args.name!r} in {args.category}; "
                f"candidates: {', '.join(sorted(labels))}"
            )
    else:
        target = str(args.name).casefold()
        matched = [r for r in records if _record_label(r, args.category).casefold() == target]
    if not matched:
        raise QueryError(f"no {args.category} entries matching {args.name!r} in {args.month}")
    matched.sort(key=lambda r: str(r.get("created_utc", "")))
    if args.by_user:
        counts: dict[str, int] = {}
        for record in matched:
            author = str(record.get("author", ""))
            counts[author] = counts.get(author, 0) + 1
        rows = [
            {"author": author, "shaves": count}
            for author, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
    else:
        rows = [
            {
                "date": _entry_date(r),
                "author": str(r.get("author", "")),
                "matched": _record_label(r, args.category),
            }
            for r in matched
        ]
    return {
        "month": args.month,
        "category": args.category,
        "name": args.name,
        "total_shaves": len(matched),
        "rows": rows,
    }


def _render_schema(result: dict[str, Any]) -> str:
    """Render the schema result as aligned per-category lines."""
    lines = [
        f"{result['month']}  records={result['record_count']}",
        f"record keys: {', '.join(result['record_keys'])}",
    ]
    for category, info in result["categories"].items():
        keys = ", ".join(info["keys"]) or "(none)"
        matched = ", ".join(info["matched_keys"]) or "(none)"
        line = f"  {category:<6} present={info['present']}  keys: {keys}  | matched: {matched}"
        if "enriched_keys" in info:
            line += f"  | enriched: {', '.join(info['enriched_keys'])}"
        lines.append(line)
    return "\n".join(lines)


def _render_timeline(result: dict[str, Any]) -> str:
    """Render a timeline result: month table plus optional day/user sections."""
    baseline = result["baseline"]
    if baseline["since"]:
        note = (
            f"(baseline {baseline['since']}..{baseline['through']}: "
            f"{baseline['prior_users']} prior user"
            f"{'s' if baseline['prior_users'] != 1 else ''})"
        )
    else:
        note = f"(baseline: no months on disk before {result['window'][0]})"
    lines = [
        f"{result['category']} '{result['name']}'  "
        f"{result['window'][0]}:{result['window'][1]}  {note}"
    ]
    if result["skipped"]:
        lines.append(f"(skipped missing files: {', '.join(result['skipped'])})")

    headers = ["month", "shaves", "users", "new", "returning"]
    rows = [
        [
            m["month"],
            str(m["shaves"]),
            str(m["unique_users"]),
            str(m["new_users"]),
            str(m["returning_users"]),
        ]
        for m in result["months"]
    ]
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    lines.append("  ".join(h.rjust(widths[i]) for i, h in enumerate(headers)))
    for row in rows:
        lines.append("  ".join(c.rjust(widths[i]) for i, c in enumerate(row)))

    if "by_day" in result:
        lines.append("")
        day_headers = ["date", "shaves", "users"]
        day_rows = [[d["date"], str(d["shaves"]), str(d["users"])] for d in result["by_day"]]
        widths = [
            max(len(day_headers[i]), *(len(r[i]) for r in day_rows))
            for i in range(len(day_headers))
        ]
        lines.append("  ".join(h.rjust(widths[i]) for i, h in enumerate(day_headers)))
        for row in day_rows:
            lines.append("  ".join(c.rjust(widths[i]) for i, c in enumerate(row)))

    if "users" in result:
        lines.append("")
        user_headers = ["author", "shaves", "first", "last", "status"]
        user_rows = [
            [u["author"], str(u["shaves"]), u["first"], u["last"], u["status"]]
            for u in result["users"]
        ]
        widths = [
            max(len(user_headers[i]), *(len(r[i]) for r in user_rows))
            for i in range(len(user_headers))
        ]
        lines.append("  ".join(h.rjust(widths[i]) for i, h in enumerate(user_headers)))
        for row in user_rows:
            lines.append("  ".join(c.rjust(widths[i]) for i, c in enumerate(row)))
    return "\n".join(lines)


def _render(result: dict[str, Any]) -> str:
    """Render a query result as an aligned table plus summary lines."""
    lines: list[str] = []
    rows = result["rows"]
    if rows and "author" in rows[0] and "shaves" in rows[0]:
        headers = ["author", "shaves"]
        lines.append(f"total shaves: {result['total_shaves']}")
    elif rows and "matched" in rows[0]:
        headers = ["date", "author", "matched"]
        lines.append(f"total shaves: {result['total_shaves']}")
    else:
        headers = ["date", "razor", "blade", "soap", "brush"]
    if rows:
        widths = [max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers]
        lines.append("  ".join(h.rjust(widths[i]) for i, h in enumerate(headers)))
        for row in rows:
            lines.append(
                "  ".join(str(row.get(h, "")).rjust(widths[i]) for i, h in enumerate(headers))
            )
    else:
        lines.append("(no rows)")
    if "distinct_dates" in result:
        lines.append(
            f"\nentries: {result['total_entries']}, "
            f"distinct shave dates: {result['distinct_dates']}"
        )
        if result["multi_shave_dates"]:
            lines.append(f"multi-shave dates: {', '.join(result['multi_shave_dates'])}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point returning a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "schema":
            result = query_schema(args)
        elif args.command == "timeline":
            result = query_timeline(args)
        elif args.command == "user":
            result = query_user(args)
        else:
            result = query_usage(args)
    except QueryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.command == "schema":
        print(json.dumps(result, indent=2) if args.json else _render_schema(result))
    elif args.command == "timeline":
        print(json.dumps(result, indent=2) if args.json else _render_timeline(result))
    else:
        print(json.dumps(result, indent=2) if args.json else _render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
