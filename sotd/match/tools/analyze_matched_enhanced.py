#!/usr/bin/env python3
"""Enhanced analysis tool for validating brush matching performance."""

import argparse
from typing import List

from rich.console import Console

from sotd.match.tools.data_processor import (
    calculate_summary_statistics,
    extract_field_data,
    load_analysis_data,
)
from sotd.match.tools.pattern_analyzer import (
    get_pattern_effectiveness,
    identify_improvement_opportunities,
)
from sotd.match.tools.report_generator import (
    generate_confidence_analysis_panel,
    generate_opportunities_table,
    generate_pattern_effectiveness_table,
    generate_summary_panel,
    show_pattern_examples,
    show_potential_mismatches,
)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Enhanced analysis of product matching performance"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--month", type=str)
    group.add_argument("--year", type=int)
    group.add_argument("--range", type=str)
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--field", choices=["razor", "blade", "brush", "soap"], default="brush")
    parser.add_argument("--show-details", action="store_true", help="Show detailed match analysis")
    parser.add_argument("--show-patterns", action="store_true", help="Show pattern effectiveness")
    parser.add_argument(
        "--show-opportunities", action="store_true", help="Show improvement opportunities"
    )
    parser.add_argument("--show-mismatches", action="store_true", help="Show potential mismatches")
    parser.add_argument(
        "--show-examples",
        type=str,
        help="Show examples for specific pattern (e.g., 'Chisel & Hound Badger')",
    )
    parser.add_argument("--mismatch-limit", type=int, default=20, help="Limit mismatches shown")
    parser.add_argument("--example-limit", type=int, default=15, help="Limit examples shown")
    args = parser.parse_args(argv)

    console = Console()

    # Load data
    all_data = load_analysis_data(args)

    if not all_data:
        console.print("[red]No data found for the specified time period[/red]")
        return

    # Show examples for specific pattern if requested
    if args.show_examples:
        show_pattern_examples(all_data, args.show_examples, args.field, args.example_limit)
        return

    # Extract and process field data
    field_matches, match_types, confidence_scores = extract_field_data(all_data, args.field)
    summary_stats = calculate_summary_statistics(field_matches, match_types, confidence_scores)

    # Show summary statistics
    console.print(
        generate_summary_panel(
            summary_stats["total_matches"],
            summary_stats["match_type_counts"],
            summary_stats["avg_confidence"],
            summary_stats["potential_mismatches"],
            args.field,
        )
    )

    # Show potential mismatches
    if args.show_mismatches:
        console.print()
        show_potential_mismatches(all_data, args.field, args.mismatch_limit)

    # Pattern effectiveness analysis
    if args.show_patterns:
        pattern_stats = get_pattern_effectiveness(all_data, args.field)
        console.print(generate_pattern_effectiveness_table(pattern_stats))

    # Improvement opportunities
    if args.show_opportunities:
        opportunities = identify_improvement_opportunities(all_data, args.field)
        console.print(generate_opportunities_table(opportunities))

    # Quality distribution
    if args.show_details:
        console.print(
            generate_confidence_analysis_panel(confidence_scores, summary_stats["total_matches"])
        )


if __name__ == "__main__":
    main()
