"""Extract Observations sections from archived SOTD reports.

Slices the hand-written ``## Observations`` block out of
``data/report_archive/YYYY-MM-{hardware,software}.md`` so consumers (the
observations-drafter agent, shell debugging, future style analysis) get the
voice/storyline context without loading 40-55 KB report files full of tables.

Archive reports are narrative context only — never a numeric source. This
tool changes nothing; it is a read-only extractor with deterministic output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path

ARCHIVE_FILE_RE = re.compile(r"^(\d{4}-\d{2})-(hardware|software)\.md$")
OBSERVATIONS_HEADING = "## Observations"


class ExtractError(Exception):
    """Raised for user-facing extractor failures."""


def default_data_dir() -> str:
    """Return the artifact root from the environment or the repo default."""
    return os.environ.get("SOTD_DATA_DIR", "data")


def build_parser() -> argparse.ArgumentParser:
    """Build the extract_observations argument parser."""
    parser = argparse.ArgumentParser(
        prog="extract_observations",
        description="Extract Observations sections from data/report_archive reports.",
    )
    parser.add_argument("--data-dir", default=default_data_dir(), help="Artifact root directory")
    parser.add_argument(
        "--type",
        choices=["hardware", "software", "both"],
        default="both",
        help="Report type to include (default: both)",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--last", type=int, help="Most recent N months per type")
    selection.add_argument(
        "--months",
        help="Month list or inclusive range: '2026-01,2026-03' or '2026-01:2026-06'",
    )
    parser.add_argument(
        "--end",
        help="Bound selection at this month (YYYY-MM, inclusive; applies to --last and the default full history)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown blocks")
    return parser


def _archive_paths(data_dir: Path, report_type: str) -> list[tuple[str, Path]]:
    """Return sorted (month, path) pairs for the requested type."""
    archive_dir = data_dir / "report_archive"
    wanted_types = ["hardware", "software"] if report_type == "both" else [report_type]
    pairs: list[tuple[str, Path]] = []
    for path in archive_dir.iterdir():
        match = ARCHIVE_FILE_RE.match(path.name)
        if match and match.group(2) in wanted_types:
            pairs.append((match.group(1), path))
    return sorted(pairs)


def _select_months(
    pairs: list[tuple[str, Path]], args: argparse.Namespace
) -> list[tuple[str, Path]]:
    """Apply --last or --months selection, bounded by --end, to the archive files."""
    if args.end is not None:
        if args.months:
            raise ExtractError("--end cannot be combined with --months")
        if not re.match(r"^\d{4}-\d{2}$", args.end):
            raise ExtractError(f"invalid month {args.end!r}; expected YYYY-MM")
        pairs = [(month, path) for month, path in pairs if month <= args.end]
    if args.last is not None:
        if args.last < 1:
            raise ExtractError("--last must be a positive integer")
        available = sorted({month for month, _ in pairs})
        keep = set(available[-args.last :])
        return [(month, path) for month, path in pairs if month in keep]
    if args.months:
        keep = _parse_months(args.months)
        selected = [(month, path) for month, path in pairs if month in keep]
        missing = sorted(keep - {month for month, _ in selected})
        if missing:
            raise ExtractError(f"no archive files for months: {', '.join(missing)}")
        return selected
    return pairs


def _parse_months(spec: str) -> set[str]:
    """Parse a comma-separated month list or an inclusive a:b range."""
    if ":" in spec:
        start, end = spec.split(":", 1)
        if not (len(start) == 7 and len(end) == 7):
            raise ExtractError("--months range must use YYYY-MM:YYYY-MM")
        return {m for m in _all_months() if start <= m <= end}
    months = [m.strip() for m in spec.split(",") if m.strip()]
    for month in months:
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ExtractError(f"invalid month {month!r}; expected YYYY-MM")
    return set(months)


def _all_months() -> list[str]:
    """Return every YYYY-MM string (used to expand inclusive ranges)."""
    months: list[str] = []
    for year in range(2016, 2100):
        for month in range(1, 13):
            months.append(f"{year:04d}-{month:02d}")
    return months


def extract_section(path: Path) -> list[str] | None:
    """Return the Observations bullet lines of one file, or None if absent."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == OBSERVATIONS_HEADING:
            start = index + 1
            break
    if start is None:
        return None
    collected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        collected.append(line)
    while collected and not collected[0].strip():
        collected.pop(0)
    while collected and not collected[-1].strip():
        collected.pop()
    return collected


def extract_all(args: argparse.Namespace) -> list[dict[str, object]]:
    """Return observation blocks for the selected archive files."""
    data_dir = Path(args.data_dir)
    if not (data_dir / "report_archive").is_dir():
        raise ExtractError(f"archive directory not found: {data_dir / 'report_archive'}")
    pairs = _select_months(_archive_paths(data_dir, args.type), args)
    blocks: list[dict[str, object]] = []
    for month, path in pairs:
        observations = extract_section(path)
        if observations is None:
            print(f"warning: no Observations section in {path.name}", file=sys.stderr)
            continue
        blocks.append(
            {
                "month": month,
                "type": path.name.rsplit("-", 1)[1].removesuffix(".md"),
                "observations": observations,
            }
        )
    return blocks


def _render(blocks: list[dict[str, object]]) -> str:
    """Render observation blocks as readable markdown sections."""
    parts: list[str] = []
    for block in blocks:
        parts.append(f"== {block['month']} — {block['type']} ==")
        observations = block["observations"]
        assert isinstance(observations, list)
        parts.extend(observations)
        parts.append("")
    return "\n".join(parts).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point returning a process exit code."""
    args = build_parser().parse_args(argv)
    try:
        blocks = extract_all(args)
    except ExtractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not blocks:
        print("no Observations sections found", file=sys.stderr)
        return 0
    print(json.dumps(blocks, indent=2) if args.json else _render(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
