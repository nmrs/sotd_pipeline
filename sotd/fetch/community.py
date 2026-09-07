"""Fetch the full r/wetshaving community record for one or more months.

Every post in the target month (SOTD daily threads included) plus its full
comment tree is stored to ``data/community/YYYY-MM.json``::

    {"meta": {...}, "data": {"posts": [...], "comments": [...]}}

This is a sidecar to the 6-phase pipeline: nothing in extract..report consumes
this data. The ``community_query`` CLI is its access surface (agent consumption
is a later project). The pipeline's own ``data/comments/`` store (top-level SOTD
comments only) is never reused here — everything is fetched fresh from Reddit.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from itertools import islice
from typing import List, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError

from praw.models import Comment
from tqdm import tqdm

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.cli_utils.date_span import month_span
from sotd.fetch.merge import merge_records
from sotd.fetch.reddit import get_reddit, safe_call
from sotd.fetch.save import load_month_file
from sotd.utils.data_dir import get_data_dir
from sotd.utils.file_io import load_json_data, save_json_data
from sotd.utils.logging_config import setup_pipeline_logging, should_disable_tqdm

logger = logging.getLogger(__name__)

# Discovery stops here even if the month boundary was never reached
# (30 batches x 100 posts; a target month needs ~4).
PAGINATION_CAP = 3000


# --------------------------------------------------------------------------- #
# record building                                                             #
# --------------------------------------------------------------------------- #
def _iso(created_utc: float) -> str:
    return datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def build_post_record(sub, *, in_pipeline: Optional[bool]) -> dict:
    rec = {
        "id": sub.id,
        "title": sub.title,
        "selftext": getattr(sub, "selftext", "") or "",
        "author": str(sub.author) if sub.author else "[deleted]",
        "created_utc": _iso(sub.created_utc),
        "score": int(getattr(sub, "score", 0) or 0),
        "num_comments": int(getattr(sub, "num_comments", 0) or 0),
        "flair": sub.link_flair_text,
        "url": f"https://www.reddit.com{sub.permalink}",
        "locked": bool(getattr(sub, "locked", False)),
        "stickied": bool(getattr(sub, "stickied", False)),
    }
    if in_pipeline is not None:
        rec["in_pipeline"] = in_pipeline
    return rec


def build_comment_record(c, thread_id: str, thread_title: str) -> dict:
    return {
        "id": c.id,
        "thread_id": thread_id,
        "thread_title": thread_title,
        "parent_id": c.parent_id,
        "author": str(c.author) if c.author else "[deleted]",
        "created_utc": _iso(c.created_utc),
        "body": c.body,
        "score": int(getattr(c, "score", 0) or 0),
        "is_submitter": bool(getattr(c, "is_submitter", False)),
    }


# --------------------------------------------------------------------------- #
# file I/O                                                                    #
# --------------------------------------------------------------------------- #
def write_community_file(path, meta: dict, posts: list[dict], comments: list[dict]) -> None:
    save_json_data({"meta": meta, "data": {"posts": posts, "comments": comments}}, path, indent=2)


def load_community_file(path):
    """Return (meta, {"posts": [...], "comments": [...]}) if the file exists, else None."""
    if not path.is_file():
        return None
    try:
        obj = load_json_data(path)
        return obj["meta"], obj["data"]
    except (KeyError, ValueError):
        return None


def load_sotd_ids(data_dir, year: int, month: int) -> Optional[Set[str]]:
    """Return SOTD thread IDs for the month, or None when the threads file is absent."""
    path = get_data_dir(data_dir) / "threads" / f"{year:04d}-{month:02d}.json"
    existing = load_month_file(path)
    if existing is None:
        return None
    return {t["id"] for t in existing[1]}


# --------------------------------------------------------------------------- #
# forward discovery                                                            #
# --------------------------------------------------------------------------- #
def discover_month_posts(subreddit, year: int, month: int) -> Tuple[List, bool]:
    """Pull ``subreddit.new()`` until posts older than the month appear.

    Returns (in_month_posts, boundary_reached). ``in_month_posts`` is
    newest-first. ``boundary_reached`` is False when the pagination cap trips
    before the boundary — the caller must treat that month as partial.
    """
    month_str = f"{year:04d}-{month:02d}"
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end_exclusive = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )

    def _listing():
        # lazy generator so the listing's HTTP calls stay inside safe_call;
        # logs a heartbeat every 1000 items so long silent stretches are visible
        for i, sub in enumerate(subreddit.new(limit=None), 1):
            if i % 1000 == 0:
                logger.info(f"{month_str}: listing pulled {i} items…")
            yield sub

    pulled = safe_call(lambda: list(islice(_listing(), PAGINATION_CAP)))
    in_month: List = []
    boundary_reached = False
    for sub in pulled or []:
        dt = datetime.fromtimestamp(sub.created_utc, tz=timezone.utc)
        if dt < start:
            # listings are newest-first: everything after this is older
            boundary_reached = True
            break
        if dt < end_exclusive:
            in_month.append(sub)
    if not boundary_reached and pulled is not None and len(pulled) < PAGINATION_CAP:
        # listing exhausted without crossing the boundary
        boundary_reached = True
    logger.info(
        f"{month_str}: listing discovered {len(in_month)} posts "
        f"(boundary {'reached' if boundary_reached else 'not reached'})"
    )
    return in_month, boundary_reached


def fetch_all_comments(submission) -> List:
    """Return every comment under *submission* at all depths.

    Unlike the SOTD fetch (top-level shaves only), community context needs the
    nested replies — that is where the conversation lives. MoreComment stubs
    that survive a failed replace_more are dropped.
    """
    safe_call(submission.comments.replace_more, limit=None)
    return [c for c in submission.comments.list() if isinstance(c, Comment)]


# --------------------------------------------------------------------------- #
# pullpush archive discovery (IDs only; Reddit is the content source)         #
# --------------------------------------------------------------------------- #
PULLPUSH_UA = "sotd-pipeline-community-fetch/1.0 (personal research tool)"
PULLPUSH_SLEEP = 4.0  # seconds between archive requests; PullPush 429s hot callers


def _pullpush_get(url: str) -> Optional[List]:
    """GET one PullPush search page, returning its ``data`` array.

    Retries a 429 twice (PullPush rate-limits hot callers hard); returns None
    on any failure so callers treat the archive as best-effort.
    """
    for attempt in range(3):
        req = urllib.request.Request(url, headers={"User-Agent": PULLPUSH_UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                obj = json.load(resp)
        except HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                logger.warning("PullPush rate limit hit (429); cooling off…")
                time.sleep(15)
                continue
            logger.warning(f"PullPush request failed: {exc}")
            return None
        except Exception as exc:
            logger.warning(f"PullPush request failed: {exc}")
            return None
        data = obj.get("data") if isinstance(obj, dict) else None
        return data if isinstance(data, list) else None
    return None


def pullpush_submission_ids(year: int, month: int) -> Set[str]:
    """Submission IDs the PullPush archive holds for the month (IDs only).

    The archive is a *discovery* source: the caller converts each ID via
    ``reddit.submission(id=...)`` — not subject to the ~1000-item listing
    limit — and fetches comment trees fresh from Reddit.
    """
    start = int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp())
    end_dt = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    end = int(end_dt.timestamp())

    ids: Set[str] = set()
    cursor = end
    page_no = 0
    while True:
        page_no += 1
        url = (
            "https://api.pullpush.io/reddit/search/submission/"
            f"?subreddit=wetshaving&after={start}&before={cursor}&size=100&sort=desc"
        )
        data = _pullpush_get(url)
        if not data:
            break
        page_ids = {s["id"] for s in data if s.get("id") and start <= int(s["created_utc"]) < end}
        if page_ids <= ids:
            break  # archive served a page we already have; stop instead of looping
        ids |= page_ids
        oldest = min(int(s["created_utc"]) for s in data)
        logger.info(
            f"pullpush: page {page_no}: {len(data)} ids "
            f"(oldest {datetime.fromtimestamp(oldest, tz=timezone.utc):%Y-%m-%d})"
        )
        if oldest <= start or len(data) < 100:
            break
        cursor = oldest
        time.sleep(PULLPUSH_SLEEP)
    logger.info(f"pullpush: {len(ids)} archive ids across {page_no} pages")
    return ids


def discover_via_pullpush(reddit, year: int, month: int) -> List:
    """Archive-discovered posts: PullPush supplies IDs, Reddit supplies content.

    IDs that no longer resolve on Reddit (deleted posts) are skipped — the same
    dead-seed skip as thread seeding.
    """
    ids = pullpush_submission_ids(year, month)
    out: List = []
    for sid in sorted(ids):
        sub = safe_call(lambda _sid=sid: reddit.submission(id=_sid))
        title = safe_call(lambda _s=sub: _s.title) if sub is not None else None
        if title:
            out.append(sub)
    logger.info(
        f"{year:04d}-{month:02d}: pullpush: resolved {len(out)} of {len(ids)} archive ids on Reddit"
    )
    return out


# --------------------------------------------------------------------------- #
# backfill discovery (months .new() cannot reach)                             #
# --------------------------------------------------------------------------- #
def discover_via_search(subreddit, start_ts: int, end_ts: int) -> List:
    """Reddit search over a UTC timestamp window (lucene ``timestamp:`` syntax).

    Returns [] when the search fails for any reason (unsupported/unindexed
    syntax, rate limit, iteration error) — the recorded discovery meta then
    simply shows no contribution from this strategy.
    """
    query = f"timestamp:{start_ts}..{end_ts}"
    search_fn = getattr(subreddit, "search", None)
    if search_fn is None:
        return []
    try:
        # praw's search() is lazy: the HTTP call happens during iteration, so
        # list() must run inside safe_call to keep failures contained
        raw = safe_call(
            lambda: list(search_fn(query, sort="new", syntax="lucene", time_filter="all"))
        )
    except Exception as e:
        logger.warning(f"timestamp search unavailable: {e}")
        return []
    return list(raw) if raw else []


def era_authors(data_dir, months: Sequence[str], top_n: int = 100) -> List[str]:
    """Most active comment authors across *months* (from the pipeline's SOTD comments)."""
    counts: dict = {}
    for m in months:
        existing = load_month_file(get_data_dir(data_dir) / "comments" / f"{m}.json")
        if existing is None:
            continue
        for c in existing[1]:
            a = c.get("author")
            if a and a != "[deleted]":
                counts[a] = counts.get(a, 0) + 1
    return [a for a, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:top_n]]


