"""
End-to-end-ish tests for fetch helpers, using fake PRAW objects so no network.
"""

from __future__ import annotations

from datetime import date
from typing import Any, List
from unittest.mock import patch

from sotd.utils import parse_thread_date


# ------------------------------------------------------------------ #
# Fake PRAW objects                                                  #
# ------------------------------------------------------------------ #


class FakeSubmission:
    def __init__(self, sid: str, title: str) -> None:
        self.id = sid
        self.title = title
        self.permalink = f"/r/wetshaving/comments/{sid}/"
        self.created_utc = 1_700_000_000
        self.num_comments = 0
        self.link_flair_text = None
        self.author = "AutoModerator"


class FakeSubreddit:
    def __init__(self) -> None:
        self.last_query: str | None = None

    def search(self, query: str, *, sort: str, syntax: str):
        self.last_query = query
        yield from [
            FakeSubmission("good1", "Sat SOTD - May 3"),
            FakeSubmission("badxx", "Weekly Question Thread"),
            FakeSubmission("good2", "SOTD Thread May 5, 2025"),
        ]


# ----------------- comment stubs so fetch_top_level_comments works ---- #


class DummyComment:
    def __init__(self, cid: str):
        self.id = cid
        self.author = "tester"
        self.body = "comment body"
        self.created_utc = 1_700_000_100
        self.is_root = True
        self.permalink = f"/x/{cid}/"


class DummySubmission:
    """Submission stub for comment fetcher."""

    def __init__(self, sid: str):
        self.id = sid
        self.title = "Dummy"
        self.permalink = f"/r/wetshaving/comments/{sid}/dummy/"
        self.created_utc = 1_700_000_000
        self.num_comments = 2
        self.link_flair_text = None

        class _Comments(list):  # type: ignore
            def replace_more(self, limit: int = 0):  # noqa: D401
                return None

        self.comments = _Comments([DummyComment(f"{sid}_1"), DummyComment(f"{sid}_2")])


class FakeReddit:
    def __init__(self, *args, **kwargs) -> None:  # noqa: D401
        self._sub = FakeSubreddit()

    def subreddit(self, name: str) -> FakeSubreddit:  # noqa: D401
        return self._sub

    def submission(self, sid: str):  # noqa: D401
        return DummySubmission(sid)


# ------------------------------------------------------------------ #
# Tests                                                              #
# ------------------------------------------------------------------ #


@patch("sotd.fetch.reddit.get_reddit", return_value=FakeReddit())
def test_filter_valid_threads_and_missing(_patched) -> None:
    from sotd.fetch.reddit import filter_valid_threads, search_threads

    year, month = 2025, 5
    raw = list(_patched.return_value._sub.search("dummy", sort="new", syntax="lucene"))
    valid = filter_valid_threads(raw, year, month)

    assert [s.id for s in valid] == ["good1", "good2"]

    parsed_days: list[int] = []
    for s in valid:
        d = parse_thread_date(s.title, year)
        assert d is not None
        parsed_days.append(d.day)
    assert parsed_days == [3, 5]

    results: List[Any] = search_threads("wetshaving", year, month)
    assert len(results) == 2


def test_missing_day_calc() -> None:
    """_calc_missing should detect all calendar gaps."""
    from sotd.fetch.run import _calc_missing

    class Dummy:
        def __init__(self, title: str):
            self.title = title

    threads = [Dummy("SOTD Thread May 1, 2025"), Dummy("SOTD Thread May 3, 2025")]
    missing = _calc_missing(2025, 5, threads)

    # Basic expectations
    assert date(2025, 5, 2) in missing  # key gap detected
    assert len(missing) == 29  # 31 days in May − 2 present
