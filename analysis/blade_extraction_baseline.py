#!/usr/bin/env python3
"""
Blade Extraction Baseline Analysis Tool

Analyzes current blade extraction accuracy across multiple months to establish
a baseline for measuring improvements. Identifies incorrect extractions like
"Uses: 1" vs correct extractions like "Persona Comfort Coat".
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import argparse


class BladeExtractionAnalyzer:
    """Analyzes blade extraction patterns and accuracy."""

    def __init__(self, data_path: Path = Path("data")):
        self.data_path = data_path
        self.incorrect_patterns = [
            r"^Uses?:\s*\d+$",
            r"^Count:\s*\d+$",
            r"^Times?:\s*\d+$",
            r"^Number:\s*\d+$",
            r"^\d+\s*times?$",
            r"^\d+\s*uses?$",
            r"^#\d+$",
            r"^\d+/\d+$",  # like "15/31"
            r"^\d+(?:st|nd|rd|th)\s*use$",
            r"^new$",
            r"^fresh$",
        ]
        self.correct_indicators = [
            r"^[A-Za-z][A-Za-z0-9\s\-\.&'()]+$",  # Brand names
            r".*blade.*",  # Contains "blade"
            r".*razor.*",  # Contains "razor"
            r".*shave.*",  # Contains "shave"
        ]

    def load_month_data(self, month: str) -> Optional[Dict]:
        """Load extracted data for a specific month."""
        file_path = self.data_path / "extracted" / f"{month}.json"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze_blade_extraction(self, data: Dict) -> Dict:
        """Analyze blade extractions in the data."""
        results = {
            "total_shaves": 0,
            "with_blade_field": 0,
            "correct_extractions": 0,
            "incorrect_extractions": 0,
            "incorrect_examples": [],
            "correct_examples": [],
            "pattern_breakdown": defaultdict(int),
            "month": data.get("meta", {}).get("month", "unknown"),
        }

        for entry in data.get("data", []):
            results["total_shaves"] += 1

            if "blade" in entry:
                results["with_blade_field"] += 1
                blade_data = entry["blade"]
                original = blade_data.get("original", "")

                if self.is_incorrect_extraction(original):
                    results["incorrect_extractions"] += 1
                    results["incorrect_examples"].append(
                        {
                            "id": entry.get("id", "unknown"),
                            "author": entry.get("author", "unknown"),
                            "original": original,
                            "body_snippet": self.extract_body_snippet(
                                entry.get("body", ""), original
                            ),
                        }
                    )
                    # Track which pattern matched
                    for pattern in self.incorrect_patterns:
                        if re.match(pattern, original, re.IGNORECASE):
                            results["pattern_breakdown"][pattern] += 1
                            break
                else:
                    results["correct_extractions"] += 1
                    results["correct_examples"].append(
                        {
                            "id": entry.get("id", "unknown"),
                            "author": entry.get("author", "unknown"),
                            "original": original,
                        }
                    )

        return results

    def is_incorrect_extraction(self, text: str) -> bool:
        """Determine if a blade extraction is likely incorrect."""
        if not text or not isinstance(text, str):
            return False

        text = text.strip()

        # Check against known incorrect patterns
        for pattern in self.incorrect_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        # Check if it's too short to be a real blade name
        if len(text) < 3:
            return True

        # Check if it's just a number
        if text.isdigit():
            return True

        return False

    def extract_body_snippet(self, body: str, target_text: str) -> str:
        """Extract a snippet of the body text around the target text."""
        if not body or not target_text:
            return ""

        # Find the line containing the target text
        lines = body.split("\n")
        for line in lines:
            if target_text in line:
                return line.strip()

        return ""

    def analyze_multiple_months(self, months: List[str]) -> Dict:
        """Analyze blade extraction across multiple months."""
        results = {
            "months": {},
            "summary": {
                "total_months": len(months),
                "total_shaves": 0,
                "total_with_blade": 0,
                "total_correct": 0,
                "total_incorrect": 0,
                "accuracy_rate": 0.0,
            },
        }

        for month in months:
            print(f"Analyzing {month}...")
            data = self.load_month_data(month)
            if data:
                month_results = self.analyze_blade_extraction(data)
                results["months"][month] = month_results

                # Update summary
                results["summary"]["total_shaves"] += month_results["total_shaves"]
                results["summary"]["total_with_blade"] += month_results["with_blade_field"]
                results["summary"]["total_correct"] += month_results["correct_extractions"]
                results["summary"]["total_incorrect"] += month_results["incorrect_extractions"]

        # Calculate overall accuracy
        if results["summary"]["total_with_blade"] > 0:
            results["summary"]["accuracy_rate"] = (
                results["summary"]["total_correct"] / results["summary"]["total_with_blade"]
            )

        return results

    def generate_report(self, results: Dict) -> str:
        """Generate a detailed analysis report."""
        report = []
        report.append("# Blade Extraction Baseline Analysis Report")
        report.append("=" * 50)
        report.append("")

        # Summary
        summary = results["summary"]
        report.append("## Summary")
        report.append(f"- Total months analyzed: {summary['total_months']}")
        report.append(f"- Total shaves: {summary['total_shaves']:,}")
        report.append(f"- Shaves with blade field: {summary['total_with_blade']:,}")
        report.append(f"- Correct extractions: {summary['total_correct']:,}")
        report.append(f"- Incorrect extractions: {summary['total_incorrect']:,}")
        report.append(f"- Accuracy rate: {summary['accuracy_rate']:.2%}")
        report.append("")

        # Monthly breakdown
        report.append("## Monthly Breakdown")
        for month, data in results["months"].items():
            accuracy = 0.0
            if data["with_blade_field"] > 0:
                accuracy = data["correct_extractions"] / data["with_blade_field"]

            report.append(f"### {month}")
            report.append(f"- Total shaves: {data['total_shaves']:,}")
            report.append(f"- With blade field: {data['with_blade_field']:,}")
            report.append(f"- Correct: {data['correct_extractions']:,}")
            report.append(f"- Incorrect: {data['incorrect_extractions']:,}")
            report.append(f"- Accuracy: {accuracy:.2%}")
            report.append("")

        # Pattern breakdown
        all_patterns = defaultdict(int)
        for month_data in results["months"].values():
            for pattern, count in month_data["pattern_breakdown"].items():
                all_patterns[pattern] += count

        if all_patterns:
            report.append("## Incorrect Pattern Breakdown")
            for pattern, count in sorted(all_patterns.items(), key=lambda x: x[1], reverse=True):
                report.append(f"- `{pattern}`: {count:,} occurrences")
            report.append("")

        # Examples
        report.append("## Sample Incorrect Extractions")
        sample_incorrect = []
        for month_data in results["months"].values():
            sample_incorrect.extend(month_data["incorrect_examples"][:5])  # Top 5 per month

        for i, example in enumerate(sample_incorrect[:20], 1):  # Show top 20
            report.append(f"{i}. **{example['original']}** (ID: {example['id']})")
            if example["body_snippet"]:
                report.append(f"   Context: `{example['body_snippet']}`")
            report.append("")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Analyze blade extraction accuracy")
    parser.add_argument(
        "--months", nargs="+", default=["2025-08", "2025-09", "2025-10"], help="Months to analyze"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/blade_extraction_baseline_report.md"),
        help="Output report file",
    )

    args = parser.parse_args()

    analyzer = BladeExtractionAnalyzer()
    results = analyzer.analyze_multiple_months(args.months)

    # Generate and save report
    report = analyzer.generate_report(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Analysis complete. Report saved to {args.output}")
    print(f"Overall accuracy: {results['summary']['accuracy_rate']:.2%}")
    print(f"Incorrect extractions: {results['summary']['total_incorrect']:,}")


if __name__ == "__main__":
    main()
