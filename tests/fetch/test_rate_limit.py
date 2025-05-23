import time
from prawcore.exceptions import TooManyRequests  # use correct exception class

"""Module for fetching data from Reddit."""

import pytest

from sotd.fetch.reddit import safe_call, RateLimitExceeded  # type: ignore[attr-defined]


class DummyRL(RateLimitExceeded):
    """A dummy exception class that mimics rate-limit errors."""

    def __init__(self, sleep_time: int):
        # Initialize dummy without invoking base class __init__
        self.sleep_time = sleep_time


def test_safe_call_success(monkeypatch, capsys):
    """safe_call retries once after a RateLimitExceeded and returns the result."""
    calls = {"n": 0}

    def fn():
        if calls["n"] == 0:
            calls["n"] += 1
            raise DummyRL(1)
        return "ok"

    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    result = safe_call(fn)

    assert result == "ok"
    assert slept == [2]  # sleep_time + 1
    out = capsys.readouterr().out
    assert "[WARN] Reddit rate-limit hit; sleeping 0m 1s…" in out


def test_safe_call_double_fail():
    """safe_call does not retry more than once."""

    def fn():
        raise DummyRL(1)

    with pytest.raises(RateLimitExceeded):
        safe_call(fn)
