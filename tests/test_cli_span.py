from datetime import date
from types import SimpleNamespace

import pytest

from sotd.fetch import run


def patch_today(monkeypatch, y, m):
    class DummyDate(date):  # override today()
        @classmethod
        def today(cls):  # type: ignore[override]
            return cls(y, m, 15)

    monkeypatch.setattr(run, "_current_ym", lambda: (y, m))


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
    # handle flags without value
    if "--start" in argv and len(argv) == 3:
        ns.start = argv[1]
    if "--end" in argv and len(argv) == 3:
        ns.end = argv[1]
    months = run._month_span(ns)
    assert months == expect


@pytest.mark.parametrize(
    "argv",
    [
        ["--month", "2025-04", "--range", "2025-03:2025-05"],
        ["--year", "2024", "--month", "2024-01"],
    ],
)
def test_conflict(monkeypatch, argv):
    patch_today(monkeypatch, 2025, 5)
    with pytest.raises(run.argparse.ArgumentTypeError):
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
        run._month_span(ns)
