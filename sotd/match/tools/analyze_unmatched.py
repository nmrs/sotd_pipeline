import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from sotd.cli_utils.date_span import month_span


def strip_use_count(text: str) -> str:
    """Strip use count from blade text, e.g. 'Koraat (5)' -> 'Koraat'."""
    return re.sub(r"\s*[\(\[\{](?:x)?\d+(?:x)?[\)\]\}]", "", text, flags=re.IGNORECASE).strip()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Analyze unmatched field values (razor, blade, soap, brush) "
        "for pattern and candidate discovery"
    )
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
        help="Maximum number of unmatched entries to show (default: 20)",
    )
    parser.add_argument(
        "--field",
        type=str,
        default="razor",
        choices=["razor", "blade", "soap", "brush", "handle"],
        help="Field to analyze for unmatched entries (default: razor)",
    )
    args = parser.parse_args(argv)

    all_unmatched = defaultdict(list)

    for year, month in month_span(args):
        path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if path.exists():
            if args.debug:
                print(f"Analyzing: {path}")
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            for record in content.get("data", []):
                if args.field == "handle":
                    brush = record.get("brush")
                    if isinstance(brush, dict):
                        matched = brush.get("matched")
                        if matched is None:
                            # If nothing matched at all, count as unmatched handle
                            original = brush.get("original", "")
                            all_unmatched[original].append(path.name)
                        elif isinstance(matched, dict):
                            handle_maker = matched.get("handle_maker")
                            if not handle_maker:
                                original = brush.get("original", "")
                                all_unmatched[original].append(path.name)
                else:
                    field_val = record.get(args.field)
                    if isinstance(field_val, str):
                        # For blades, strip use count before adding to unmatched
                        if args.field == "blade":
                            field_val = strip_use_count(field_val)
                        all_unmatched[field_val].append(path.name)
                    elif isinstance(field_val, dict):
                        if "matched" not in field_val or not field_val["matched"]:
                            # For blades, strip use count from original text
                            original = field_val.get("original", "")
                            if args.field == "blade":
                                original = strip_use_count(original)
                            all_unmatched[original].append(path.name)
        else:
            if args.debug:
                print(f"Skipped (missing): {path}")

    print(
        f"\n🔍 Found {len(all_unmatched)} unique unmatched {args.field} "
        f"descriptions across all files:\n"
    )
    # Sort alphabetically by value, then by file count descending
    for value, files in sorted(all_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1])))[
        : args.limit
    ]:
        print(f"{value:<60}  ({len(files)} uses)")
        for f in sorted(set(files)):
            print(f"    ↳ {f}")


if __name__ == "__main__":
    main()