def discover_via_authors(reddit, authors: Sequence[str], start_ts: int, end_ts: int) -> List:
    """Submission histories of active authors, filtered to the month window."""
    out: List = []
    seen: Set[str] = set()
    for name in authors:
        redditor = safe_call(reddit.redditor, name)
        if redditor is None:
            continue
        stream = safe_call(lambda _r=redditor: list(islice(_r.submissions.new(limit=1000), 1000)))
        for sub in stream or []:
            if start_ts <= sub.created_utc <= end_ts and sub.id not in seen:
                seen.add(sub.id)
                out.append(sub)
    return out


def _backfill_posts(reddit, subreddit, year: int, month: int, sotd_ids, data_dir):
    """Best-effort discovery union for months ``new_listing`` cannot reach.

    Strategies: known SOTD thread IDs (IDs seeded from data/threads/ — full
    trees are fetched fresh later; the pipeline's top-level-only comment store
    is never reused), PullPush archive IDs (IDs only, converted to fresh
    submissions), timestamp search, and active-author submission histories.
    A strategy is listed only when it contributed at least one post.
    Returns (posts, strategies_used, per_strategy_raw_counts).
    """
    month_str = f"{year:04d}-{month:02d}"
    start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
    end_dt = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )
    start_ts, end_ts = int(start_dt.timestamp()), int(end_dt.timestamp())

    found: dict = {}
    strategies: List[str] = []
    per_strategy: dict = {}

    if sotd_ids:
        logger.info(f"{month_str}: thread_seed: resolving {len(sotd_ids)} known SOTD threads…")
        for sid in sotd_ids:
            sub = safe_call(lambda _sid=sid: reddit.submission(id=_sid))
            title = safe_call(lambda _s=sub: _s.title) if sub is not None else None
            if sub is not None and title:
                found[sub.id] = sub
        per_strategy["thread_seed"] = len(found)
        logger.info(f"{month_str}: thread_seed: resolved {len(found)} of {len(sotd_ids)}")
        if found:
            strategies.append("thread_seed")

    search_posts = discover_via_search(subreddit, start_ts, end_ts)
    per_strategy["timestamp_search"] = len(search_posts)
    logger.info(f"{month_str}: timestamp_search: found {len(search_posts)} posts")
    if search_posts:
        strategies.append("timestamp_search")
    for sub in search_posts:
        found.setdefault(sub.id, sub)

    pullpush_posts = discover_via_pullpush(reddit, year, month)
    per_strategy["pullpush"] = len(pullpush_posts)
    if pullpush_posts:
        strategies.append("pullpush")
    for sub in pullpush_posts:
        found.setdefault(sub.id, sub)

    authors = era_authors(data_dir, [month_str])
    logger.info(f"{month_str}: author_histories: scanning {len(authors)} era authors…")
    author_posts = discover_via_authors(reddit, authors, start_ts, end_ts)
    per_strategy["author_histories"] = len(author_posts)
    logger.info(
        f"{month_str}: author_histories: scanned {len(authors)} era authors, "
        f"found {len(author_posts)} posts"
    )
    if author_posts:
        strategies.append("author_histories")
    for sub in author_posts:
        found.setdefault(sub.id, sub)

    logger.info(
        f"{month_str}: backfill discovery: {len(found)} unique posts via strategies: "
        f"{', '.join(strategies) if strategies else '(none)'}"
    )
    return list(found.values()), strategies, per_strategy


