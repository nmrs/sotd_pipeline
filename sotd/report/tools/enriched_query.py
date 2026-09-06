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
        if args.command == "user":
            result = query_user(args)
        else:
            result = query_usage(args)
    except QueryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.json else _render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
