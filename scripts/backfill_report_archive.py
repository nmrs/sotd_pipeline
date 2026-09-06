#!/usr/bin/env python3
"""Download all top-level Reddit posts by u/jimm262 into one JSONL file.

No classification — titles are reviewed manually afterwards. The JSONL keeps
selftext so report bodies can be archived without a second Reddit fetch.
"""

import argparse
import json
from pathlib import Path

REPORT_USER = "jimm262"


def fetch_posts(redditor) -> list:
    """Fetch all submissions for a redditor as plain dicts (all subreddits)."""
    posts = []
    for thing in redditor.submissions.new(limit=None):
        posts.append(
            {
                "id": thing.id,
                "title": thing.title,
                "selftext": thing.selftext,
                "subreddit": thing.subreddit.display_name,
                "created_utc": thing.created_utc,
                "permalink": thing.permalink,
            }
        )
    return posts


def save_raw_snapshot(posts: list, path: Path) -> None:
    """Write posts as JSONL so review can happen offline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=REPORT_USER)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data") / "report_archive" / "_reddit_raw" / "posts.jsonl",
    )
    args = parser.parse_args()

    from sotd.fetch.reddit import get_reddit

    reddit = get_reddit()
    posts = fetch_posts(reddit.redditor(args.username))
    save_raw_snapshot(posts, args.out)
    print(f"Fetched {len(posts)} submissions by u/{args.username}")
    if len(posts) >= 1000 and len(posts) % 1000 == 0:
        print(
            "WARNING: count is a multiple of 1000 - Reddit listing cap may "
            "have truncated older posts"
        )
    wetshaving = [p for p in posts if p["subreddit"].casefold() == "wetshaving"]
    print(f"Saved to {args.out} ({len(wetshaving)} in r/wetshaving)")


if __name__ == "__main__":
    main()
