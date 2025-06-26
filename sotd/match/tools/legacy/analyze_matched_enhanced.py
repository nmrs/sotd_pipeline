#!/usr/bin/env python3
"""Enhanced analysis tool for validating brush matching performance."""

from typing import List

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.analysis_base import AnalysisTool
from sotd.match.tools.cli_utils import BaseAnalysisCLI
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


class EnhancedAnalyzer(AnalysisTool):
    """Enhanced analyzer for product matching performance."""

    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for enhanced analysis tool."""
        parser = BaseCLIParser(
            description="Enhanced analysis of product matching performance",
            add_help=True,
        )

        # Add analysis-specific arguments
        parser.add_argument("--field", choices=["razor", "blade", "brush", "soap"], default="brush")
        BaseAnalysisCLI.add_pattern_arguments(parser)

        return parser

    def run(self, args) -> None:
        """Run the enhanced analysis tool."""
        # Load data
        all_data = load_analysis_data(args)

        if not all_data:
            self.console.print("[red]No data found for the specified time period[/red]")
            return

        # Show examples for specific pattern if requested
        if args.show_examples:
            show_pattern_examples(all_data, args.show_examples, args.field, args.example_limit)
            return

        # Extract and process field data
        field_matches, match_types, confidence_scores = extract_field_data(all_data, args.field)
        summary_stats = calculate_summary_statistics(field_matches, match_types, confidence_scores)

        # Show summary statistics
        self.console.print(
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
            self.console.print()
            show_potential_mismatches(all_data, args.field, args.mismatch_limit)

        # Pattern effectiveness analysis
        if args.show_patterns:
            pattern_stats = get_pattern_effectiveness(all_data, args.field)
            self.console.print(generate_pattern_effectiveness_table(pattern_stats))

        # Improvement opportunities
        if args.show_opportunities:
            opportunities = identify_improvement_opportunities(all_data, args.field)
            self.console.print(generate_opportunities_table(opportunities))

        # Quality distribution
        if args.show_details:
            self.console.print(
                generate_confidence_analysis_panel(
                    confidence_scores, summary_stats["total_matches"]
                )
            )


def get_parser() -> BaseCLIParser:
    """Get CLI parser for enhanced analysis tool."""
    analyzer = EnhancedAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the enhanced analysis tool."""
    analyzer = EnhancedAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the enhanced analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
