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


def test_parse_thread_date_day_month_year_format():
    from datetime import date as _date

    # Should parse only if year is present
    assert parse_thread_date("SOTD (6 Oct 2021)", 2000) == _date(2021, 10, 6)
    assert parse_thread_date("SOTD 10 Sep 2022", 2000) == _date(2022, 9, 10)
    assert parse_thread_date("(31 Dec 1999)", 2000) == _date(1999, 12, 31)
    assert parse_thread_date("Event: 2 jan 2020", 1900) == _date(2020, 1, 2)
    # Should not match if year is missing
    assert parse_thread_date("SOTD 10 Sep", 2000) is None
    assert parse_thread_date("(12 Apr)", 2000) is None
