import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from sotd.cli_utils.date_span import month_span


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze matched fields using a regex pattern")
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
    parser.add_argument("--pattern", help="Regex pattern to match against field values")
    parser.add_argument(
        "--field",
        choices=["razor", "blade", "brush", "soap"],
        default="razor",
        help="Field to analyze (default: razor)",
    )
    args = parser.parse_args(argv)

    if args.pattern:
        regex = re.compile(args.pattern, re.IGNORECASE)
        original_matches_exact_pattern = defaultdict(list)
        original_matches_other_pattern = defaultdict(list)
        matched_files_exact = set()
        matched_files_other = set()

        for year, month in month_span(args):
            path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
            if path.exists():
                if args.debug:
                    print(f"Analyzing: {path}")
                with path.open("r", encoding="utf-8") as f:
                    content = json.load(f)
                for record in content.get("data", []):
                    field_data = record.get(args.field)
                    if isinstance(field_data, dict):
                        original = field_data.get("original", "")
                        matched = field_data.get("matched")
                        pattern = field_data.get("pattern", "")
                        if isinstance(original, str) and regex.search(original):
                            if regex.pattern == pattern:
                                original_matches_exact_pattern[original].append(path.name)
                                matched_files_exact.add(path.name)
                            else:
                                original_matches_other_pattern[(original, pattern)].append(
                                    path.name
                                )
                                matched_files_other.add(path.name)
            else:
                if args.debug:
                    print(f"Skipped (missing): {path}")

        print(
            f"\n🟢 Matched original {args.field} string AND pattern == regex "
            f"({len(original_matches_exact_pattern)} unique):\n"
        )
        for name, files in sorted(original_matches_exact_pattern.items(), key=lambda x: -len(x[1]))[
            : args.limit
        ]:
            print(f"{name:<60}  ({len(files)} uses)")
            for f in sorted(set(files)):
                print(f"    ↳ {f}")

        print(
            f"\n🟡 Matched original {args.field} string BUT pattern != regex "
            f"({len(original_matches_other_pattern)} unique):\n"
        )
        for (name, pat), files in sorted(
            original_matches_other_pattern.items(), key=lambda x: -len(x[1])
        )[: args.limit]:
            print(f"{name:<60}  (pattern: {pat})  ({len(files)} uses)")
            for f in sorted(set(files)):
                print(f"    ↳ {f}")
    else:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Matched {args.field} Records")
        table.add_column(args.field.capitalize())
        table.add_column("Original")
        table.add_column("Match Type")
        table.add_column("Strategy")
        include_match_type = False
        include_strategy = False

        # Determine if match_type or strategy fields are present
        for year, month in month_span(args):
            path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    content = json.load(f)
                for record in content.get("data", []):
                    field_data = record.get(args.field)
                    if isinstance(field_data, dict) and "matched" in field_data:
                        if "match_type" in field_data:
                            include_match_type = True
                        if "strategy" in field_data:
                            include_strategy = True

        # Print matched table
        seen = set()
        for year, month in month_span(args):
            path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    content = json.load(f)
                for record in content.get("data", []):
                    field_data = record.get(args.field)
                    if isinstance(field_data, dict) and isinstance(field_data.get("matched"), dict):
                        matched = field_data["matched"]
                        row = [
                            f"{matched.get('brand', '')} {matched.get('model', '')}".strip(),
                            field_data.get("original", ""),
                            field_data.get("match_type", "") if include_match_type else "",
                            field_data.get("strategy", "") if include_strategy else "",
                        ]

                        row_key = tuple(str(x) if x is not None else "" for x in row)
                        if row_key not in seen:
                            seen.add(row_key)
        for row_key in sorted(seen, key=lambda x: (x[0] == "", x[0].lower(), x[1].lower())):
            table.add_row(*row_key)
        console.print(table)


if __name__ == "__main__":
    main()
