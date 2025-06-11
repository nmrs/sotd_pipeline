import argparse
import json
from collections import defaultdict
from pathlib import Path

from sotd.cli_utils.date_span import _month_span


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
        choices=["razor", "blade", "soap", "brush"],
        help="Field to analyze for unmatched entries (default: razor)",
    )
    args = parser.parse_args(argv)

    all_unmatched = defaultdict(list)

    for year, month in _month_span(args):
        path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if path.exists():
            if args.debug:
                print(f"Analyzing: {path}")
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            for record in content.get("data", []):
                field_val = record.get(args.field)
                if isinstance(field_val, str):
                    all_unmatched[field_val].append(path.name)
                elif isinstance(field_val, dict):
                    if "matched" not in field_val or not field_val["matched"]:
                        all_unmatched[field_val.get("original", "")].append(path.name)
        else:
            if args.debug:
                print(f"Skipped (missing): {path}")

    print(
        f"\n🔍 Found {len(all_unmatched)} unique unmatched {args.field} "
        f"descriptions across all files:\n"
    )
    for value, files in sorted(all_unmatched.items(), key=lambda x: -len(x[1]))[: args.limit]:
        print(f"{value:<60}  ({len(files)} uses)")
        for f in sorted(set(files)):
            print(f"    ↳ {f}")


if __name__ == "__main__":
    main()
