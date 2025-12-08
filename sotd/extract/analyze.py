import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sotd.extract.fields import extract_field_with_pattern, get_patterns
from sotd.utils.aliases import FIELD_ALIASES
from sotd.utils.text import preprocess_body


def analyze_skipped_patterns(
    paths: Iterable[Path], top_n: int = 20, show_examples: int = 3, show_all: bool = False
) -> None:
    # keywords = ["razor", "blade", "brush", "soap", "lather", "post", "pre", "prep", "aftershave"]
    keywords = [k.lower() for k in ["razor", "blade", "brush", "soap", "lather"]]
    pattern_counts = Counter()
    examples = {}

    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
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
        with open(path, "r", encoding="utf-8") as f:
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
            with open(path, "r", encoding="utf-8") as f:
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


def analyze_pattern_usage(paths: Iterable[Path]) -> None:
    """
    Analyze which extraction patterns match razor fields in comment files.

    Processes all provided comment files, tracks which pattern index (0-14)
    matched each razor field extraction, and prints a table of usage statistics.
    """
    pattern_counts = Counter()
    total_razors = 0

    # Pattern descriptions based on get_patterns() comments (ordered by frequency)
    pattern_descriptions = {
        0: "Markdown bold: * **alias:** value",
        1: "Simple explicit: Field: Value",
        2: "Markdown bold: * **alias**: value",
        3: "Emoji-prefixed: *alias:* value",
        4: "Emoji-prefixed: *alias:* value (variant 2)",
        5: "Markdown bold: * **Field** Value (no separator)",
        6: "Emoji-prefixed: *alias:* value (variant)",
        7: "Markdown bold: * **alias - value**",
        8: "Underscore: __alias:__ value",
        9: "Forward slash: **alias //** value",
        10: "Checkmark: ✓Field: Value",
        11: "Double hash: ##alias## - value",
        12: "Simple explicit: Field - Value",
        13: "Ambiguous: Field Value (no markers)",
    }

    # Get razor patterns for base "razor" alias (this gives us the 0-13 pattern indices)
    base_patterns = get_patterns("razor")
    patterns_per_alias = len(base_patterns)  # Should be 14 (0-13)

    # Get all aliases for razor (to match actual extraction behavior)
    aliases = FIELD_ALIASES.get("razor", ["razor"])

    # Process all comment files
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skipped missing file: {path}")
            continue

        # Process all comments in the file
        for comment in data.get("data", []):
            # Preprocess body (same as parse_comment)
            if "body" in comment:
                body = preprocess_body(comment["body"])
            else:
                body = None

            if not body:
                continue

            lines = body.splitlines()
            # Remove markdown links (same as parse_comment)
            lines = [re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line) for line in lines]

            # Try patterns in order (pattern priority), then lines, matching actual extraction logic
            matched_pattern_index = None
            for alias in aliases:
                alias_patterns = get_patterns(alias)
                for pattern_index_in_alias, pattern in enumerate(alias_patterns):
                    for line in lines:
                        value = extract_field_with_pattern(line, "razor", pattern)
                        if value:
                            # Map pattern index back to base "razor" pattern index (0-14)
                            matched_pattern_index = pattern_index_in_alias
                            break
                    if matched_pattern_index is not None:
                        break
                if matched_pattern_index is not None:
                    break

            if matched_pattern_index is not None:
                pattern_counts[matched_pattern_index] += 1
                total_razors += 1

    # Print results table
    print("\nPattern Usage Analysis for Razor Field:")
    print("=" * 80)
    print(f"{'Pattern':<8} | {'Description':<45} | {'Count':<10} | {'Percentage':<10}")
    print("-" * 80)

    # Create list of all patterns with their counts (0 for unmatched)
    all_patterns = []
    for pattern_index in range(patterns_per_alias):
        count = pattern_counts.get(pattern_index, 0)
        all_patterns.append((pattern_index, count))

    # Sort by count (descending), then by pattern index
    sorted_patterns = sorted(all_patterns, key=lambda x: (x[1], -x[0]), reverse=True)

    for pattern_index, count in sorted_patterns:
        percentage = (count / total_razors * 100) if total_razors > 0 else 0
        description = pattern_descriptions.get(pattern_index, f"Pattern {pattern_index}")
        print(f"{pattern_index:<8} | {description:<45} | {count:<10,} | {percentage:>9.2f}%")

    print("-" * 80)
    print(f"Total razor extractions: {total_razors:,}")
    print()


# CLI entry point for running analyses
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--examples", type=int, default=3)
    parser.add_argument(
        "--mode", choices=["skipped", "garbage", "missing", "prefix", "pattern"], default="skipped"
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
    elif args.mode == "pattern":
        analyze_pattern_usage(args.paths)
