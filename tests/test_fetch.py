"""
Unit tests for the minimal Reddit search helper.

• We monkey-patch sotd.fetch.reddit.get_reddit so no network access occurs.
• Type annotations are relaxed to avoid invariant-list conflicts with Pylance.
"""

from __future__ import annotations

from typing import Any, List
from unittest.mock import patch

import pytest

# ------------------------------------------------------------------ #
# Fake PRAW-like objects                                              #
# ------------------------------------------------------------------ #


class FakeSubmission:  # minimal subset we need
    def __init__(self, sid: str, title: str) -> None:
        self.id = sid
        self.title = title


class FakeSubreddit:
    def __init__(self) -> None:
        self.last_query: str | None = None

    # mimic praw.Subreddit.search
    def search(self, query: str, *, sort: str, syntax: str):  # noqa: D401
        self.last_query = query
        yield from [
            FakeSubmission("abc123", "Monday SOTD Thread - Jan 1, 2025"),
            FakeSubmission("def456", "Tuesday SOTD Thread - Jan 2, 2025"),
        ]


class FakeReddit:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        self._sub = FakeSubreddit()

    def subreddit(self, name: str) -> FakeSubreddit:
        assert name == "wetshaving"
        return self._sub


# ------------------------------------------------------------------ #
# Test search_threads                                                 #
# ------------------------------------------------------------------ #


@patch("sotd.fetch.reddit.get_reddit", return_value=FakeReddit())
def test_search_threads_builds_expected_query(
    _mock_get_reddit, monkeypatch: pytest.MonkeyPatch
) -> None:
    """search_threads() should build the correct flair query string."""
    # Ensure env vars exist so get_reddit does not raise
    monkeypatch.setenv("REDDIT_CLIENT_ID", "x")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "y")
    monkeypatch.setenv("REDDIT_USER_AGENT", "z")

    from sotd.fetch.reddit import search_threads

    # We don't care about exact types here, only count & behaviour
    results: List[Any] = search_threads("wetshaving", 2025, 3, debug=False)

    # Two fake submissions should be returned
    assert len(results) == 2

    # Verify the underlying query string that FakeSubreddit received
    fake_subreddit: FakeSubreddit = _mock_get_reddit.return_value._sub  # type: ignore[attr-defined]
    assert fake_subreddit.last_query == "flair:SOTD mar march 2025"
