import pytest

from sotd.cli_utils import date_span
from sotd.fetch import run


def patch_today(monkeypatch, y, m):
    monkeypatch.setattr(date_span, "_current_ym", lambda: (y, m))


@pytest.mark.parametrize(
    ("argv", "expect"),
    [
        ([], [(2025, 5)]),  # current month default
        (["--month", "2025-04"], [(2025, 4)]),
        (["--year", "2024"], [(2024, m) for m in range(1, 13)]),
        (["--start", "2023-06"], [(2023, 6)]),
        (["--end", "2023-12"], [(2023, 12)]),
        (["--start", "2023-06", "--end", "2023-08"], [(2023, 6), (2023, 7), (2023, 8)]),
        (["--range", "2023-06:2023-08"], [(2023, 6), (2023, 7), (2023, 8)]),
    ],
)
def test_month_span_success(monkeypatch, argv, expect):
    patch_today(monkeypatch, 2025, 5)
    ns = run.argparse.Namespace(
        month=None,
        year=None,
        range=None,
        start=None,
        end=None,
        out_dir="data",
        debug=False,
        force=False,
    )
    # inject args
    for i, v in zip(argv[::2], argv[1::2]):
        setattr(ns, i.lstrip("-").replace("-", "_"), v)
    if not argv:
        ns.month = "2025-05"
    elif "--start" in argv and "--end" not in argv:
        ns.end = argv[1]
    elif "--end" in argv and "--start" not in argv:
        ns.start = argv[1]
    months = run.month_span(ns)
    assert months == expect


@pytest.mark.parametrize(
    "argv, expect",
    [
        (["--month", "2025-04", "--range", "2025-03:2025-05"], [(2025, 4)]),
        (["--year", "2024", "--month", "2024-01"], [(2024, 1)]),
    ],
)
def test_conflict(monkeypatch, argv, expect):
    patch_today(monkeypatch, 2025, 5)
    ns = run.argparse.Namespace(
        month=None,
        year=None,
        range=None,
        start=None,
        end=None,
        out_dir="data",
        debug=False,
        force=False,
    )
    for i, v in zip(argv[::2], argv[1::2]):
        setattr(ns, i.lstrip("-").replace("-", "_"), v)
    months = run.month_span(ns)
    assert months == expect
