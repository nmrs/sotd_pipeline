#!/usr/bin/env python3
"""Focused module for soap-specific analysis functionality."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.cli_utils.date_span import month_span
from sotd.match.soap_matcher import analyze_soap_matches


class SoapAnalyzer:
    """Analyzer for soap-specific analysis functionality."""

    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for soap analysis tool."""
        parser = BaseCLIParser(
            description="Analyze soap matches for likely duplicates and pattern suggestions",
            add_help=True,
        )

        # Add soap-specific arguments
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
            "--mode",
            choices=["scent", "brand"],
            default="scent",
            help="Suggest patterns for 'scent' or 'brand'",
        )
        parser.add_argument(
            "--reverse", action="store_true", help="Reverse the sort order (lowest count first)"
        )

        return parser

    def run(self, args) -> None:
        """Run the soap analysis tool."""
        if hasattr(args, "threshold") and hasattr(args, "input_dir"):
            # Duplicate detection mode
            self._run_duplicate_detection(args)
        else:
            # Pattern suggestion mode
            self._run_pattern_suggestions(args)

    def _run_duplicate_detection(self, args) -> None:
        """Run soap duplicate detection analysis."""
        months = [f"{y:04d}-{m:02d}" for y, m in month_span(args)]
        matches = self._collect_soap_matches(args.input_dir, months)

        if args.debug:
            print(f"✅ Loaded {len(matches)} matched soap entries from {len(months)} months.\n")

        analyze_soap_matches(matches, similarity_threshold=args.threshold, limit=args.limit)

    def _run_pattern_suggestions(self, args) -> None:
        """Run soap pattern suggestion analysis."""
        months = month_span(args)
        records = self._load_matched_data(args.out_dir, months)

        if args.mode == "scent":
            grouped = self._group_brand_fallbacks(records)
            self._print_grouped(grouped, reverse=args.reverse)
        elif args.mode == "brand":
            grouped = self._group_split_fallbacks(records)
            self._print_split_fallbacks(grouped, reverse=args.reverse)

    def _collect_soap_matches(self, input_dir: Path, months: List[str]) -> List[Dict]:
        """Collect soap matches from files."""
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

    def _load_matched_data(self, out_dir: Path, months: List[tuple[int, int]]) -> List[Dict]:
        """Load matched data from files."""
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

    def _group_brand_fallbacks(self, records: List[Dict]) -> Dict:
        """Group brand fallback matches."""

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

    def _group_split_fallbacks(self, records: List[Dict]) -> Dict:
        """Group split fallback matches."""

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

    def _print_grouped(self, grouped: Dict, reverse: bool = False) -> None:
        """Print grouped brand fallback results."""
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

    def _print_split_fallbacks(self, grouped: Dict, reverse: bool = False) -> None:
        """Print split fallback results."""

        class BrandInfo:
            def __init__(self):
                self.total: int = 0
                self.scents: Dict[tuple[str, int], List[str]] = {}

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


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the soap analysis tool."""
    analyzer = SoapAnalyzer()
    parser = analyzer.get_parser()
    args = parser.parse_args(argv)
    analyzer.run(args)


if __name__ == "__main__":
    main()
