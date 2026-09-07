"""Point-query CLI for aggregated SOTD data.

Answers the deterministic questions the observations-drafter agent (and shell
debugging) need without loading whole 500-700 KB JSON files: month meta,
top-N rows of a category, and rank history for a single item across months
or years. All numbers come from ``data/aggregated/`` — the machine truth.

Monthly files (``data/aggregated/YYYY-MM.json``) wrap categories in a
``data`` key with a ``meta`` block; annual files
(``data/aggregated/annual/YYYY.json``) put categories at the top level with
``metadata``. Both shapes are normalized on load.

Exit codes: 0 success, 1 on query errors (unknown category, ambiguous name,
missing month).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

HUMAN_DEFAULT_TOP = 10


class QueryError(Exception):
    """Raised for deterministic, user-facing query failures."""


def default_data_dir() -> str:
    """Return the artifact root from the environment or the repo default."""
    return os.environ.get("SOTD_DATA_DIR", "data")


def build_parser() -> argparse.ArgumentParser:
    """Build the aggregate_query argument parser."""
    parser = argparse.ArgumentParser(
        prog="aggregate_query",
        description="Query data/aggregated JSON files (meta, top-N, rank history).",
    )
    parser.add_argument("--data-dir", default=default_data_dir(), help="Artifact root directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of aligned text")
    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("meta", help="Print the meta/metadata block for a month or year")
    _add_period_args(meta)

    schema = sub.add_parser("schema", help="List categories with row counts and entry fields")
    _add_period_args(schema)

    top = sub.add_parser("top", help="Print the top N rows of a category")
    _add_period_args(top)
    top.add_argument("--category", required=True, help="Category key (e.g. razors, soaps)")
    top.add_argument(
        "--top", type=int, default=HUMAN_DEFAULT_TOP, help="Number of rows (default 10)"
    )
    top.add_argument(
        "--min-shaves",
        type=int,
        default=0,
        help="Exclude entries with fewer shaves (use to match report-table thresholds)",
    )

    history = sub.add_parser(
        "history", help="Rank history for one item (or a multi-item matrix) across months or years"
    )
    history.add_argument("--category", required=True, help="Category key (e.g. razors, soaps)")
    history.add_argument(
        "--name",
        required=True,
        action="append",
        help="Item name (case-insensitive exact match); repeat for a side-by-side matrix",
    )
    history.add_argument(
        "--contains", action="store_true", help="Match by case-insensitive substring"
    )
    history.add_argument("--last", type=int, help="Most recent N monthly files")
    history.add_argument("--start", help="Range start month (YYYY-MM)")
    history.add_argument("--end", help="Range end month (YYYY-MM, inclusive)")
    history.add_argument("--year", help="Single annual file (YYYY)")
    history.add_argument(
        "--min-shaves",
        type=int,
        default=0,
        help="Only count months where the item clears this threshold",
    )

    return parser


def _add_period_args(parser: argparse.ArgumentParser) -> None:
    """Add the --month / --year period selectors shared by meta and top."""
    period = parser.add_mutually_exclusive_group(required=True)
    period.add_argument("--month", help="Monthly file (YYYY-MM)")
    period.add_argument("--year", help="Annual file (YYYY)")


def _monthly_paths(data_dir: Path) -> list[Path]:
    """Return sorted monthly aggregated file paths."""
    return sorted((data_dir / "aggregated").glob("????-??.json"))


def _annual_path(data_dir: Path, year: str) -> Path:
    """Return the annual aggregated file path for a year."""
    return data_dir / "aggregated" / "annual" / f"{year}.json"


def _load(path: Path) -> dict[str, Any]:
    """Load a JSON document, raising QueryError if missing."""
    try:
        with path.open(encoding="utf-8") as handle:
            doc = json.load(handle)
    except FileNotFoundError as exc:
        raise QueryError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise QueryError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise QueryError(f"unexpected structure in {path}")
    return doc


def _category_container(doc: dict[str, Any]) -> dict[str, Any]:
    """Return the dict holding category keys for either file shape."""
    data = doc.get("data")
    return data if isinstance(data, dict) else doc


def _category_list(doc: dict[str, Any], category: str) -> list[dict[str, Any]]:
    """Return the ranked list for a category, or raise QueryError."""
    container = _category_container(doc)
    if category not in container:
        valid = sorted(k for k, v in container.items() if isinstance(v, list))
        raise QueryError(f"unknown category {category!r}; valid categories: {', '.join(valid)}")
    value = container[category]
    if not isinstance(value, list):
        raise QueryError(f"category {category!r} is not a ranked list")
    return [entry for entry in value if isinstance(entry, dict)]


def _resolve_period(args: argparse.Namespace, data_dir: Path) -> tuple[Path, bool]:
    """Return (path, is_annual) for the selected period."""
    if args.month:
        return data_dir / "aggregated" / f"{args.month}.json", False
    return _annual_path(data_dir, args.year), True


def _select_history_files(
    args: argparse.Namespace, data_dir: Path
) -> tuple[list[tuple[str, Path]], bool, list[str]]:
    """Return (labelled paths, is_annual, missing labels) for a history query.

    Range mode enumerates calendar months between --start and --end so gaps
    surface as skipped labels instead of silently compressing the history.
    """
    if args.year:
        if args.last is not None or args.start or args.end:
            raise QueryError("--year cannot be combined with --last/--start/--end")
        return [(args.year, _annual_path(data_dir, args.year))], True, []
    if args.last is None and not (args.start or args.end):
        raise QueryError("history needs --last N (optionally with --start/--end), or --year")
    if args.last is not None and args.last < 1:
        raise QueryError("--last must be a positive integer")
    for value in (args.start, args.end):
        if value is not None and not re.match(r"^\d{4}-\d{2}$", value):
            raise QueryError(f"invalid month {value!r}; expected YYYY-MM")
    if args.start and args.end and args.start > args.end:
        raise QueryError("--start must not be after --end")
    if args.start and args.end:
        labels = _month_range_labels(args.start, args.end)
    else:
        existing = _monthly_paths(data_dir)
        if args.end:
            existing = [p for p in existing if p.stem <= args.end]
        if args.start:
            existing = [p for p in existing if p.stem >= args.start]
        if args.last is not None:
            existing = existing[-args.last :]
        labels = [p.stem for p in existing]
    month_dir = data_dir / "aggregated"
    paths = [(label, month_dir / f"{label}.json") for label in labels]
    missing = [label for label, path in paths if not path.exists()]
    return paths, False, missing


def _month_range_labels(start: str, end: str) -> list[str]:
    """Return every YYYY-MM label between start and end inclusive."""
    start_year, start_month = int(start[:4]), int(start[5:7])
    end_year, end_month = int(end[:4]), int(end[5:7])
    labels: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        labels.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return labels


def _find_entry(entries: list[dict[str, Any]], name: str, contains: bool) -> dict[str, Any] | None:
    """Match one entry by name; raise QueryError on ambiguous substring matches."""
    if contains:
        matches = [e for e in entries if name.casefold() in str(e.get("name", "")).casefold()]
        if len(matches) > 1:
            names = ", ".join(sorted(str(e.get("name", "")) for e in matches))
            raise QueryError(f"ambiguous name {name!r} with --contains; candidates: {names}")
        return matches[0] if matches else None
    target = name.casefold()
    for entry in entries:
        if str(entry.get("name", "")).casefold() == target:
            return entry
    return None


def query_schema(args: argparse.Namespace) -> dict[str, Any]:
    """Return per-category row counts and entry-field unions for the period."""
    data_dir = Path(args.data_dir)
    path, _ = _resolve_period(args, data_dir)
    doc = _load(path)
    container = _category_container(doc)
    categories: dict[str, Any] = {}
    for key in sorted(container):
        value = container[key]
        if isinstance(value, list):
            dicts = [entry for entry in value if isinstance(entry, dict)]
            fields = sorted({field for entry in dicts for field in entry})
            categories[key] = {"type": "list", "rows": len(value), "fields": fields}
        elif isinstance(value, dict):
            categories[key] = {"type": "dict", "keys": sorted(value)}
        else:
            categories[key] = {"type": type(value).__name__}
    return {"file": str(path), "period": args.month or args.year, "categories": categories}


def query_meta(args: argparse.Namespace) -> dict[str, Any]:
    """Return the meta/metadata block for the selected period."""
    data_dir = Path(args.data_dir)
    path, is_annual = _resolve_period(args, data_dir)
    doc = _load(path)
    key = "metadata" if is_annual else "meta"
    block = doc.get(key)
    if not isinstance(block, dict):
        raise QueryError(f"{key} block missing in {path}")
    return {k: block[k] for k in sorted(block)}


def query_top(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Return the top rows of a category for the selected period."""
    data_dir = Path(args.data_dir)
    path, _ = _resolve_period(args, data_dir)
    doc = _load(path)
    entries = _category_list(doc, args.category)
    if args.min_shaves > 0:
        entries = [e for e in entries if _entry_int(e, "shaves") >= args.min_shaves]
    return entries[: max(args.top, 0)]


