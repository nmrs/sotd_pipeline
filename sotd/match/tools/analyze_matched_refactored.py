#!/usr/bin/env python3
"""Refactored enhanced analysis tool for validating brush matching performance."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import List

from rich.console import Console

from sotd.cli_utils.date_span import month_span
from sotd.match.tools.confidence_analyzer import analyze_match_confidence
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
    all_data = []

    # Collect all data
    for year, month in month_span(args):
        path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                content = json.load(f)
                all_data.extend(content.get("data", []))

    if not all_data:
        console.print("[red]No data found for the specified time period[/red]")
        return

    # Show examples for specific pattern if requested
    if args.show_examples:
        show_pattern_examples(all_data, args.show_examples, args.field, args.example_limit)
        return

    # Extract field-specific data
    field_matches = []
    match_types = []
    confidence_scores = []

    for record in all_data:
        field_data = record.get(args.field, {})
        if isinstance(field_data, dict) and isinstance(field_data.get("matched"), dict):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            field_matches.append((original, brand, model, match_type))
            match_types.append(match_type)

            # Analyze match confidence
            confidence = analyze_match_confidence(original, brand, model, match_type)
            confidence_scores.append(confidence["score"])

    # Summary Statistics
    total_matches = len(field_matches)
    match_type_counts = Counter(match_types)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    potential_mismatches = sum(1 for score in confidence_scores if score < 70)

    # Create summary panel
    summary_panel = generate_summary_panel(
        total_matches, match_type_counts, avg_confidence, potential_mismatches, args.field
    )
    console.print(summary_panel)

    # Show potential mismatches
    if args.show_mismatches:
        console.print()
        show_potential_mismatches(all_data, args.field, args.mismatch_limit)

    # Pattern effectiveness analysis
    if args.show_patterns:
        pattern_stats = get_pattern_effectiveness(all_data, args.field)
        pattern_table = generate_pattern_effectiveness_table(pattern_stats)
        console.print(pattern_table)

    # Improvement opportunities
    if args.show_opportunities:
        opportunities = identify_improvement_opportunities(all_data, args.field)

        if opportunities:
            opp_table = generate_opportunities_table(opportunities)
            console.print(opp_table)
        else:
            console.print("[green]No improvement opportunities identified![/green]")

    # Quality distribution
    if args.show_details:
        confidence_panel = generate_confidence_analysis_panel(confidence_scores, total_matches)
        console.print(confidence_panel)


if __name__ == "__main__":
    main()
