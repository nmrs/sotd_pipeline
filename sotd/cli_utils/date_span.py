from datetime import datetime
from typing import Iterator


def parse_ym(s: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(s.strip(), "%Y-%m")
        return dt.year, dt.month
    except ValueError as exc:
        raise ValueError(f"Invalid YYYY-MM format: {s}") from exc


def iter_months(start: tuple[int, int], end: tuple[int, int]) -> Iterator[tuple[int, int]]:
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


def month_span(args) -> list[tuple[int, int]]:
    if hasattr(args, "delta_months") and args.delta_months:
        # Handle delta months (comma-separated list)
        months = []
        for month_str in args.delta_months.split(","):
            month_str = month_str.strip()
            if month_str:
                months.append(parse_ym(month_str))
        return months

    if args.month:
        return [parse_ym(args.month)]

    if args.year:
        y = int(args.year)
        return [(y, m) for m in range(1, 13)]

    if args.range:
        try:
            start_str, end_str = args.range.split(":")
            start = parse_ym(start_str)
            end = parse_ym(end_str)
        except ValueError as exc:
            raise ValueError(f"Invalid range format: {args.range}") from exc
        return list(iter_months(start, end))

    if args.start and args.end:
        start = parse_ym(args.start)
        end = parse_ym(args.end)
        return list(iter_months(start, end))

    raise ValueError(
        "Must provide --month, --year, --range, both --start and --end, or --delta-months."
    )
