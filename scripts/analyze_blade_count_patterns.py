#!/usr/bin/env python3
"""
Analyze blade count patterns from extracted data.

This script analyzes the blade strings containing numbers to identify:
1. Different types of number patterns
2. Common formats and structures
3. Usage patterns and frequencies
4. Examples of each pattern type

Outputs a comprehensive markdown analysis.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_blade_strings(file_path: Path) -> List[str]:
    """Load blade strings from the analysis file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []


def categorize_number_patterns(strings: List[str]) -> Dict[str, List[str]]:
    """
    Categorize strings by their number pattern types.

    Returns a dictionary mapping pattern types to lists of example strings.
    """
    patterns = defaultdict(list)

    for s in strings:
        # Shave count patterns
        if re.search(r"shave\s*#?\s*\d+", s, re.IGNORECASE):
            patterns["shave_count"].append(s)
        elif re.search(r"\(shave\s*#?\s*\d+\)", s, re.IGNORECASE):
            patterns["shave_count_parens"].append(s)

        # Simple number in parentheses
        elif re.search(r"\(\s*\d+\s*\)", s):
            patterns["simple_number_parens"].append(s)

        # Blade model numbers (like FHS-10, ASD-10)
        elif re.search(r"\b[A-Z]+\s*-\s*\d+\b", s):
            patterns["model_number"].append(s)

        # Blade model numbers with letters (like B-20, P-30)
        elif re.search(r"\b[A-Z]\s*-\s*\d+\b", s):
            patterns["letter_number_model"].append(s)

        # Price patterns ($0.19, $0.80)
        elif re.search(r"\$\s*\d+\.\d+", s):
            patterns["price"].append(s)

        # Fraction patterns (1/2, 9/10)
        elif re.search(r"\d+\s*/\s*\d+", s):
            patterns["fraction"].append(s)

        # Ordinal numbers (first, second, third)
        ordinal_pattern = r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b"
        if re.search(ordinal_pattern, s, re.IGNORECASE):
            patterns["ordinal"].append(s)

        # Written numbers (one, two, three)
        written_pattern = r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\b"
        if re.search(written_pattern, s, re.IGNORECASE):
            patterns["written_number"].append(s)

        # Roman numerals (I, II, III, IV, V)
        elif re.search(r"\b[IVX]+\.?\b", s):
            patterns["roman_numeral"].append(s)

        # Blade count patterns (like "2 blade thingys")
        elif re.search(r"\d+\s+blade", s, re.IGNORECASE):
            patterns["blade_count"].append(s)

        # Generic number patterns (any remaining numbers)
        elif re.search(r"\d+", s):
            patterns["generic_number"].append(s)

    return dict(patterns)


def analyze_pattern_frequency(patterns: Dict[str, List[str]]) -> Dict[str, int]:
    """Count the frequency of each pattern type."""
    return {pattern_type: len(examples) for pattern_type, examples in patterns.items()}


