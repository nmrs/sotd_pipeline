#!/usr/bin/env python3
"""One-shot: re-run extract→match→enrich for months with extract overrides.

After the match phase starts preserving the ``overridden`` audit flag, run this
once so matched/enriched files for override months pick up the flag.

Usage:
  python scripts/rerun_extract_override_months.py
  python scripts/rerun_extract_override_months.py --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OVERRIDE_FILE = PROJECT_ROOT / "data" / "extract_overrides.yaml"


def months_with_overrides(override_file: Path) -> list[tuple[str, int, int]]:
    """Return sorted (month, comment_count, field_count) from the override YAML."""
    if not override_file.exists():
        return []

    content = yaml.safe_load(override_file.read_text(encoding="utf-8"))
    if not content or not isinstance(content, dict):
        return []

    rows: list[tuple[str, int, int]] = []
    for month in sorted(content.keys()):
        month_data = content[month]
        if not isinstance(month_data, dict):
            continue
        comment_count = len(month_data)
        field_count = sum(len(fields) for fields in month_data.values() if isinstance(fields, dict))
        rows.append((str(month), comment_count, field_count))
    return rows


def run_pipeline_for_month(month: str, dry_run: bool = False) -> int:
    """Run extract:enrich with --force for a single month. Returns process exit code."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "run.py"),
        "extract:enrich",
        "--month",
        month,
        "--force",
    ]
    print(f"\n>>> {' '.join(cmd)}")
    if dry_run:
        return 0
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-run extract→match→enrich for months in extract_overrides.yaml"
    )
    parser.add_argument(
        "--override-file",
        type=Path,
        default=DEFAULT_OVERRIDE_FILE,
        help="Path to extract_overrides.yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print months and commands without running the pipeline",
    )
    args = parser.parse_args(argv)

    rows = months_with_overrides(args.override_file)
    if not rows:
        print(f"No overrides found in {args.override_file}")
        return 0

    print(f"Months with extract overrides ({len(rows)}):")
    for month, comment_count, field_count in rows:
        print(f"  {month}: {comment_count} comment(s), {field_count} field(s)")

    failed: list[str] = []
    for month, _, _ in rows:
        code = run_pipeline_for_month(month, dry_run=args.dry_run)
        if code != 0:
            print(f"FAILED: {month} (exit {code})")
            failed.append(month)

    if failed:
        print(f"\nCompleted with failures: {', '.join(failed)}")
        return 1

    print("\nAll months processed successfully." + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
