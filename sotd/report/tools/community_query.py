"""Point-query CLI for community context data.

Answers the questions agents and shell debugging need about ``data/community/``
without loading whole month files into context:
thread listings, one thread with its reconstructed comment tree, and
keyword/author search across a bounded month window.

Month/window arguments are always explicit — this structurally enforces the
"never see future months" rule (same mechanism as --end on history queries).

Exit codes: 0 success, 1 on query errors (missing/malformed month file,
unknown thread ID, bad window).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path


class QueryError(Exception):
    """Raised for deterministic, user-facing query failures."""


def default_data_dir() -> str:
    """Return the artifact root from the environment or the repo default."""
    return os.environ.get("SOTD_DATA_DIR", "data")


def parse_month(s: str) -> str:
    try:
        datetime.strptime(s.strip(), "%Y-%m")
    except ValueError as exc:
        raise QueryError(f"Invalid YYYY-MM format: {s}") from exc
    return s.strip()


def month_iter(start: str, end: str) -> list:
    """Inclusive list of YYYY-MM strings from start to end."""
    a = datetime.strptime(start, "%Y-%m")
    b = datetime.strptime(end, "%Y-%m")
    if a > b:
        raise QueryError(f"Window start {start} is after end {end}")
    months = []
    cur = a
    while cur <= b:
        months.append(cur.strftime("%Y-%m"))
        cur = datetime(cur.year + (cur.month == 12), 1 if cur.month == 12 else cur.month + 1, 1)
    return months


def load_month(data_dir: str, month: str) -> dict:
    path = Path(data_dir) / "community" / f"{month}.json"
    if not path.is_file():
        raise QueryError(f"No community file for {month}: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise QueryError(f"Unreadable community file for {month}: {exc}") from exc
    if not isinstance(doc, dict) or "meta" not in doc or "data" not in doc:
        raise QueryError(f"Malformed community file for {month}: missing meta/data")
    return doc


def comment_counts(doc: dict) -> Counter:
    return Counter(c["thread_id"] for c in doc["data"].get("comments", []))


def cmd_meta(doc: dict, *, as_json: bool) -> str:
    meta = doc["meta"]
    if as_json:
        return json.dumps(meta, indent=2)
    discovery = meta.get("discovery", {})
    return "\n".join(
        [
            f"month:                    {meta.get('month')}",
            f"extracted_at:             {meta.get('extracted_at')}",
            f"post_count:               {meta.get('post_count')}",
            f"comment_count:            {meta.get('comment_count')}",
            f"in_pipeline_post_count:   {meta.get('in_pipeline_post_count')}",
            f"discovery.strategies:     {', '.join(discovery.get('strategies', []))}",
            f"discovery.complete:       {discovery.get('complete')}",
        ]
    )


def keymap_for(sort: str):
    return {
        "comments": lambda r: (-r["_comments"], r["created_utc"]),
        "score": lambda r: (-r["score"], r["created_utc"]),
        "date": lambda r: r["created_utc"],
    }[sort]


def cmd_threads(
    doc: dict,
    *,
    min_comments: int = 0,
    author: str | None = None,
    flair: str | None = None,
    top: int = 10,
    sort: str = "comments",
    thread_filter: str = "all",
    as_json: bool = False,
) -> str:
    counts = comment_counts(doc)
    rows = []
    for p in doc["data"].get("posts", []):
        if thread_filter == "sotd" and not p.get("in_pipeline"):
            continue
        if thread_filter == "non-sotd" and p.get("in_pipeline"):
            continue
        if author and (p.get("author") or "").lower() != author.lower():
            continue
        if flair and (p.get("flair") or "") != flair:
            continue
        n_comments = counts.get(p["id"], 0)
        if n_comments < min_comments:
            continue
        rows.append({**p, "_comments": n_comments})

    rows.sort(key=keymap_for(sort))

    if as_json:
        return json.dumps(rows[:top], indent=2)

    lines = [
        f"{'id':<12} {'date':<10} {'flag':<5} {'cmts':>4} {'score':>5}  "
        f"{'author':<20} {'title'}"
    ]
    for r in rows[:top]:
        flag = ("SOTD" if r.get("in_pipeline") else "-") if "in_pipeline" in r else "n/a"
        title = (r.get("title") or "")[:60]
        lines.append(
            f"{r['id']:<12} {r['created_utc'][:10]:<10} {flag:<5} {r['_comments']:>4} "
            f"{r['score']:>5}  {(r.get('author') or '')[:20]:<20} {title}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="community_query",
        description="Query data/community JSON files (meta, thread listings, thread trees, search).",
    )
    parser.add_argument("--data-dir", default=default_data_dir(), help="Artifact root directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of aligned text")

    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("meta", help="Print the meta block for a month")
    meta.add_argument("--month", required=True, help="Month (YYYY-MM)")

    threads = sub.add_parser("threads", help="List posts for a month with filters")
    threads.add_argument("--month", required=True, help="Month (YYYY-MM)")
    threads.add_argument("--min-comments", type=int, default=0, help="Minimum comment count")
    threads.add_argument("--author", help="Exact author name (case-insensitive)")
    threads.add_argument("--flair", help="Exact link flair text")
    threads.add_argument("--top", type=int, default=10, help="Max rows (default 10)")
    threads.add_argument(
        "--sort", choices=["comments", "score", "date"], default="comments", help="Sort key"
    )
    threads.add_argument(
        "--filter",
        choices=["sotd", "non-sotd", "all"],
        default="all",
        help="Key off the in_pipeline flag (default all)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        doc = load_month(args.data_dir, parse_month(args.month))
        if args.command == "meta":
            print(cmd_meta(doc, as_json=args.json))
        elif args.command == "threads":
            print(
                cmd_threads(
                    doc,
                    min_comments=args.min_comments,
                    author=args.author,
                    flair=args.flair,
                    top=args.top,
                    sort=args.sort,
                    thread_filter=args.filter,
                    as_json=args.json,
                )
            )
        else:
            raise QueryError(f"Unknown command: {args.command}")
        return 0
    except QueryError as e:
        print(str(e), file=sys.stderr)
        return 1
