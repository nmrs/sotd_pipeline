"""Module for fetching data from Reddit."""

import time

import pytest
import requests
from prawcore.exceptions import TooManyRequests

from sotd.fetch.reddit import safe_call


class DummyRL(TooManyRequests):
    """A dummy exception class that mimics rate-limit errors."""

    def __init__(self, sleep_time: int):
        response = requests.Response()
        response.status_code = 429
        super().__init__(response)
        self.sleep_time = sleep_time


def test_safe_call_success(monkeypatch, caplog):
    """safe_call retries once after a TooManyRequests and returns the result."""
    calls = {"n": 0}

    def fn():
        if calls["n"] == 0:
            calls["n"] += 1
            raise DummyRL(1)
        return "ok"

    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    with caplog.at_level("WARNING"):
        result = safe_call(fn)

    assert result == "ok"
    assert slept == [1]  # sleep_time with exponential backoff
    log_output = caplog.text
    # With jitter, the exact message may vary, so check for key parts
    assert "Reddit rate-limit hit (hit #1 in 0.0s, attempt 1/3)" in log_output
    assert "waiting 0m 1s" in log_output


def test_safe_call_double_fail(monkeypatch):
    """safe_call does not retry more than once."""
    # Mock sleep to avoid actual sleeping during tests
    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    def fn():
        raise DummyRL(1)

    with pytest.raises(TooManyRequests):
        safe_call(fn)

    # Verify that sleep was called with the expected duration (with jitter)
    assert len(slept) == 2  # Two sleep calls
    assert 0.9 <= slept[0] <= 1.1  # First retry: ~1s with jitter (from headers)
    assert 0.9 <= slept[1] <= 1.1  # Second retry: ~1s with jitter (from headers)
