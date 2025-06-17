"""Comprehensive tests for reddit.py module."""

import os
import time
from unittest.mock import Mock, patch

import pytest
from praw.models import Submission
from prawcore.exceptions import TooManyRequests, RequestException
import requests

from sotd.fetch.reddit import (
    get_reddit,
    _require_env,
    search_threads,
    filter_valid_threads,
    fetch_top_level_comments,
    safe_call,
)


# --------------------------------------------------------------------------- #
# Test fixtures and helper classes                                            #
# --------------------------------------------------------------------------- #
class MockSubmission(Submission):
    """Mock Reddit submission for testing."""

    def __init__(self, submission_id: str, title: str, created_utc: int = 1609459200):
        mock_reddit = Mock()
        super().__init__(
            mock_reddit, submission_id
        )  # Initialize base class with mock reddit instance
        self._title = title
        self._created_utc = created_utc
        self._permalink = f"/r/test/comments/{submission_id}/"
        self._num_comments = 5
        self._link_flair_text = "SOTD"
        self._author = "test_user"

        # Mock comments
        self._comments = Mock()
        self._comments.replace_more = Mock()
        self._comments.list = Mock(
            return_value=[
                MockComment("c1", is_root=True),
                MockComment("c2", is_root=False),  # Reply
                MockComment("c3", is_root=True),
            ]
        )

    @property
    def title(self):
        return self._title

    @property
    def created_utc(self):
        return self._created_utc

    @property
    def permalink(self):
        return self._permalink

    @property
    def num_comments(self):
        return self._num_comments

    @property
    def link_flair_text(self):
        return self._link_flair_text

    @property
    def author(self):
        return self._author

    @property
    def comments(self):
        return self._comments


class MockComment:
    """Mock Reddit comment for testing."""

    def __init__(self, comment_id: str, body: str = "Test comment", is_root: bool = True):
        self.id = comment_id
        self.body = body
        self.created_utc = 1609459200
        self.author = "comment_user"
        self.permalink = f"/r/test/comments/sub/{comment_id}/"
        self.is_root = is_root


class MockSubreddit:
    """Mock Reddit subreddit for testing."""

    def __init__(self, search_results=None):
        self.search_results = search_results or []

    def search(self, query, sort="relevance", syntax="lucene"):  # pylint: disable=unused-argument
        """Mock search method that returns predefined results regardless of query."""
        return iter(self.search_results)


class MockReddit:
    """Mock Reddit instance for testing."""

    def __init__(self, subreddit_mock=None):
        self._subreddit_mock = subreddit_mock or MockSubreddit()

    def subreddit(self, _name):
        return self._subreddit_mock


class MockRateLimitException(TooManyRequests):
    """Mock rate limit exception with configurable attributes."""

    def __init__(self, sleep_time=None, retry_after=None):
        # Create a minimal Response object
        response = requests.Response()
        response.status_code = 429
        super().__init__(response)
        if sleep_time is not None:
            self.sleep_time = sleep_time
        if retry_after is not None:
            self.retry_after = retry_after


# --------------------------------------------------------------------------- #
# Environment variable tests                                                   #
# --------------------------------------------------------------------------- #
def test_require_env_success():
    """_require_env should return value when environment variable exists."""
    with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
        result = _require_env("TEST_VAR")
        assert result == "test_value"


