import json
import re
from pathlib import Path
from collections import Counter, defaultdict
import argparse
from sotd.cli_utils.date_span import _month_span


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze matched razors using a regex pattern")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--month", type=str)
    group.add_argument("--year", type=int)
    group.add_argument("--range", type=str)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of matching razors to show (default: 20)",
    )
    parser.add_argument(
        "--pattern", required=True, help="Regex pattern to match against razor values"
    )
    args = parser.parse_args(argv)

    regex = re.compile(args.pattern, re.IGNORECASE)
    original_matches_exact_pattern = defaultdict(list)
    original_matches_other_pattern = defaultdict(list)
    matched_files_exact = set()
    matched_files_other = set()

    for year, month in _month_span(args):
        path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if path.exists():
            if args.debug:
                print(f"Analyzing: {path}")
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            for record in content.get("data", []):
                razor = record.get("razor")
                if isinstance(razor, dict):
                    original = razor.get("original", "")
                    matched = razor.get("matched")
                    pattern = razor.get("pattern", "")
                    if isinstance(original, str) and regex.search(original):
                        if regex.pattern == pattern:
                            original_matches_exact_pattern[original].append(path.name)
                            matched_files_exact.add(path.name)
                        else:
                            original_matches_other_pattern[(original, pattern)].append(path.name)
                            matched_files_other.add(path.name)
        else:
            if args.debug:
                print(f"Skipped (missing): {path}")

    print(
        f"\n🟢 Matched original razor string AND pattern == regex ({len(original_matches_exact_pattern)} unique):\n"
    )
    for name, files in sorted(original_matches_exact_pattern.items(), key=lambda x: -len(x[1]))[
        : args.limit
    ]:
        print(f"{name:<60}  ({len(files)} uses)")
        for f in sorted(set(files)):
            print(f"    ↳ {f}")

    print(
        f"\n🟡 Matched original razor string BUT pattern != regex ({len(original_matches_other_pattern)} unique):\n"
    )
    for (name, pat), files in sorted(
        original_matches_other_pattern.items(), key=lambda x: -len(x[1])
    )[: args.limit]:
        print(f"{name:<60}  (pattern: {pat})  ({len(files)} uses)")
        for f in sorted(set(files)):
            print(f"    ↳ {f}")


if __name__ == "__main__":
    main()