def _entry_int(entry: dict[str, Any], key: str) -> int:
    """Return an entry's integer field, tolerating missing or non-int values."""
    value = entry.get(key, 0)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def query_history(args: argparse.Namespace) -> dict[str, Any]:
    """Return per-month (or annual) rank rows for one item, or a multi-item matrix."""
    data_dir = Path(args.data_dir)
    labelled, _is_annual, missing = _select_history_files(args, data_dir)
    if not labelled:
        raise QueryError("no aggregated files match the selected period")
    names: list[str] = args.name
    rows: list[dict[str, Any]] = []
    skipped: list[str] = list(missing)
    for label, path in labelled:
        if not path.exists():
            continue
        doc = _load(path)
        entries = _category_list(doc, args.category)
        row: dict[str, Any] = {"period": label}
        for name in names:
            entry = _find_entry(entries, name, args.contains)
            info = None
            if entry is not None and (
                args.min_shaves <= 0 or _entry_int(entry, "shaves") >= args.min_shaves
            ):
                info = {
                    "rank": entry.get("rank"),
                    "shaves": entry.get("shaves"),
                    "unique_users": entry.get("unique_users"),
                }
            if len(names) == 1:
                row.update(info or {"rank": None, "shaves": None, "unique_users": None})
            else:
                row[name] = info
        rows.append(row)
    if len(names) == 1:
        return {"category": args.category, "name": names[0], "rows": rows, "skipped": skipped}
    return {"category": args.category, "names": names, "rows": rows, "skipped": skipped}