def test_require_env_missing():
    """_require_env should raise RuntimeError when environment variable is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="Missing environment variable: MISSING_VAR"):
            _require_env("MISSING_VAR")


def test_require_env_empty():
    """_require_env should raise RuntimeError when environment variable is empty."""
    with patch.dict(os.environ, {"EMPTY_VAR": ""}):
        with pytest.raises(RuntimeError, match="Missing environment variable: EMPTY_VAR"):
            _require_env("EMPTY_VAR")


# --------------------------------------------------------------------------- #
# Reddit instance creation tests                                               #
# --------------------------------------------------------------------------- #
@patch("praw.Reddit")
def test_get_reddit_success(mock_reddit_class):
    """get_reddit should create PRAW instance successfully."""
    mock_instance = Mock()
    mock_reddit_class.return_value = mock_instance

    result = get_reddit()

    assert result == mock_instance
    mock_reddit_class.assert_called_once_with()


@patch("praw.Reddit")
def test_get_reddit_configuration_error(mock_reddit_class):
    """get_reddit should propagate PRAW configuration errors."""
    mock_reddit_class.side_effect = Exception("Configuration error")

    with pytest.raises(Exception, match="Configuration error"):
        get_reddit()


# --------------------------------------------------------------------------- #
# Safe call rate limiting tests (extended)                                     #
# --------------------------------------------------------------------------- #
def test_safe_call_rate_limit_with_sleep_time(monkeypatch, capsys):
    """safe_call should use sleep_time attribute when available."""
    calls = 0

    def failing_function():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise MockRateLimitException(sleep_time=5)
        return "success"

    sleep_calls = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    result = safe_call(failing_function)

    assert result == "success"
    assert calls == 2
    assert sleep_calls == [6]  # sleep_time + 1

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit; sleeping 0m 5s…" in output


def test_safe_call_rate_limit_with_retry_after(monkeypatch, capsys):
    """safe_call should fall back to retry_after when sleep_time not available."""
    calls = 0

    def failing_function():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise MockRateLimitException(retry_after=3)
        return "success"

    sleep_calls = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    result = safe_call(failing_function)

    assert result == "success"
    assert sleep_calls == [4]  # retry_after + 1

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit; sleeping 0m 3s…" in output


def test_safe_call_rate_limit_no_timing_info(monkeypatch, capsys):
    """safe_call should use default 60s when no timing attributes available."""
    calls = 0

    def failing_function():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise MockRateLimitException()
        return "success"

    sleep_calls = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    result = safe_call(failing_function)

    assert result == "success"
    assert sleep_calls == [61]  # default 60 + 1

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit; sleeping 1m 0s…" in output


def test_safe_call_rate_limit_double_failure():
    """safe_call should not retry more than once."""

    def always_failing():
        raise MockRateLimitException(sleep_time=1)

    with pytest.raises(TooManyRequests):
        safe_call(always_failing)


def test_safe_call_with_arguments():
    """safe_call should pass through function arguments correctly."""

    def function_with_args(a, b, c=None):
        return f"{a}-{b}-{c}"

    result = safe_call(function_with_args, "arg1", "arg2", c="kwarg")
    assert result == "arg1-arg2-kwarg"


def test_safe_call_other_exceptions():
    """safe_call should return None for non-rate-limit exceptions."""

    def failing_function():
        raise RequestException(
            Exception("Reddit API error"),
            request_args=("test",),
            request_kwargs={},
        )

    result = safe_call(failing_function)
    assert not result  # Should return None for non-rate-limit exceptions


# --------------------------------------------------------------------------- #
# Search threads tests                                                         #
# --------------------------------------------------------------------------- #
def test_search_threads_basic():
    """search_threads should find and filter threads correctly."""
    submissions = [
        MockSubmission("s1", "SOTD Thread May 01, 2025"),
        MockSubmission("s2", "SOTD Thread May 02, 2025"),
        MockSubmission("s3", "Weekly Recap"),  # Should be filtered out
    ]

    mock_subreddit = MockSubreddit(submissions)
    mock_reddit = MockReddit(mock_subreddit)

    with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
        result = search_threads("wetshaving", 2025, 5)

    assert len(result) == 2
    assert result[0].id == "s1"
    assert result[1].id == "s2"


def test_search_threads_deduplication():
    """search_threads should deduplicate submissions by ID across multiple queries."""
    # Same submission returned by both queries
    submission = MockSubmission("duplicate", "SOTD Thread May 01, 2025")

    mock_subreddit = MockSubreddit([submission, submission])
    mock_reddit = MockReddit(mock_subreddit)

    with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
        result = search_threads("wetshaving", 2025, 5)

    # Should only return one copy despite being in both query results
    assert len(result) == 1
    assert result[0].id == "duplicate"


def test_search_threads_debug_output(capsys):
    """search_threads should print debug information when debug=True."""
    submission = MockSubmission("s1", "SOTD Thread May 01, 2025")
    mock_subreddit = MockSubreddit([submission])
    mock_reddit = MockReddit(mock_subreddit)

    with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
        search_threads("wetshaving", 2025, 5, debug=True)

    output = capsys.readouterr().out
    assert "[DEBUG] Search query: 'flair:SOTD may may 2025'" in output
    assert "[DEBUG] Search query: 'flair:SOTD may may 2025SOTD'" in output
    assert "[DEBUG] PRAW raw results for" in output
    assert "[DEBUG] Combined raw results (deduped):" in output
    assert "[DEBUG] Valid threads:" in output


def test_search_threads_reddit_api_error():
    """search_threads should handle Reddit API errors appropriately."""
    mock_subreddit = Mock()
    mock_subreddit.search.side_effect = RequestException(
        Exception("Reddit API Error"),
        request_args=("flair:SOTD may may 2025",),
        request_kwargs={"sort": "relevance", "syntax": "lucene"},
    )
    mock_reddit = MockReddit(mock_subreddit)

    with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
        result = search_threads("wetshaving", 2025, 5)
        assert not result  # Should return empty list when safe_call returns None


# --------------------------------------------------------------------------- #
# Filter valid threads tests                                                   #
# --------------------------------------------------------------------------- #
def test_filter_valid_threads_basic():
    """filter_valid_threads should keep only threads with valid dates."""
    submissions = [
        MockSubmission("valid1", "SOTD Thread May 01, 2025"),
        MockSubmission("valid2", "SOTD Thread May 15, 2025"),
        MockSubmission("invalid1", "Weekly Discussion"),
        MockSubmission("invalid2", "SOTD Thread June 01, 2025"),  # Wrong month
    ]

    result = filter_valid_threads(submissions, 2025, 5)

    assert len(result) == 2
    assert result[0].id == "valid1"
    assert result[1].id == "valid2"


def test_filter_valid_threads_sorting():
    """filter_valid_threads should sort threads by date."""
    submissions = [
        MockSubmission("day15", "SOTD Thread May 15, 2025"),
        MockSubmission("day01", "SOTD Thread May 01, 2025"),
        MockSubmission("day10", "SOTD Thread May 10, 2025"),
    ]

    result = filter_valid_threads(submissions, 2025, 5)

    assert len(result) == 3
    assert result[0].id == "day01"  # May 1
    assert result[1].id == "day10"  # May 10
    assert result[2].id == "day15"  # May 15


def test_filter_valid_threads_debug_output(capsys):
    """filter_valid_threads should print debug information when debug=True."""
    submissions = [
        MockSubmission("valid", "SOTD Thread May 01, 2025"),
        MockSubmission("invalid", "Weekly Discussion"),
    ]

    filter_valid_threads(submissions, 2025, 5, debug=True)

    output = capsys.readouterr().out
    assert "[DEBUG] Skip (no-date)" in output
    assert "[DEBUG] Valid threads:" in output


def test_filter_valid_threads_wrong_month_debug(capsys):
    """filter_valid_threads should debug wrong month submissions."""
    submissions = [
        MockSubmission("wrong_month", "SOTD Thread June 01, 2025"),
    ]

    filter_valid_threads(submissions, 2025, 5, debug=True)

    output = capsys.readouterr().out
    assert "[DEBUG] Skip (wrong-month)" in output


def test_filter_valid_threads_empty_list():
    """filter_valid_threads should handle empty input gracefully."""
    result = filter_valid_threads([], 2025, 5)
    assert not result  # Should return empty list when safe_call returns None


# --------------------------------------------------------------------------- #
# Fetch comments tests                                                         #
# --------------------------------------------------------------------------- #
def test_fetch_top_level_comments_basic():
    """fetch_top_level_comments should return only root comments."""
    submission = MockSubmission("test", "Test Thread")

    with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
        # Mock safe_call to just call the function directly
        mock_safe_call.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)

        result = fetch_top_level_comments(submission)

    # Should call replace_more with limit=None
    submission.comments.replace_more.assert_called_once_with(limit=None)

    # Should return only root comments (c1 and c3 from our mock)
    assert len(result) == 2
    assert all(comment.is_root for comment in result)
    assert result[0].id == "c1"
    assert result[1].id == "c3"


def test_fetch_top_level_comments_replace_more_error():
    """fetch_top_level_comments should handle replace_more errors via safe_call."""
    submission = MockSubmission("test", "Test Thread")
    submission.comments.replace_more.side_effect = Exception("Reddit API Error")

    with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
        # Make safe_call return None for errors
        mock_safe_call.return_value = None

        # Mock comments.list to return empty list when safe_call returns None
        submission.comments.list.return_value = []

        result = fetch_top_level_comments(submission)
        assert result == []


def test_fetch_top_level_comments_no_comments():
    """fetch_top_level_comments should handle submissions with no comments."""
    submission = MockSubmission("test", "Test Thread")
    submission.comments.list.return_value = []

    with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
        mock_safe_call.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)

        result = fetch_top_level_comments(submission)

    assert result == []


def test_fetch_top_level_comments_missing_is_root_attribute():
    """fetch_top_level_comments should handle comments missing is_root attribute."""
    submission = MockSubmission("test", "Test Thread")

    # Create a simple object without is_root attribute
    class CommentWithoutIsRoot:
        def __init__(self):
            self.id = "no_attr"
            self.body = "test comment"
            # Deliberately not setting is_root

    comment_without_attr = CommentWithoutIsRoot()
    submission.comments.list.return_value = [comment_without_attr]

    with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
        mock_safe_call.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)

        result = fetch_top_level_comments(submission)

    # Should return empty list since getattr(comment, "is_root", False) returns False
    assert result == []


# --------------------------------------------------------------------------- #
# Integration tests                                                            #
# --------------------------------------------------------------------------- #
def test_search_and_fetch_integration():
    """Integration test combining search and comment fetching."""
    # Create submission with comments
    submission = MockSubmission("integration", "SOTD Thread May 01, 2025")

    mock_subreddit = MockSubreddit([submission])
    mock_reddit = MockReddit(mock_subreddit)

    with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
        # Search for threads
        threads = search_threads("wetshaving", 2025, 5)
        assert len(threads) == 1

        # Fetch comments from the thread
        with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
            mock_safe_call.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)

            comments = fetch_top_level_comments(threads[0])
            assert len(comments) == 2  # Only root comments
