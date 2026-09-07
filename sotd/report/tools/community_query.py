"""Point-query CLI for community context data.

Answers the questions agents and shell debugging need about ``data/community/``
without loading whole month files into context:
thread listings, one thread with its reconstructed comment tree, bounded
selftext slices for chosen ids ("body reads"), and
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
        return json.dumps(
            [{k: v for k, v in r.items() if k != "_comments"} for r in rows[:top]], indent=2
        )

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

    thread = sub.add_parser("thread", help="One thread with its reconstructed comment tree")
    thread.add_argument("--month", required=True, help="Month (YYYY-MM)")
    thread.add_argument("--id", required=True, help="Thread ID (with or without t3_ prefix)")
    thread.add_argument("--max-comments", type=int, default=50, help="Max comments rendered")

    bodies = sub.add_parser("bodies", help="Bounded selftext slices for chosen post ids")
    bodies.add_argument("--month", required=True, help="Month (YYYY-MM)")
    bodies.add_argument(
        "--ids", required=True, help="Comma-separated post ids (t3_ prefix optional)"
    )
    bodies.add_argument(
        "--max-chars", type=int, default=1000, help="Slice each body to this many chars"
    )

    search = sub.add_parser("search", help="Keyword/author search across a bounded window")
    search.add_argument("--months", required=True, help="Window YYYY-MM:YYYY-MM (inclusive)")
    search.add_argument("--query", required=True, help="Case-insensitive substring")
    search.add_argument("--author", help="Exact author name (case-insensitive)")
    search.add_argument("--top", type=int, default=20, help="Max results (default 20)")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "search":
            parts = args.months.split(":")
            if len(parts) != 2:
                raise QueryError(f"Window must be YYYY-MM:YYYY-MM (got: {args.months})")
            start, end = parts
            months = month_iter(parse_month(start), parse_month(end))
            docs, missing = _search_docs(args.data_dir, months)
            print(
                cmd_search(
                    docs,
                    query=args.query,
                    author=args.author,
                    top=args.top,
                    as_json=args.json,
                    missing=missing,
                )
            )
        else:
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
            elif args.command == "thread":
                print(cmd_thread(doc, args.id, max_comments=args.max_comments, as_json=args.json))
            elif args.command == "bodies":
                ids = [s for s in (i.strip() for i in args.ids.split(",")) if s]
                if not ids:
                    raise QueryError("No ids given (--ids is comma-separated)")
                print(cmd_bodies(doc, ids, max_chars=args.max_chars, as_json=args.json))
            else:
                raise QueryError(f"Unknown command: {args.command}")
        return 0
    except QueryError as e:
        print(str(e), file=sys.stderr)
        return 1


def _flatten_body(body: str) -> str:
    return " / ".join(line.strip() for line in (body or "").splitlines() if line.strip())


def cmd_thread(doc: dict, thread_id: str, *, max_comments: int = 50, as_json: bool = False) -> str:
    pid = thread_id.removeprefix("t3_")
    posts = {p["id"]: p for p in doc["data"].get("posts", [])}
    post = posts.get(pid)
    if post is None:
        raise QueryError(f"Unknown thread: {thread_id} (month {doc['meta'].get('month')})")
    comments = [c for c in doc["data"].get("comments", []) if c["thread_id"] == pid]
    comments.sort(key=lambda c: c["created_utc"])

    if as_json:
        payload = {"post": post, "comments": comments[:max_comments]}
        if len(comments) > max_comments:
            payload["truncated"] = True
        return json.dumps(payload, indent=2)

    lines = [
        f"{post['id']}  {post['created_utc'][:10]}  u/{post.get('author')}  "
        f"{comment_counts(doc).get(pid, 0)} comments  score {post['score']}"
        + (f"  flair={post['flair']}" if post.get("flair") else ""),
        post["url"],
        post["title"],
    ]
    if post.get("selftext"):
        lines.append("--- body ---")
        lines.append(post["selftext"])
    lines.append(f"--- {len(comments)} comments ---")

    children: dict = {}
    for c in comments:
        # Key replies by bare parent id (Reddit stores t1_<id>) so the tree can be
        # walked by bare comment id; top-level t3_<pid> parents match the walk seed.
        children.setdefault(c["parent_id"].removeprefix("t1_"), []).append(c)

    rendered = 0
    truncated = False

    def walk(parent: str, depth: int) -> None:
        nonlocal rendered, truncated
        for c in sorted(children.get(parent, []), key=lambda x: x["created_utc"]):
            if rendered >= max_comments:
                truncated = True
                return
            body = _flatten_body(c["body"])[:200]
            op = " (OP)" if c.get("is_submitter") else ""
            lines.append(
                f"{'  ' * depth}[{c['id']}] u/{c['author']} " f"{c['created_utc'][:10]}{op}: {body}"
            )
            rendered += 1
            walk(c["id"], depth + 1)

    walk(f"t3_{pid}", 0)
    if truncated:
        lines.append(f"(comments after the first {max_comments} not shown)")
    return "\n".join(lines)


def cmd_bodies(doc: dict, ids: list, *, max_chars: int = 1000, as_json: bool = False) -> str:
    posts = {p["id"]: p for p in doc["data"].get("posts", [])}
    found = []
    unknown = []
    for raw in ids:
        pid = raw.removeprefix("t3_")
        post = posts.get(pid)
        if post is None:
            unknown.append(raw)
        else:
            found.append((pid, post))
    if not found:
        raise QueryError(
            f"None of the requested ids exist in {doc['meta'].get('month')}: "
            f"{', '.join(unknown or ids)}"
        )

    if as_json:
        payload = []
        for pid, post in found:
            body = post.get("selftext") or ""
            payload.append(
                {
                    "id": pid,
                    "title": post.get("title"),
                    "author": post.get("author"),
                    "created_utc": post["created_utc"],
                    "selftext": body[:max_chars],
                    "truncated": len(body) > max_chars,
                }
            )
        return json.dumps({"bodies": payload, "unknown_ids": unknown}, indent=2)

    lines = []
    for pid, post in found:
        lines.append(
            f"t3_{pid}  {post['created_utc'][:10]}  u/{post.get('author')}  {post.get('title')}"
        )
        body = post.get("selftext") or ""
        if body:
            lines.append(body[:max_chars])
            if len(body) > max_chars:
                lines.append(f"(truncated at {max_chars} chars)")
        else:
            lines.append("(no selftext)")
        lines.append("")
    if unknown:
        lines.append(f"(unknown ids: {', '.join(unknown)})")
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _search_docs(data_dir: str, months: list):
    """Load available months; skip missing ones (reported in output, not an error)."""
    docs = []
    missing = []
    for m in months:
        try:
            docs.append((m, load_month(data_dir, m)))
        except QueryError:
            missing.append(m)
    return docs, missing


def _snippet(text: str, needle: str, width: int = 160) -> str:
    flat = _flatten_body(text)
    idx = flat.lower().find(needle.lower())
    if idx < 0:
        return flat[:width]
    start = max(0, idx - 30)
    return flat[start : start + width]


def cmd_search(
    docs: list,
    *,
    query: str,
    author: str | None = None,
    top: int = 20,
    as_json: bool = False,
    missing: list | None = None,
) -> str:
    hits = []
    for _month, doc in docs:
        for p in doc["data"].get("posts", []):
            haystack = f"{p.get('title', '')}\n{p.get('selftext', '')}"
            if query.lower() in haystack.lower():
                if author and (p.get("author") or "").lower() != author.lower():
                    continue
                hits.append(
                    {
                        "created_utc": p["created_utc"],
                        "kind": "post",
                        "thread_id": p["id"],
                        "title": p.get("title"),
                        "author": p.get("author"),
                        "snippet": _snippet(p.get("title", ""), query),
                    }
                )
        for c in doc["data"].get("comments", []):
            if query.lower() in (c.get("body") or "").lower():
                if author and (c.get("author") or "").lower() != author.lower():
                    continue
                hits.append(
                    {
                        "created_utc": c["created_utc"],
                        "kind": "comment",
                        "thread_id": c["thread_id"],
                        "comment_id": c["id"],
                        "thread_title": c.get("thread_title"),
                        "author": c.get("author"),
                        "snippet": _snippet(c.get("body") or "", query),
                    }
                )
    hits.sort(key=lambda h: h["created_utc"])
    hits = hits[:top]

    if as_json:
        return json.dumps({"matches": hits, "missing_months": missing or []}, indent=2)

    lines = [f"(no community file for {m})" for m in missing or []]
    if not hits:
        lines.append("No matches for the query in the given window.")
        return "\n".join(lines)
    for h in hits:
        who = f" u/{h['author']}" if h.get("author") else ""
        title = h.get("thread_title") or h.get("title") or ""
        if h["kind"] == "post":
            lines.append(f"{h['created_utc'][:10]}  [post]     t3_{h['thread_id']}{who}")
        else:
            lines.append(
                f"{h['created_utc'][:10]}  [comment]  t3_{h['thread_id']}  "
                f"t1_{h['comment_id']}{who}"
            )
        if title:
            lines.append(f"           thread: {title[:60]}")
        lines.append(f"           \"{h['snippet']}\"")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
