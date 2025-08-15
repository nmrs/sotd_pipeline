#!/usr/bin/env python3
"""
Create YAML file grouping blade strings by pattern type.

This script:
1. Loads the blade count patterns analysis
2. Groups strings by their identified pattern types
3. Saves the grouped data to a YAML file
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


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


def create_yaml_structure(patterns: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Create the YAML structure with pattern names and examples."""
    yaml_data = {}

    # Define friendly names for each pattern type
    pattern_names = {
        "simple_number_parens": "Simple Number Parens",
        "shave_count": "Shave Count",
        "shave_count_parens": "Shave Count Parens",
        "ordinal": "Ordinal Numbers",
        "model_number": "Model Numbers",
        "letter_number_model": "Letter-Number Models",
        "fraction": "Fractions",
        "roman_numeral": "Roman Numerals",
        "written_number": "Written Numbers",
        "blade_count": "Blade Count",
        "price": "Price References",
        "generic_number": "Generic Numbers",
    }

    # Add each pattern with its examples
    for pattern_type, examples in patterns.items():
        friendly_name = pattern_names.get(pattern_type, pattern_type.replace("_", " ").title())
        yaml_data[friendly_name] = examples

    return yaml_data


def save_yaml_file(data: Dict[str, any], output_path: Path) -> None:
    """Save the data to a YAML file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2
            )

        print(f"YAML file saved to {output_path}")

    except Exception as e:
        print(f"Error saving YAML file: {e}")


def main():
    """Main execution function."""
    input_file = Path("analysis/20250815-blade-use-count-analysis.txt")
    output_file = Path("analysis/20250815-blade-use-patterns.yaml")

    print(f"Creating YAML file from {input_file}")

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

    print(f"Loaded {len(blade_strings)} blade strings")

    # Categorize patterns
    print("Categorizing number patterns...")
    patterns = categorize_number_patterns(blade_strings)

    # Create YAML structure
    print("Creating YAML structure...")
    yaml_data = create_yaml_structure(patterns)

    # Save YAML file
    print("Saving YAML file...")
    save_yaml_file(yaml_data, output_file)

    # Show summary
    print("\nYAML Creation Summary:")
    print(f"Total pattern types: {len(patterns)}")
    print(f"Total examples: {sum(len(examples) for examples in patterns.values()):,}")

    print("\nPattern types and counts:")
    for pattern_type, examples in sorted(patterns.items()):
        friendly_name = pattern_type.replace("_", " ").title()
        print(f"  {friendly_name}: {len(examples):,}")


if __name__ == "__main__":
    main()