def _render_meta(block: dict[str, Any]) -> str:
    """Render a meta block as aligned key: value lines."""
    width = max((len(k) for k in block), default=0)
    return "\n".join(f"{k:<{width}}  {json.dumps(v)}" for k, v in block.items())


def _render_schema(result: dict[str, Any]) -> str:
    """Render the schema result as aligned per-category lines."""
    lines = [f"{result['period']}  {result['file']}"]
    for key, info in result["categories"].items():
        if info["type"] == "list":
            fields = ", ".join(info["fields"]) or "(no dict rows)"
            lines.append(f"  {key:<24} list  rows={info['rows']}  fields: {fields}")
        elif info["type"] == "dict":
            keys = ", ".join(info["keys"])
            lines.append(f"  {key:<24} dict           keys: {keys}")
        else:
            lines.append(f"  {key:<24} {info['type']}")
    return "\n".join(lines)


def _render_rows(rows: list[dict[str, Any]], show_rank: bool = True) -> str:
    """Render period/rank/shaves/unique_users rows as an aligned table."""
    headers = ["period", "rank", "shaves", "unique_users"] if show_rank else ["period", "shaves"]
    table: list[list[str]] = []
    for row in rows:
        cells = [str(row["period"])]
        if show_rank:
            cells.append(str(row["rank"]) if row["rank"] is not None else "-")
        cells.append(f"{row['shaves']:,}" if row["shaves"] is not None else "-")
        cells.append(str(row["unique_users"]) if row["unique_users"] is not None else "-")
        table.append(cells)
    widths = [max(len(headers[i]), *(len(r[i]) for r in table)) for i in range(len(headers))]
    header_line = "  ".join(h.rjust(widths[i]) for i, h in enumerate(headers))
    body = "\n".join("  ".join(c.rjust(widths[i]) for i, c in enumerate(r)) for r in table)
    return f"{header_line}\n{body}" if table else "(no rows)"


def _render_top(entries: list[dict[str, Any]]) -> str:
    """Render top-N entries as aligned rank/name/shaves/users rows."""
    headers = ["rank", "name", "shaves", "unique_users"]
    table = [
        [
            str(e.get("rank", "")),
            str(e.get("name", "")),
            f"{_entry_int(e, 'shaves'):,}",
            str(e.get("unique_users", "")),
        ]
        for e in entries
    ]
    widths = [max(len(headers[i]), *(len(r[i]) for r in table)) for i in range(len(headers))]
    header_line = "  ".join(h.rjust(widths[i]) for i, h in enumerate(headers))
    body = "\n".join("  ".join(c.rjust(widths[i]) for i, c in enumerate(r)) for r in table)
    return f"{header_line}\n{body}" if table else "(no rows)"


def _render_matrix(result: dict[str, Any]) -> str:
    """Render a multi-item history as a period x item matrix of rank shaves/users cells."""
    names = result["names"]
    headers = ["period"] + names
    table: list[list[str]] = []
    for row in result["rows"]:
        cells = [str(row["period"])]
        for name in names:
            entry = row.get(name)
            if entry is None:
                cells.append("-")
            else:
                shaves = entry.get("shaves")
                cell = f"#{entry.get('rank')}"
                if shaves is not None:
                    cell += f" {shaves:,}/{entry.get('unique_users')}"
                cells.append(cell)
        table.append(cells)
    widths = [max(len(headers[i]), *(len(r[i]) for r in table)) for i in range(len(headers))]
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    body = "\n".join("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)) for r in table)
    return f"{header_line}\n{body}" if table else "(no rows)"


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point returning a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "meta":
            block = query_meta(args)
            output = json.dumps(block, indent=2) if args.json else _render_meta(block)
        elif args.command == "schema":
            result = query_schema(args)
            output = json.dumps(result, indent=2) if args.json else _render_schema(result)
        elif args.command == "top":
            entries = query_top(args)
            output = json.dumps(entries, indent=2) if args.json else _render_top(entries)
        else:
            result = query_history(args)
            if args.json:
                output = json.dumps(result, indent=2)
            else:
                output = (
                    _render_matrix(result) if "names" in result else _render_rows(result["rows"])
                )
            if result["skipped"]:
                output += f"\n(skipped missing files: {', '.join(result['skipped'])})"
    except QueryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
