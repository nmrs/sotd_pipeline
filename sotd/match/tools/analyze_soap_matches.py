import argparse
import json
from pathlib import Path

from sotd.cli_utils.date_span import _month_span
from sotd.match.soap_matcher import analyze_soap_matches


def collect_soap_matches(input_dir: Path, months: list[str]) -> list[dict]:
    all_matches = []
    for month in months:
        file_path = input_dir / f"{month}.json"
        if not file_path.exists():
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
            for record in content.get("data", []):
                soap = record.get("soap")
                if isinstance(soap, dict):
                    matched = soap.get("matched")
                    if isinstance(matched, dict):
                        all_matches.append(soap)
    if not all_matches:
        print(f"⚠️ No soap matches found in {input_dir} for months: {', '.join(months)}")
        return []
    return all_matches


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze soap matches for likely duplicates.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--month", help="Specific month to analyze (e.g., 2023-05)")
    group.add_argument("--range", help="Month range to analyze (e.g., 2022-01:2023-01)")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/matched"),
        help="Directory of matched JSON files",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.9, help="Fuzzy similarity threshold (default: 0.9)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of duplicate groups shown"
    )
    parser.add_argument("--debug", action="store_true", help="Print debug output")
    args = parser.parse_args(argv)

    months = [f"{y:04d}-{m:02d}" for y, m in _month_span(args)]
    matches = collect_soap_matches(args.input_dir, months)
    if args.debug:
        print(f"✅ Loaded {len(matches)} matched soap entries from {len(months)} months.\n")

    analyze_soap_matches(matches, similarity_threshold=args.threshold, limit=args.limit)


if __name__ == "__main__":
    main()
