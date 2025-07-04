import pytest
from sotd.cli_utils import date_span


def test_parse_ym_valid():
    assert date_span.parse_ym("2023-09") == (2023, 9)
    assert date_span.parse_ym("2024-01") == (2024, 1)


def test_parse_ym_invalid():
    with pytest.raises(ValueError):
        date_span.parse_ym("invalid")
    with pytest.raises(ValueError):
        date_span.parse_ym("2023-13")  # Invalid month
    with pytest.raises(ValueError):
        date_span.parse_ym("2023-00")  # Invalid month


def test_iter_months():
    months = list(date_span.iter_months((2023, 11), (2024, 1)))
    assert months == [(2023, 11), (2023, 12), (2024, 1)]

    months = list(date_span.iter_months((2024, 1), (2024, 1)))
    assert months == [(2024, 1)]


def test_month_span_from_month():
    class Args:
        month = "2023-09"
        year = range = start = end = None

    assert date_span.month_span(Args()) == [(2023, 9)]


def test_month_span_from_year():
    class Args:
        year = "2023"
        month = range = start = end = None

    assert date_span.month_span(Args()) == [(2023, m) for m in range(1, 13)]


def test_month_span_from_range():
    class Args:
        range = "2023-11:2024-01"
        month = year = start = end = None

    assert date_span.month_span(Args()) == [(2023, 11), (2023, 12), (2024, 1)]


def test_month_span_from_start_end():
    class Args:
        start = "2024-01"
        end = "2024-03"
        month = year = range = None

    assert date_span.month_span(Args()) == [(2024, 1), (2024, 2), (2024, 3)]


def test_month_span_missing_args():
    class Args:
        month = year = range = start = end = None

    with pytest.raises(ValueError):
        date_span.month_span(Args())
