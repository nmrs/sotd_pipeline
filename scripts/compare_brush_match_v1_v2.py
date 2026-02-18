#!/usr/bin/env python3
"""
Compare brush slots between v1 and v2 matched output (Phase 1.6 acceptance).

One-shot (run v1, save snapshot, run v2, compare — iterate until clean):
  python scripts/compare_brush_match_v1_v2.py --month 2026-02

Compare two existing files:
  python scripts/compare_brush_match_v1_v2.py --v1 data/matched/2026-02-v1.json --v2 data/matched/2026-02.json

Exit code 0 if identical, 1 if diffs found or error.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Allow running from repo root with PYTHONPATH=.
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brushmatch.phase16_parity import compare_brush_slots, load_matched_data


def run_match(month: str, brush_version: str, data_dir: Path) -> int:
    """Run run.py match for month with given brush-match-version. Returns exit code."""
    cmd = [
        sys.executable,
        str(repo_root / "run.py"),
        "match",
        "--month",
        month,
        "--force",
        "--brush-match-version",
        brush_version,
    ]
    if data_dir != repo_root / "data":
        cmd.extend(["--data-dir", str(data_dir)])
    return subprocess.run(cmd, cwd=repo_root).returncode


def main() -> int:
    p = argparse.ArgumentParser(
        description="Compare brush slots v1 vs v2. Use --month to run both and compare."
    )
    p.add_argument("--month", type=str, help="YYYY-MM: run v1, save snapshot, run v2, compare")
    p.add_argument("--data-dir", type=Path, default=None, help="Data dir (default: data)")
    p.add_argument("--v1", type=Path, help="Path to v1 matched JSON (omit if using --month)")
    p.add_argument("--v2", type=Path, help="Path to v2 matched JSON (omit if using --month)")
    args = p.parse_args()
    data_dir = Path(args.data_dir) if args.data_dir else repo_root / "data"
    matched_dir = data_dir / "matched"

    if args.month:
        month = args.month
        v1_path = matched_dir / f"{month}-v1-snapshot.json"
        v2_path = matched_dir / f"{month}.json"
        print(f"Run match v1 for {month}...", flush=True)
        if run_match(month, "v1", data_dir) != 0:
            print("Error: v1 match failed.", file=sys.stderr)
            return 1
        shutil.copy(v2_path, v1_path)
        print(f"Saved v1 snapshot to {v1_path}", flush=True)
        print(f"Run match v2 for {month}...", flush=True)
        if run_match(month, "v2", data_dir) != 0:
            print("Error: v2 match failed.", file=sys.stderr)
            return 1
    else:
        if not args.v1 or not args.v2:
            p.error("Either --month or both --v1 and --v2 are required")
        v1_path = args.v1
        v2_path = args.v2

    if not v1_path.exists():
        print(f"Error: {v1_path} not found", file=sys.stderr)
        return 1
    if not v2_path.exists():
        print(f"Error: {v2_path} not found", file=sys.stderr)
        return 1
    v1_data = load_matched_data(v1_path)
    v2_data = load_matched_data(v2_path)
    ok, diffs = compare_brush_slots(v1_data, v2_data)
    if ok:
        print("OK: brush slots identical.")
        return 0
    print(f"Diff: {len(diffs)} record(s) differ.", file=sys.stderr)
    for idx, b1, b2 in diffs[:20]:
        print(f"  [{idx}] v1={b1!r} vs v2={b2!r}", file=sys.stderr)
    if len(diffs) > 20:
        print(f"  ... and {len(diffs) - 20} more.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
