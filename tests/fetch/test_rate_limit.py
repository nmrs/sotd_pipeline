"""Module for fetching data from Reddit."""

import time
import pytest

from sotd.fetch.reddit import safe_call, RateLimitExceeded  # type: ignore[attr-defined]


class DummyRL(RateLimitExceeded):
    """A dummy exception class that mimics rate-limit errors."""

    def __init__(self, sleep_time: int):
        self.sleep_time = sleep_time
        self.headers = {"x-ratelimit-reset": str(sleep_time)}  # Required by RateLimitExceeded
        # Create a mock response object with required attributes
        mock_response = type(
            "Response",
            (),
            {
                "headers": self.headers,
                "text": "Rate limit exceeded",
                "status_code": 429,
            },
        )()
        super().__init__(response=mock_response)  # type: ignore[arg-type]


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


def test_safe_call_double_fail(monkeypatch):
    """safe_call does not retry more than once."""
    # Mock sleep to avoid actual sleeping during tests
    slept: list[int] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(int(s)))

    def fn():
        raise DummyRL(1)

    with pytest.raises(RateLimitExceeded):
        safe_call(fn)

    # Verify that sleep was called once with the expected duration
    assert slept == [2]  # sleep_time + 1
