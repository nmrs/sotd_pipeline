"""Parametrised tests for parse_thread_date()."""

from __future__ import annotations

from datetime import date

import pytest

from sotd.utils import parse_thread_date


@pytest.mark.parametrize(
    ("title", "year_hint", "expected"),
    [
        (
            "Monday SOTD Thread - May 20, 2025",
            2025,
            date(2025, 5, 20),
        ),
        (
            "Sat SOTD - May 5",
            2025,
            date(2025, 5, 5),
        ),
        (
            "Sunday Lather Games SOTD Thread Jun 29 2024",
            2024,
            date(2024, 6, 29),
        ),
        (
            "SOTD Thread 5/12",
            2025,
            date(2025, 5, 12),
        ),
    ],
)
def test_parse_thread_date_success(title: str, year_hint: int, expected) -> None:
    assert parse_thread_date(title, year_hint) == expected


def test_parse_thread_date_failure() -> None:
    bad = "Weekly Recap – Favourite Blades"
    assert parse_thread_date(bad, 2025) is None


@pytest.mark.parametrize(
    "title",
    [
        "SOTD Report: April 2020",
        "SOTD Report: April 2019",
        "March 2018 SOTD Report",
    ],
)
def test_parse_thread_date_report_titles(title: str) -> None:
    """Monthly or yearly SOTD report posts should not parse as daily SOTD dates."""
    assert parse_thread_date(title, 2025) is None
