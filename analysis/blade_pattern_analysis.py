#!/usr/bin/env python3
"""
Blade Pattern Analysis Tool

Analyzes the specific regex patterns in sotd/extract/fields.py to identify
which patterns are causing incorrect blade extractions.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from sotd.extract.fields import get_patterns
from sotd.utils.aliases import FIELD_ALIASES


class BladePatternAnalyzer:
    """Analyzes blade extraction patterns to identify problematic ones."""

    def __init__(self):
        self.problematic_cases = [
            "Blade Uses: 1",
            "Blade Count: 5",
            "Blade Times: 3",
            "Blade Number: 2",
        ]
        self.correct_cases = [
            "Blade: Persona Comfort Coat",
            "Blade - Persona Comfort Coat",
            "Blade Persona Comfort Coat",
            "Blade (1)",
            "Blade 1",
            "Blade: 1",
            "Blade - 1",
        ]

    def analyze_patterns(self) -> Dict:
        """Analyze all blade extraction patterns."""
        results = {
            "total_patterns": 0,
            "problematic_patterns": [],
            "correct_patterns": [],
            "pattern_analysis": [],
        }

        # Get all patterns for blade field
        patterns = get_patterns("blade")
        results["total_patterns"] = len(patterns)

        for i, pattern in enumerate(patterns):
            pattern_analysis = {
                "index": i + 1,
                "pattern": pattern,
                "matches_problematic": [],
                "matches_correct": [],
                "is_problematic": False,
            }

            # Test against problematic cases
            for case in self.problematic_cases:
                match = re.match(pattern, case, re.IGNORECASE)
                if match:
                    pattern_analysis["matches_problematic"].append(
                        {"case": case, "captured": match.group(1) if match.groups() else None}
                    )
                    pattern_analysis["is_problematic"] = True

            # Test against correct cases
            for case in self.correct_cases:
                match = re.match(pattern, case, re.IGNORECASE)
                if match:
                    pattern_analysis["matches_correct"].append(
                        {"case": case, "captured": match.group(1) if match.groups() else None}
                    )

            results["pattern_analysis"].append(pattern_analysis)

            if pattern_analysis["is_problematic"]:
                results["problematic_patterns"].append(pattern_analysis)
            else:
                results["correct_patterns"].append(pattern_analysis)

        return results

    def generate_report(self, results: Dict) -> str:
        """Generate a detailed pattern analysis report."""
        report = []
        report.append("# Blade Pattern Analysis Report")
        report.append("=" * 40)
        report.append("")

        report.append(f"## Summary")
        report.append(f"- Total patterns: {results['total_patterns']}")
        report.append(f"- Problematic patterns: {len(results['problematic_patterns'])}")
        report.append(f"- Correct patterns: {len(results['correct_patterns'])}")
        report.append("")

        # Problematic patterns
        if results["problematic_patterns"]:
            report.append("## Problematic Patterns")
            report.append("These patterns incorrectly match usage count fields:")
            report.append("")

            for pattern_info in results["problematic_patterns"]:
                report.append(f"### Pattern {pattern_info['index']}")
                report.append(f"```regex")
                report.append(pattern_info["pattern"])
                report.append("```")
                report.append("")

                if pattern_info["matches_problematic"]:
                    report.append("**Matches problematic cases:**")
                    for match in pattern_info["matches_problematic"]:
                        report.append(f"- `{match['case']}` → `{match['captured']}`")
                    report.append("")

                if pattern_info["matches_correct"]:
                    report.append("**Also matches correct cases:**")
                    for match in pattern_info["matches_correct"]:
                        report.append(f"- `{match['case']}` → `{match['captured']}`")
                    report.append("")

        # All patterns analysis
        report.append("## All Patterns Analysis")
        for pattern_info in results["pattern_analysis"]:
            status = "❌ PROBLEMATIC" if pattern_info["is_problematic"] else "✅ OK"
            report.append(f"### Pattern {pattern_info['index']} {status}")
            report.append(f"```regex")
            report.append(pattern_info["pattern"])
            report.append("```")

            if pattern_info["matches_problematic"]:
                report.append("**Problematic matches:**")
                for match in pattern_info["matches_problematic"]:
                    report.append(f"- `{match['case']}` → `{match['captured']}`")
                report.append("")

            if pattern_info["matches_correct"]:
                report.append("**Correct matches:**")
                for match in pattern_info["matches_correct"]:
                    report.append(f"- `{match['case']}` → `{match['captured']}`")
                report.append("")

        return "\n".join(report)

    def suggest_fixes(self, results: Dict) -> List[str]:
        """Suggest specific fixes for problematic patterns."""
        suggestions = []

        for pattern_info in results["problematic_patterns"]:
            pattern = pattern_info["pattern"]
            suggestions.append(f"Pattern {pattern_info['index']}: {pattern}")

            # Analyze the specific issue
            if r"\b{alias}\b\s+(.+)$" in pattern:
                suggestions.append("  Issue: Too permissive - matches any text after 'blade'")
                suggestions.append("  Fix: Add word boundary check or remove this pattern")
                suggestions.append(
                    "  Alternative: Use more specific patterns that require colons/dashes"
                )
                suggestions.append("")
            elif r"\s*[-:]\s*" in pattern and not r"\b{alias}\b\s*[-:]\s*" in pattern:
                suggestions.append(
                    "  Issue: Pattern allows other words between field name and colon"
                )
                suggestions.append(
                    "  Fix: Use word boundaries to ensure field name is immediately followed by colon"
                )
                suggestions.append("")

        return suggestions


def main():
    analyzer = BladePatternAnalyzer()
    results = analyzer.analyze_patterns()

    # Generate report
    report = analyzer.generate_report(results)
    report_path = Path("analysis/blade_pattern_analysis_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Pattern analysis complete. Report saved to {report_path}")

    # Show suggestions
    suggestions = analyzer.suggest_fixes(results)
    if suggestions:
        print("\nSuggested fixes:")
        for suggestion in suggestions:
            print(suggestion)


if __name__ == "__main__":
    main()
