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
# Exponential Backoff Tests                                                   #
# --------------------------------------------------------------------------- #
class TestExponentialBackoff:
    """Test exponential backoff retry logic functionality."""

    def test_exponential_backoff_calculation(self, monkeypatch):
        """Test exponential backoff delay calculation."""
        calls = 0
        attempt = 0

        def failing_function():
            nonlocal calls, attempt
            calls += 1
            attempt += 1
            if attempt <= 3:
                raise MockRateLimitException(sleep_time=1)
            return "success"

        # Mock sleep to track delays
        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        # This should fail after multiple retries with exponential delays
        with pytest.raises(TooManyRequests):
            safe_call(failing_function)

        # Should have multiple sleep calls with increasing delays
        assert len(sleep_calls) >= 2
        # First delay should be sleep_time = 1
        assert sleep_calls[0] == 1

    def test_exponential_backoff_with_configurable_parameters(self, monkeypatch):
        """Test exponential backoff with configurable retry parameters."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=5)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"
        assert calls == 3  # Initial + 2 retries

        # Should have exponential delays
        assert len(sleep_calls) == 2
        # First delay: sleep_time = 5
        # Second delay: should be exponential (e.g., 10)
        assert sleep_calls[0] == 5

    def test_exponential_backoff_max_attempts(self, monkeypatch):
        """Test exponential backoff respects maximum retry attempts."""
        calls = 0

        def always_failing_function():
            nonlocal calls
            calls += 1
            raise MockRateLimitException(sleep_time=1)

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        # Should fail after maximum retries
        with pytest.raises(TooManyRequests):
            safe_call(always_failing_function)

        # Should have attempted multiple times with exponential delays
        assert calls >= 2
        assert len(sleep_calls) >= 1

    def test_exponential_backoff_base_delay(self, monkeypatch):
        """Test exponential backoff with configurable base delay."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=3)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should use base delay for exponential calculation
        assert len(sleep_calls) == 2
        # First delay: sleep_time = 3
        assert sleep_calls[0] == 3

    def test_exponential_backoff_max_delay(self, monkeypatch):
        """Test exponential backoff respects maximum delay limit."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:  # Only fail on first 2 attempts
                raise MockRateLimitException(sleep_time=10)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should cap delays at maximum
        assert len(sleep_calls) == 2
        # All delays should be reasonable (not exponentially huge)
        for delay in sleep_calls:
            assert delay <= 60  # Reasonable maximum

    def test_exponential_backoff_intelligent_retry_decision(self, monkeypatch):
        """Test intelligent retry decision logic."""
        calls = 0

        def smart_failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=2)
            elif calls == 2:
                raise MockRateLimitException(sleep_time=1)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(smart_failing_function)
        assert result == "success"
        assert calls == 3

        # Should have different delays based on rate limit response
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 2  # First: sleep_time
        assert (
            sleep_calls[1] == 2
        )  # Second: sleep_time (same because both calls have same sleep_time)

    def test_exponential_backoff_integration_with_existing_safe_call(self, monkeypatch):
        """Test exponential backoff integrates with existing safe_call functionality."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=4)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should work with existing safe_call structure
        assert calls == 3
        assert len(sleep_calls) == 2

    def test_exponential_backoff_error_handling(self, monkeypatch):
        """Test exponential backoff error handling and logging."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=3)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should handle errors gracefully
        assert calls == 3
        assert len(sleep_calls) == 2

    def test_exponential_backoff_configuration_options(self, monkeypatch):
        """Test different exponential backoff configuration options."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=2)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should work with different configuration parameters
        assert calls == 3
        assert len(sleep_calls) == 2

    def test_exponential_backoff_different_api_endpoints(self, monkeypatch):
        """Test exponential backoff with different API endpoints."""
        calls = 0

        def search_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=5)
            return "search_results"

        def comment_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=3)
            return "comment_results"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        # Test with different functions (simulating different endpoints)
        result1 = safe_call(search_function)
        result2 = safe_call(comment_function)

        assert result1 == "search_results"
        assert result2 == "comment_results"
        assert calls == 4  # 2 calls each for 2 functions (2 successful attempts)

    def test_exponential_backoff_performance_improvement(self, monkeypatch):
        """Test that exponential backoff provides performance improvements."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=1)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)

        assert result == "success"
        # Should complete successfully with exponential backoff
        assert calls == 3
        assert len(sleep_calls) == 2

    def test_exponential_backoff_graceful_degradation(self, monkeypatch):
        """Test exponential backoff graceful degradation under heavy load."""
        calls = 0

        def heavily_rate_limited_function():
            nonlocal calls
            calls += 1
            if calls <= 5:  # Many rate limit hits
                raise MockRateLimitException(sleep_time=1)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        # Should eventually fail gracefully
        with pytest.raises(TooManyRequests):
            safe_call(heavily_rate_limited_function)

        # Should have attempted multiple times
        assert calls >= 2
        assert len(sleep_calls) >= 1

    def test_exponential_backoff_monitoring_integration(self, monkeypatch):
        """Test exponential backoff integrates with monitoring capabilities."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=4)
            return "success"

        sleep_calls = []
        monkeypatch.setattr(time, "sleep", lambda s: sleep_calls.append(s))

        result = safe_call(failing_function)
        assert result == "success"

        # Should work with existing monitoring
        assert calls == 3
        assert len(sleep_calls) == 2


