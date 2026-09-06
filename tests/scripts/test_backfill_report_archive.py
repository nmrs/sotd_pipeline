"""Tests for the Reddit report backfill script (fetch u/jimm262 posts to file)."""

import json
from pathlib import Path

from scripts.backfill_report_archive import fetch_posts, save_raw_snapshot


def _post(
    id: str,
    title: str,
    selftext: str = "REPORT BODY",
    subreddit: str = "wetshaving",
    created_utc: float = 0.0,
) -> dict:
    return {
        "id": id,
        "title": title,
        "selftext": selftext,
        "subreddit": subreddit,
        "created_utc": created_utc,
        "permalink": f"/r/wetshaving/comments/{id}/x/",
    }


# --------------------------------------------------------------------------- #
# fetch_posts (duck-typed PRAW redditor)
# --------------------------------------------------------------------------- #
class FakeThing:
    def __init__(self, d: dict) -> None:
        self.id = d["id"]
        self.title = d["title"]
        self.selftext = d["selftext"]
        self.created_utc = d["created_utc"]
        self.permalink = d["permalink"]
        self.subreddit = type("Sub", (), {"display_name": d["subreddit"]})()


class FakeRedditor:
    class _Sub:
        def __init__(self, things: list) -> None:
            self._things = things

        def new(self, limit=None, params=None):
            return iter(self._things)

    def __init__(self, things: list) -> None:
        self._things = things

    @property
    def submissions(self):
        return self._Sub(self._things)


class TestFetchPosts:
    def test_fetch_posts_aggregates_and_converts(self) -> None:
        things = [
            FakeThing(_post("abc", "Hardware Report - June 2025", created_utc=1_700_000_000)),
            FakeThing(_post("def", "casual post", "hello", created_utc=1_700_000_100)),
        ]
        posts = fetch_posts(FakeRedditor(things))
        assert len(posts) == 2
        assert posts[0]["id"] == "abc"
        assert posts[0]["title"] == "Hardware Report - June 2025"
        assert posts[0]["subreddit"] == "wetshaving"
        assert posts[1]["selftext"] == "hello"


# --------------------------------------------------------------------------- #
# save_raw_snapshot
# --------------------------------------------------------------------------- #
class TestSaveRawSnapshot:
    def test_roundtrip_jsonl(self, tmp_path: Path) -> None:
        posts = [_post("abc", "Hardware Report - June 2025", created_utc=1_700_000_000)]
        out = tmp_path / "posts.jsonl"
        save_raw_snapshot(posts, out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["id"] == "abc"