def find_common_subpatterns(patterns: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Find common subpatterns within each category."""
    subpatterns = defaultdict(list)

    for pattern_type, examples in patterns.items():
        if pattern_type == "shave_count":
            # Extract shave count numbers
            shave_counts = []
            for s in examples:
                match = re.search(r"shave\s*#?\s*(\d+)", s, re.IGNORECASE)
                if match:
                    shave_counts.append(match.group(1))
            if shave_counts:
                subpatterns[f"{pattern_type}_numbers"] = sorted(set(shave_counts), key=int)

        elif pattern_type == "simple_number_parens":
            # Extract numbers in parentheses
            numbers = []
            for s in examples:
                match = re.search(r"\(\s*(\d+)\s*\)", s)
                if match:
                    numbers.append(match.group(1))
            if numbers:
                subpatterns[f"{pattern_type}_numbers"] = sorted(set(numbers), key=int)

        elif pattern_type == "model_number":
            # Extract model numbers
            models = []
            for s in examples:
                match = re.search(r"\b([A-Z]+)\s*-\s*(\d+)\b", s)
                if match:
                    models.append(f"{match.group(1)}-{match.group(2)}")
            if models:
                subpatterns[f"{pattern_type}_examples"] = sorted(set(models))

    return dict(subpatterns)


def generate_markdown_report(
    patterns: Dict[str, List[str]], frequencies: Dict[str, int], subpatterns: Dict[str, List[str]]
) -> str:
    """Generate a comprehensive markdown report."""

    report = []
    report.append("# Blade Count Patterns Analysis")
    report.append("")
    report.append(
        f"**Analysis Date**: "
        f"{Path('analysis/20250815-blade-use-count-analysis.txt').stat().st_mtime}"
    )
    report.append("")
    report.append("## Overview")
    report.append("")
    report.append("This analysis examines blade strings containing numbers to identify common")
    report.append("patterns and usage structures in SOTD data.")
    report.append("")

    # Pattern frequencies
    report.append("## Pattern Frequencies")
    report.append("")
    report.append("| Pattern Type | Count | Percentage |")
    report.append("|--------------|-------|------------|")

    total = sum(frequencies.values())
    for pattern_type, count in sorted(frequencies.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100 if total > 0 else 0
        report.append(
            f"| {pattern_type.replace('_', ' ').title()} | {count:,} | {percentage:.1f}% |"
        )

    report.append("")

    # Subpattern analysis
    if subpatterns:
        report.append("## Subpattern Analysis")
        report.append("")
        for subpattern_type, values in subpatterns.items():
            report.append(f"### {subpattern_type.replace('_', ' ').title()}")
            report.append("")
            if len(values) <= 20:
                report.append(f"**Values**: {', '.join(values)}")
            else:
                report.append(
                    f"**Values**: {', '.join(values[:20])}... (and {len(values) - 20} more)"
                )
            report.append("")

    # Detailed pattern examples
    report.append("## Pattern Examples")
    report.append("")

    for pattern_type, examples in sorted(patterns.items()):
        report.append(f"### {pattern_type.replace('_', ' ').title()}")
        report.append("")
        report.append(f"**Count**: {len(examples)}")
        report.append("")
        report.append("**Examples**:")
        report.append("")

        # Show first 10 examples
        for i, example in enumerate(examples[:10], 1):
            report.append(f"{i}. `{example}`")

        if len(examples) > 10:
            report.append(f"... and {len(examples) - 10} more")

        report.append("")

    return "\n".join(report)


def main():
    """Main execution function."""
    input_file = Path("analysis/20250815-blade-use-count-analysis.txt")
    output_file = Path("analysis/blade-count-patterns.md")

    print(f"Analyzing blade count patterns from {input_file}")

    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        print("Please run extract_blade_count_strings.py first")
        return

    # Load blade strings
    blade_strings = load_blade_strings(input_file)
    if not blade_strings:
        print("No blade strings found")
        return

    print(f"Loaded {len(blade_strings)} blade strings for analysis")

    # Categorize patterns
    print("Categorizing number patterns...")
    patterns = categorize_number_patterns(blade_strings)

    # Analyze frequencies
    frequencies = analyze_pattern_frequency(patterns)

    # Find subpatterns
    subpatterns = find_common_subpatterns(patterns)

    # Generate report
    print("Generating markdown report...")
    report = generate_markdown_report(patterns, frequencies, subpatterns)

    # Save report
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Report saved to {output_file}")

        # Show summary
        print("\nPattern Analysis Summary:")
        print(f"Total pattern types: {len(patterns)}")
        print(f"Total examples: {sum(frequencies.values()):,}")

        print("\nTop 5 pattern types:")
        for pattern_type, count in sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]:
            print(f"  {pattern_type}: {count:,}")

    except Exception as e:
        print(f"Error saving report: {e}")


if __name__ == "__main__":
    main()