# --------------------------------------------------------------------------- #
# month orchestration                                                         #
# --------------------------------------------------------------------------- #
def _process_month(year: int, month: int, args, *, reddit) -> dict:
    """Fetch + merge + save the community record for one calendar month."""
    month_str = f"{year:04d}-{month:02d}"
    data_dir = get_data_dir(args.data_dir)
    out_path = data_dir / "community" / f"{month_str}.json"

    sotd_ids = load_sotd_ids(args.data_dir, year, month)
    if sotd_ids is None:
        logger.warning(f"No threads file for {month_str}; posts will lack the in_pipeline flag")

    if args.force and out_path.exists():
        out_path.unlink()

    subreddit = reddit.subreddit("wetshaving")
    posts_new, boundary_reached = discover_month_posts(subreddit, year, month)
    # A listing that ENDED (rather than breaking at the boundary) is not proof
    # the month is complete: Reddit serves only ~1000 listing items, so for
    # months older than ~8 listings-worth the listing dies mid-history. Cross-
    # check against the known SOTD thread IDs — any missing means the month was
    # never fully enumerated, and the backfill strategies must engage.
    if boundary_reached and sotd_ids:
        missing_sotd = sotd_ids - {s.id for s in posts_new}
        if missing_sotd:
            logger.warning(
                f"{month_str}: listing ended without reaching the month boundary; "
                f"{len(missing_sotd)} known SOTD threads missing — engaging backfill discovery"
            )
            boundary_reached = False
    strategies_used = ["new_listing"]
    per_strategy = {"new_listing": len(posts_new)}
    if not boundary_reached:
        logger.warning(
            f"{month_str}: pagination cap reached before month boundary; "
            "falling back to backfill discovery"
        )
        backfill_posts, strategies, backfill_counts = _backfill_posts(
            reddit, subreddit, year, month, sotd_ids, args.data_dir
        )
        by_id = {s.id: s for s in posts_new}
        for s in backfill_posts:
            by_id.setdefault(s.id, s)
        posts_new = sorted(by_id.values(), key=lambda s: s.created_utc, reverse=True)
        strategies_used = strategies_used + [s for s in strategies if s not in strategies_used]
        per_strategy.update(backfill_counts)

    new_posts = [
        build_post_record(s, in_pipeline=None if sotd_ids is None else s.id in sotd_ids)
        for s in posts_new
    ]

    new_comments: List[dict] = []
    logger.info(f"{month_str}: fetching comment trees for {len(posts_new)} threads…")
    for sub in tqdm(posts_new, desc="Threads", unit="thread", disable=should_disable_tqdm()):
        for c in fetch_all_comments(sub) or []:
            new_comments.append(build_comment_record(c, sub.id, sub.title))

    existing = None if args.force else load_community_file(out_path)
    if existing is not None:
        _existing_meta, existing_data = existing
        posts = merge_records(existing_data["posts"], new_posts)
        comments = merge_records(existing_data["comments"], new_comments)
    else:
        posts = sorted(new_posts, key=lambda r: r["created_utc"])
        comments = sorted(new_comments, key=lambda r: r["created_utc"])

    if not posts and not comments and existing is None:
        logger.warning(f"No community data found for {month_str}; skipping file write.")
        return {
            "year": year,
            "month": month,
            "posts": 0,
            "comments": 0,
            "complete": boundary_reached,
        }

    meta = {
        "month": month_str,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(posts),
        "comment_count": len(comments),
        "in_pipeline_post_count": sum(1 for p in posts if p.get("in_pipeline")),
        "discovery": {
            "strategies": strategies_used,
            "complete": boundary_reached,
            "per_strategy": per_strategy,
        },
    }
    write_community_file(out_path, meta, posts, comments)
    logger.info(
        f"{month_str}: wrote {len(posts)} posts / {len(comments)} comments "
        f"(discovery: {', '.join(strategies_used)}, "
        f"{'complete' if boundary_reached else 'INCOMPLETE'})"
    )
    return {
        "year": year,
        "month": month,
        "posts": len(posts),
        "comments": len(comments),
        "complete": boundary_reached,
    }


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def get_parser() -> BaseCLIParser:
    return BaseCLIParser(
        description="Fetch the full community record (all posts + full comment trees)"
    )


def main(argv: Sequence[str] | None = None) -> int:
    setup_pipeline_logging(level=logging.INFO)
    try:
        parser = get_parser()
        args = parser.parse_args(argv)
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        months = month_span(args)
        reddit = get_reddit()

        results = []
        for year, month in tqdm(months, desc="Months", unit="month", disable=should_disable_tqdm()):
            results.append(_process_month(year, month, args, reddit=reddit))

        if results:
            total_posts = sum(r["posts"] for r in results)
            total_comments = sum(r["comments"] for r in results)
            incomplete = [f"{r['year']:04d}-{r['month']:02d}" for r in results if not r["complete"]]
            logger.info(
                f"Community fetch complete: {total_posts} posts, {total_comments} comments"
                + (f"; incomplete discovery: {', '.join(incomplete)}" if incomplete else "")
            )
        return 0
    except KeyboardInterrupt:
        logger.info("Community fetch interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Community fetch failed: {e}")
        import traceback

        traceback.print_exc()
        return 1
