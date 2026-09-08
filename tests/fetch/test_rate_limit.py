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
    assert slept == [1]  # header wait (1s) meets the 1s exponential floor
    log_output = caplog.text
    assert "Reddit 429 (attempt 1/4)" in log_output
    assert "waiting 0m 1s" in log_output


def test_safe_call_double_fail(monkeypatch):
    """safe_call gives up after the retry budget: initial + three retries."""
    # Mock sleep to avoid actual sleeping during tests
    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    def fn():
        raise DummyRL(1)

    with pytest.raises(TooManyRequests):
        safe_call(fn)

    # sleep_time=1 is below the exponential floor, so delays are 1, 2, 4
    assert slept == [1, 2, 4]
