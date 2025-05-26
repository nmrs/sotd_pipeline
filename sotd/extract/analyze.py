import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


def analyze_skipped_patterns(
    paths: Iterable[Path], top_n: int = 20, show_examples: int = 3, show_all: bool = False
) -> None:
    # keywords = ["razor", "blade", "brush", "soap", "lather", "post", "pre", "prep", "aftershave"]
    keywords = [k.lower() for k in ["razor", "blade", "brush", "soap", "lather"]]
    pattern_counts = Counter()
    examples = {}

    for path in paths:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skipped missing file: {path}")
            continue
        for comment in data.get("skipped", []):
            for line in comment.get("body", "").splitlines():
                if not show_all and not any(k in line.lower() for k in keywords):
                    continue
                key = categorize_line(line)
                pattern_counts[key] += 1
                examples.setdefault(key, []).append(line)

    print(f"\nTop {top_n} skipped line categories (out of {len(pattern_counts)} total patterns):\n")
    for pattern, count in pattern_counts.most_common(top_n):
        print(f"{pattern:40} — {count} occurrences")
        for ex in examples[pattern][:show_examples]:
            print(f"   ↳ {ex}")
        print()


def categorize_line(line: str) -> str:
    if not line:
        return "<blank line>"
    if line.startswith("* "):
        return "* markdown"
    if re.match(r"^\*\s##\w+##\s*[-:]", line):
        return "bullet markdown"
    if re.match(r"^[A-Z][a-z]+:", line):
        return "TitleCase colon"
    if ":" in line:
        return "generic colon line"
    if "-" in line:
        return "contains dash"
    return "<other>"


# Analyze leading non-word character sequences in comment fields of JSON files
def analyze_garbage_leading_chars(
    paths: Iterable[Path], top_n: int = 20, show_examples: int = 3
) -> None:
    garbage_counter = Counter()
    examples = {}

    fields = ["razor", "blade", "brush", "soap"]

    for path in paths:
        with open(path, "r") as f:
            data = json.load(f)
            for comment in data.get("data", []):
                for field in fields:
                    value = comment.get(field)
                    if not isinstance(value, str):
                        continue
                    match = re.match(r"^\W+", value)
                    if match:
                        key = match.group()
                        garbage_counter[key] += 1
                        examples.setdefault(key, []).append((field, value))

    print(f"\nTop {top_n} leading non-word character sequences:\n")
    for seq, count in garbage_counter.most_common(top_n):
        print(f"'{seq}': {count} occurrences")
        for field, val in examples[seq][:show_examples]:
            print(f'   ↳ {field}="{val}"')
        print()


def analyze_missing_files(paths: Iterable[Path], *_args) -> None:
    # Infer date range from given paths
    months = sorted(path.stem for path in paths if path.stem.count("-") == 1)
    if not months:
        print("No valid YYYY-MM filenames found.")
        return

    first = datetime.strptime(months[0], "%Y-%m")
    last = datetime.strptime(months[-1], "%Y-%m")
    current = first
    expected = set()

    while current <= last:
        ym = current.strftime("%Y-%m")
        expected.add(ym)
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    present = set(months)
    missing = sorted(expected - present)

    print("\nMissing files in data/extracted/:\n")
    for ym in missing:
        print(f"  - {ym}.json")


def analyze_common_prefixes(
    paths: Iterable[Path], top_n: int = 20, show_examples: int = 3, show_all: bool = False
) -> None:
    keywords = [k.lower() for k in ["razor", "blade", "brush", "soap", "lather"]]
    lines = []

    for path in paths:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skipped missing file: {path}")
            continue
        short_path = f"extracted/{path.stem}.json"
        for comment in data.get("skipped", []):
            for line in comment.get("body", "").splitlines():
                if not show_all and not any(k in line.lower() for k in keywords):
                    continue
                lines.append((line, short_path))

    if not lines:
        print("No lines found for prefix analysis.")
        return

    prefix_length = 1
    buckets = {"": lines}
    while True:
        new_buckets = {}
        for group in buckets.values():
            if len(group) <= 1:
                for line, path in group:
                    new_buckets[line] = [(line, path)]
                continue
            for line, path in group:
                key = line[:prefix_length] if len(line) >= prefix_length else line
                new_buckets.setdefault(key, []).append((line, path))
        if new_buckets == buckets:
            break
        if all(len(g) == 1 for g in new_buckets.values()):
            buckets = new_buckets
            break
        buckets = new_buckets
        prefix_length += 1

    sorted_buckets = sorted(
        ((prefix, group) for prefix, group in buckets.items()),
        key=lambda x: (-len(x[1]), -len(x[0])),
    )

    print(f"\nTop {top_n} common prefix buckets (out of {len(sorted_buckets)} total buckets):\n")
    for prefix, group in sorted_buckets[:top_n]:
        print(f"Prefix: '{prefix}' — {len(group)} occurrences")
        # Print full example lines from each prefix bucket
        for ex in group[:show_examples]:
            line, filename = ex
            print(f"   ↳ ({filename}) {line}")
        print()


# CLI entry point for running analyses
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--examples", type=int, default=3)
    parser.add_argument(
        "--mode", choices=["skipped", "garbage", "missing", "prefix"], default="skipped"
    )
    parser.add_argument("--all", action="store_true", help="Include lines without known keywords")
    args = parser.parse_args()

    if args.mode == "skipped":
        analyze_skipped_patterns(args.paths, args.top, args.examples, args.all)
    elif args.mode == "garbage":
        analyze_garbage_leading_chars(args.paths, args.top, args.examples)
    elif args.mode == "missing":
        analyze_missing_files(args.paths)
    elif args.mode == "prefix":
        analyze_common_prefixes(args.paths, args.top, args.examples, args.all)
