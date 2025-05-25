from datetime import datetime
from typing import Iterator


def _parse_ym(s: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(s.strip(), "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        raise ValueError(f"Invalid YYYY-MM format: {s}")


def _iter_months(start: tuple[int, int], end: tuple[int, int]) -> Iterator[tuple[int, int]]:
    sy, sm = start
    ey, em = end
    while (sy, sm) <= (ey, em):
        yield sy, sm
        sm += 1
        if sm > 12:
            sm = 1
            sy += 1


def _current_ym() -> tuple[int, int]:
    today = datetime.today()
    return today.year, today.month


def _month_span(args) -> list[tuple[int, int]]:
    if args.month:
        return [_parse_ym(args.month)]

    if args.year:
        y = int(args.year)
        return [(y, m) for m in range(1, 13)]

    if args.range:
        try:
            start_str, end_str = args.range.split(":")
            start = _parse_ym(start_str)
            end = _parse_ym(end_str)
        except ValueError:
            raise ValueError(f"Invalid range format: {args.range}")
        return list(_iter_months(start, end))

    if args.start and args.end:
        start = _parse_ym(args.start)
        end = _parse_ym(args.end)
        return list(_iter_months(start, end))

    raise ValueError("Must provide --month, --year, --range, or both --start and --end.")
