import argparse
import json
from collections import defaultdict
from pathlib import Path

from sotd.cli_utils.date_span import month_span


def load_matched_data(out_dir: Path, months: list[tuple[int, int]]) -> list[dict]:
    records = []
    for year, month in months:
        filename = out_dir / f"{year:04d}-{month:02d}.json"
        if not filename.exists():
            continue
        with filename.open("r", encoding="utf-8") as f:
            data = json.load(f).get("data", [])
            for record in data:
                record["source_file"] = f"{year:04d}-{month:02d}.json"
            records.extend(data)
    return records


def group_brand_fallbacks(records: list[dict]) -> dict:
    class MatchInfo:
        def __init__(self):
            self.count = 0
            self.files = set()

    grouped = defaultdict(MatchInfo)
    for record in records:
        soap = record.get("soap")
        if not soap or not isinstance(soap, dict):
            continue
        if soap.get("match_type") != "brand_fallback":
            continue
        matched = soap.get("matched")
        if not matched:
            continue
        key = (matched.get("maker"), matched.get("scent"))
        grouped[key].count += 1
        grouped[key].files.add(record.get("source_file", ""))
    return grouped


def print_grouped(grouped: dict, reverse: bool = False):
    sorted_items = sorted(grouped.items(), key=lambda x: x[1].count, reverse=True)[:20]
    if reverse:
        sorted_items = list(reversed(sorted_items))
    print("\n🧼 Candidate scent matches (brand fallback only):\n")
    for (brand, scent), data in sorted_items:
        print(f"{brand} / {scent:<40} ({data.count} uses)")
        if data.files:
            for f in sorted(data.files):
                print(f"    ↳ {f}")
        print()


def group_split_fallbacks(records: list[dict]) -> dict:
    class MatchInfo:
        def __init__(self):
            self.count = 0
            self.files = set()

    grouped = defaultdict(MatchInfo)
    for record in records:
        soap = record.get("soap")
        if not soap or not isinstance(soap, dict):
            continue
        if soap.get("match_type") != "split_fallback":
            continue
        matched = soap.get("matched")
        if not matched:
            continue
        key = (matched.get("maker"), matched.get("scent"))
        grouped[key].count += 1
        grouped[key].files.add(record.get("source_file", ""))
    return grouped


def print_split_fallbacks(grouped: dict, reverse: bool = False):
    # Reorganize grouped data by brand

    class BrandInfo:
        def __init__(self):
            self.total: int = 0
            self.scents: dict[tuple[str, int], list[str]] = {}

    brand_totals = defaultdict(BrandInfo)
    for (brand, scent), data in grouped.items():
        brand_totals[brand].total += data.count
        brand_totals[brand].scents[(scent, data.count)] = sorted(data.files)

    # Sort brands by total usage
    sorted_brands = sorted(brand_totals.items(), key=lambda x: x[1].total, reverse=True)
    if reverse:
        sorted_brands = list(reversed(sorted_brands))

    print("\n🧼 Candidate soap matches (split fallback only):\n")
    for brand, info in sorted_brands:
        print(f"{brand:<35} ({info.total} uses)")
        all_files = sorted({f for files in info.scents.values() for f in files})
        if all_files:
            print(f"--range {all_files[0][:-5]}:{all_files[-1][:-5]}")
        sorted_scents = sorted(info.scents.items(), key=lambda x: x[0][1], reverse=True)
        for (scent, count), files in sorted_scents:
            print(f"  / {scent:<35} ({count} uses)")
            for f in files:
                print(f"    ↳ {f}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Suggest soap patterns for unmatched soaps (brand or scent)."
    )
    parser.add_argument("--month", help="Single YYYY-MM to run")
    parser.add_argument("--year", help="Year to run")
    parser.add_argument("--range", help="Month range, e.g. 2024-01:2025-03")
    parser.add_argument("--start", help="Start date (YYYY-MM)")
    parser.add_argument("--end", help="End date (YYYY-MM)")
    parser.add_argument("--out-dir", default="data/matched", help="Path to matched JSON files")
    parser.add_argument(
        "--mode",
        choices=["scent", "brand"],
        default="scent",
        help="Suggest patterns for 'scent' or 'brand'",
    )
    parser.add_argument(
        "--reverse", action="store_true", help="Reverse the sort order (lowest count first)"
    )
    args = parser.parse_args()

    months = month_span(args)
    out_dir = Path(args.out_dir)
    records = load_matched_data(out_dir, months)

    if args.mode == "scent":
        grouped = group_brand_fallbacks(records)
        print_grouped(grouped, reverse=args.reverse)
    elif args.mode == "brand":
        grouped = group_split_fallbacks(records)
        print_split_fallbacks(grouped, reverse=args.reverse)


if __name__ == "__main__":
    main()