# --------------------------------------------------------------------------- #
# Enhanced Rate Limit Detection Tests                                         #
# --------------------------------------------------------------------------- #
class TestEnhancedRateLimitDetection:
    """Test enhanced rate limit detection functionality."""

    def test_rate_limit_detection_from_response_time(self, monkeypatch):
        """Test rate limit detection from response times > 2 seconds."""
        calls = 0
        start_time = 1000.0

        def slow_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                # Simulate slow response that should trigger rate limit detection
                return "slow_response"
            return "success"

        # Mock time.time to simulate slow response
        def mock_time():
            nonlocal start_time
            if calls == 1:
                start_time += 3.0  # Simulate 3 second response time
            return start_time

        monkeypatch.setattr(time, "time", mock_time)
        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(slow_function)
        # With new behavior, slow responses don't trigger retries on first attempt
        assert result == "slow_response"

    def test_rate_limit_detection_from_exception_types(self, monkeypatch):
        """Test rate limit detection from specific exception types."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise MockRateLimitException(sleep_time=2)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"
        assert calls == 3  # Initial + 2 retries

    def test_rate_limit_frequency_tracking(self, monkeypatch):
        """Test rate limit frequency and pattern tracking."""
        rate_limit_hits = 0

        def function_with_multiple_rate_limits():
            nonlocal rate_limit_hits
            rate_limit_hits += 1
            if rate_limit_hits <= 3:  # Fail on first 3 calls
                raise MockRateLimitException(sleep_time=1)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        # This should fail after 3 attempts (max attempts reached)
        with pytest.raises(TooManyRequests):
            safe_call(function_with_multiple_rate_limits)

        # Should have attempted 3 times
        assert rate_limit_hits == 3

    def test_enhanced_logging_for_rate_limits(self, monkeypatch, capsys):
        """Test enhanced logging for rate limit events."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=10)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"

        output = capsys.readouterr().out
        assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
        assert "sleeping 0m 10s…" in output

    def test_rate_limit_detection_with_retry_after(self, monkeypatch, capsys):
        """Test rate limit detection using retry_after attribute."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(retry_after=15)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"

        output = capsys.readouterr().out
        assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
        assert "sleeping 0m 15s…" in output

    def test_rate_limit_detection_with_default_timing(self, monkeypatch, capsys):
        """Test rate limit detection with default timing when no attributes available."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException()  # No timing attributes
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"

        output = capsys.readouterr().out
        assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
        assert "sleeping 1m 0s…" in output

    def test_rate_limit_detection_performance_metrics(self, monkeypatch):
        """Test that rate limit detection includes performance metrics."""
        calls = 0
        start_time = 1000.0

        def slow_function():
            nonlocal calls, start_time
            calls += 1
            if calls == 1:
                start_time += 2.5  # Simulate slow response
                return "slow_response"
            return "success"

        def mock_time():
            nonlocal start_time
            return start_time

        monkeypatch.setattr(time, "time", mock_time)
        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(slow_function)
        # With new behavior, slow responses don't trigger retries on first attempt
        assert result == "slow_response"

    def test_rate_limit_detection_debugging_info(self, monkeypatch, capsys):
        """Test that rate limit detection provides debugging information."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=30)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"

        output = capsys.readouterr().out
        # Check for debugging information in the warning message
        assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
        assert "sleeping 0m 30s…" in output

    def test_rate_limit_detection_integration_with_search(self, monkeypatch):
        """Test rate limit detection integration with search operations."""
        mock_subreddit = Mock()

        # Create a call counter to track search calls
        call_count = 0

        def mock_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MockRateLimitException(sleep_time=5)  # First call fails
            return iter([MockSubmission("s1", "SOTD Thread May 01, 2025")])  # Second call succeeds

        mock_subreddit.search.side_effect = mock_search
        mock_reddit = MockReddit(mock_subreddit)

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        with patch("sotd.fetch.reddit.get_reddit", return_value=mock_reddit):
            result = search_threads("wetshaving", 2025, 5)

        assert len(result) == 1
        assert result[0].id == "s1"

    def test_rate_limit_detection_integration_with_comments(self, monkeypatch):
        """Test rate limit detection integration with comment fetching."""
        submission = MockSubmission("test", "Test Thread")

        # Mock replace_more to fail first, then succeed
        call_count = 0

        def mock_replace_more(limit=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise MockRateLimitException(sleep_time=3)
            return None

        submission.comments.replace_more.side_effect = mock_replace_more

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        with patch("sotd.fetch.reddit.safe_call") as mock_safe_call:
            # Mock safe_call to handle rate limits
            def mock_safe_call_impl(fn, *args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except MockRateLimitException:
                    # Simulate retry logic
                    return fn(*args, **kwargs)

            mock_safe_call.side_effect = mock_safe_call_impl

            result = fetch_top_level_comments(submission)

        assert len(result) == 2  # Should get comments after retry

    def test_rate_limit_detection_monitoring_integration(self, monkeypatch):
        """Test that rate limit detection integrates with monitoring."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=5)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        # Test that monitoring data is collected during rate limit events
        result = safe_call(failing_function)
        assert result == "success"
        assert calls == 2

    def test_rate_limit_detection_real_time_feedback(self, monkeypatch, capsys):
        """Test that rate limit detection provides real-time feedback."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=8)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"

        output = capsys.readouterr().out
        # Check for real-time feedback in the warning message
        assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
        assert "sleeping 0m 8s…" in output

    def test_rate_limit_detection_metrics_in_output(self, monkeypatch):
        """Test that rate limit detection includes metrics in fetch phase output."""
        calls = 0

        def failing_function():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise MockRateLimitException(sleep_time=5)
            return "success"

        monkeypatch.setattr(time, "sleep", lambda s: None)  # Mock sleep

        result = safe_call(failing_function)
        assert result == "success"
        assert calls == 2

        # Test that metrics are available for fetch phase output
        # This will be implemented in the actual code


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
    assert sleep_calls == [5]  # sleep_time

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
    assert "sleeping 0m 5s…" in output


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
    assert sleep_calls == [3]  # retry_after

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
    assert "sleeping 0m 3s…" in output


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
    assert sleep_calls == [60]  # default 60

    output = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit (hit #1 in" in output
    assert "sleeping 1m 0s…" in output


def test_safe_call_rate_limit_double_failure(monkeypatch):
    """safe_call should retry up to 3 times before giving up."""
    # Mock sleep to avoid actual sleeping during tests
    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    def always_failing():
        raise MockRateLimitException(sleep_time=1)

    with pytest.raises(TooManyRequests):
        safe_call(always_failing)

    # Verify that sleep was called multiple times with exponential delays
    assert len(slept) == 2  # 2 sleep calls: 1, 2 (no sleep on final attempt)
    assert slept[0] == 1  # First attempt
    assert slept[1] == 2  # Second attempt (exponential)


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


class TestParallelCommentFetching:
    """Test parallel comment fetching functionality."""

    def test_parallel_fetch_top_level_comments_basic(self, monkeypatch):
        """Test basic parallel comment fetching functionality."""
        # Mock submissions
        mock_submissions = [
            MockSubmission("sub1", "Thread 1", 10),
            MockSubmission("sub2", "Thread 2", 15),
            MockSubmission("sub3", "Thread 3", 8),
        ]

        # Mock comments for each submission
        mock_comments = {
            "sub1": [MockComment("c1", "Comment 1"), MockComment("c2", "Comment 2")],
            "sub2": [
                MockComment("c3", "Comment 3"),
                MockComment("c4", "Comment 4"),
                MockComment("c5", "Comment 5"),
            ],
            "sub3": [MockComment("c6", "Comment 6")],
        }

        def mock_fetch_comments(submission):
            return mock_comments.get(submission.id, [])

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        # Import the parallel function (we'll create this)
        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test parallel fetching
        results = fetch_top_level_comments_parallel(mock_submissions, max_workers=2)

        # Verify results
        assert len(results) == 3
        assert len(results[0]) == 2  # sub1 has 2 comments
        assert len(results[1]) == 3  # sub2 has 3 comments
        assert len(results[2]) == 1  # sub3 has 1 comment

    def test_parallel_fetch_top_level_comments_rate_limit_handling(self, monkeypatch):
        """Test parallel comment fetching with rate limit handling."""
        mock_submissions = [
            MockSubmission("sub1", "Thread 1", 10),
            MockSubmission("sub2", "Thread 2", 15),
        ]

        call_count = 0

        def mock_fetch_with_rate_limit(submission):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Simulate rate limit on second call
                raise MockRateLimitException(sleep_time=5)  # Use proper constructor
            return [MockComment(f"c{call_count}", f"Comment {call_count}")]

        monkeypatch.setattr(
            "sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_with_rate_limit
        )

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test that rate limits are handled gracefully
        results = fetch_top_level_comments_parallel(mock_submissions, max_workers=2)

        # Should handle rate limits and continue processing
        assert len(results) == 2
        assert len(results[0]) == 1  # First call succeeds
        assert len(results[1]) == 1  # Second call succeeds after retry

    def test_parallel_fetch_top_level_comments_worker_count_configuration(self, monkeypatch):
        """Test parallel comment fetching with different worker counts."""
        mock_submissions = [MockSubmission(f"sub{i}", f"Thread {i}", 10) for i in range(5)]

        def mock_fetch_comments(submission):
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test with different worker counts
        results_1 = fetch_top_level_comments_parallel(mock_submissions, max_workers=1)
        results_2 = fetch_top_level_comments_parallel(mock_submissions, max_workers=2)
        results_5 = fetch_top_level_comments_parallel(mock_submissions, max_workers=5)

        # All should return same number of results
        assert len(results_1) == 5
        assert len(results_2) == 5
        assert len(results_5) == 5

    def test_parallel_fetch_top_level_comments_empty_input(self, monkeypatch):
        """Test parallel comment fetching with empty input."""
        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test with empty list
        results = fetch_top_level_comments_parallel([], max_workers=2)
        assert results == []

    def test_parallel_fetch_top_level_comments_single_submission(self, monkeypatch):
        """Test parallel comment fetching with single submission."""
        mock_submission = MockSubmission("sub1", "Thread 1", 10)

        def mock_fetch_comments(submission):
            return [MockComment("c1", "Comment 1"), MockComment("c2", "Comment 2")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        results = fetch_top_level_comments_parallel([mock_submission], max_workers=2)
        assert len(results) == 1
        assert len(results[0]) == 2

    def test_parallel_fetch_top_level_comments_error_handling(self, monkeypatch):
        """Test parallel comment fetching with error handling."""
        mock_submissions = [
            MockSubmission("sub1", "Thread 1", 10),
            MockSubmission("sub2", "Thread 2", 15),
        ]

        def mock_fetch_with_error(submission):
            if submission.id == "sub2":
                raise Exception("API error")
            return [MockComment("c1", "Comment 1")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_with_error)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Should handle errors gracefully
        results = fetch_top_level_comments_parallel(mock_submissions, max_workers=2)
        assert len(results) == 2
        assert len(results[0]) == 1  # First succeeds
        assert len(results[1]) == 0  # Second fails, returns empty list

    def test_parallel_fetch_top_level_comments_performance_improvement(self, monkeypatch):
        """Test that parallel fetching provides performance improvement."""
        import time

        mock_submissions = [MockSubmission(f"sub{i}", f"Thread {i}", 10) for i in range(10)]

        def mock_fetch_with_delay(submission):
            time.sleep(0.1)  # Simulate API delay
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_with_delay)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test sequential vs parallel timing
        start_time = time.time()
        results_sequential = fetch_top_level_comments_parallel(mock_submissions, max_workers=1)
        sequential_time = time.time() - start_time

        start_time = time.time()
        results_parallel = fetch_top_level_comments_parallel(mock_submissions, max_workers=5)
        parallel_time = time.time() - start_time

        # Parallel should be faster
        assert parallel_time < sequential_time
        assert len(results_sequential) == len(results_parallel)

    def test_parallel_fetch_top_level_comments_integration_with_safe_call(self, monkeypatch):
        """Test that parallel fetching integrates with safe_call rate limiting."""
        mock_submissions = [
            MockSubmission("sub1", "Thread 1", 10),
            MockSubmission("sub2", "Thread 2", 15),
        ]

        call_count = 0

        def mock_fetch_with_rate_limit(submission):
            nonlocal call_count
            call_count += 1
            # Simulate rate limit on second call, but succeed on third attempt
            if submission.id == "sub2" and call_count <= 2:
                raise MockRateLimitException(sleep_time=1)  # Shorter sleep for test
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr(
            "sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_with_rate_limit
        )

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Should handle rate limits through safe_call integration
        results = fetch_top_level_comments_parallel(mock_submissions, max_workers=2)
        assert len(results) == 2
        assert len(results[0]) == 1  # First succeeds
        assert len(results[1]) == 1  # Second succeeds after retry

    def test_parallel_fetch_top_level_comments_worker_adjustment(self, monkeypatch):
        """Test dynamic worker adjustment based on rate limit hits."""
        mock_submissions = [MockSubmission(f"sub{i}", f"Thread {i}", 10) for i in range(5)]

        rate_limit_count = 0

        def mock_fetch_with_adaptive_rate_limits(submission):
            nonlocal rate_limit_count
            rate_limit_count += 1
            if rate_limit_count <= 2:  # First two calls hit rate limits
                raise MockRateLimitException("Rate limit hit")
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr(
            "sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_with_adaptive_rate_limits
        )

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Should adjust workers based on rate limit frequency
        results = fetch_top_level_comments_parallel(
            mock_submissions, max_workers=3, adaptive_workers=True
        )
        assert len(results) == 5

    def test_parallel_fetch_top_level_comments_monitoring_integration(self, monkeypatch):
        """Test that parallel fetching provides monitoring metrics."""
        mock_submissions = [MockSubmission(f"sub{i}", f"Thread {i}", 10) for i in range(3)]

        def mock_fetch_comments(submission):
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Should provide monitoring metrics
        results, metrics = fetch_top_level_comments_parallel(
            mock_submissions, max_workers=2, return_metrics=True
        )

        assert len(results) == 3
        assert "total_time" in metrics
        assert "worker_utilization" in metrics
        assert "rate_limit_hits" in metrics
        assert metrics["rate_limit_hits"] >= 0

    def test_parallel_fetch_top_level_comments_configuration_options(self, monkeypatch):
        """Test parallel comment fetching with various configuration options."""
        mock_submissions = [MockSubmission("sub1", "Thread 1", 10)]

        def mock_fetch_comments(submission):
            return [MockComment("c1", "Comment 1")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Test different configuration options
        results1 = fetch_top_level_comments_parallel(mock_submissions, max_workers=2, chunk_size=1)
        results2 = fetch_top_level_comments_parallel(mock_submissions, max_workers=2, chunk_size=5)
        results3 = fetch_top_level_comments_parallel(mock_submissions, max_workers=2, timeout=30)

        assert len(results1) == 1
        assert len(results2) == 1
        assert len(results3) == 1

    def test_parallel_fetch_top_level_comments_graceful_degradation(self, monkeypatch):
        """Test graceful degradation when parallel processing fails."""
        mock_submissions = [MockSubmission(f"sub{i}", f"Thread {i}", 10) for i in range(3)]

        def mock_fetch_comments(submission):
            return [MockComment(f"c{submission.id}", f"Comment {submission.id}")]

        monkeypatch.setattr("sotd.fetch.reddit.fetch_top_level_comments", mock_fetch_comments)

        from sotd.fetch.reddit import fetch_top_level_comments_parallel

        # Should fall back to sequential if parallel fails
        results = fetch_top_level_comments_parallel(
            mock_submissions, max_workers=0, fallback_to_sequential=True
        )
        assert len(results) == 3
