#!/usr/bin/env python3
"""Refactored mismatch identification tool for analyzing potential regex mismatches."""

import json
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
from sotd.match.tools.managers.pattern_manager import PatternManager
from sotd.match.tools.utils.analysis_base import AnalysisTool
from sotd.match.tools.utils.mismatch_detector import MismatchDetector
from sotd.match.tools.utils.mismatch_display import MismatchDisplay


class MismatchAnalyzer(AnalysisTool):
    """Analyzer for identifying potential mismatches in matched data."""

    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        console = console or Console()
        self.pattern_manager = PatternManager(console)
        self.correct_matches_manager = CorrectMatchesManager(console)
        self.mismatch_detector = MismatchDetector(console)
        self.mismatch_display = MismatchDisplay(console)

    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for mismatch analysis."""
        parser = BaseCLIParser(
            description="Analyze mismatches in matched data",
            add_date_args=False,
            add_output_args=False,
            add_debug_args=False,
            add_force_args=False,
            require_date_args=False,
        )

        # Main arguments
        parser.add_argument(
            "--field",
            choices=["razor", "blade", "brush", "soap"],
            help="Field to analyze (razor, blade, brush, soap)",
        )
        parser.add_argument(
            "--month",
            help="Month to analyze (YYYY-MM format)",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=3,
            help="Levenshtein distance threshold for similarity (default: 3)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of mismatches to display (default: 50)",
        )
        parser.add_argument(
            "--show-all",
            action="store_true",
            help="Show all matches, not just mismatches",
        )
        parser.add_argument(
            "--mark-correct",
            action="store_true",
            help="Mark displayed matches as correct",
        )
        parser.add_argument(
            "--clear-correct",
            action="store_true",
            help="Clear all correct matches",
        )
        parser.add_argument(
            "--clear-field",
            help="Clear correct matches for a specific field (razor, blade, brush, soap)",
        )
        parser.add_argument(
            "--show-correct",
            action="store_true",
            help="Show summary of correct matches by field",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh of pattern cache",
        )

        return parser

    def run(self, args) -> None:
        """Run the mismatch analyzer."""
        # Handle special commands first
        if args.clear_correct:
            self.correct_matches_manager.clear_correct_matches()
            return

        if args.clear_field:
            if args.clear_field not in ["razor", "blade", "brush", "soap"]:
                self.console.print(
                    "[red]Error: Invalid field. Must be razor, blade, brush, or soap[/red]"
                )
                return
            self.correct_matches_manager.clear_correct_matches_by_field(args.clear_field)
            return

        if args.show_correct:
            self.correct_matches_manager.display_correct_matches_summary()
            return

        # For analysis commands, field and month are required
        if not args.field:
            self.console.print("[red]Error: --field is required for analysis commands[/red]")
            return

        if not args.month:
            self.console.print("[red]Error: --month is required for analysis commands[/red]")
            return

        # Load correct matches
        self.correct_matches_manager.load_correct_matches()

        # Clear cache if forced
        if args.force:
            self.pattern_manager.clear_cache()

        # Load data
        data_path = Path("data") / "matched" / f"{args.month}.json"
        if not data_path.exists():
            self.console.print(f"[red]Error: No matched data found for {args.month}[/red]")
            return

        try:
            with data_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError) as e:
            self.console.print(f"[red]Error loading data: {e}[/red]")
            return

        # Identify mismatches
        mismatches = self.mismatch_detector.identify_mismatches(data, args.field, args)

        # Display results
        if args.show_all:
            self.mismatch_display.display_all_matches(data, args.field, mismatches, args)
        else:
            self.mismatch_display.display_mismatches(mismatches, args.field, args)

        # Show summary
        self._display_analysis_summary(data, args.field)

    def _display_analysis_summary(self, data, field: str) -> None:
        """Display analysis summary."""
        records = data.get("data", [])
        total_confirmed = 0
        total_unconfirmed = 0
        total_exact_matches = 0

        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue
            original = field_data.get("original", "")
            matched = field_data.get("matched", {})
            match_type = field_data.get("match_type", "")
            if not original or not matched:
                continue

            # Count exact matches (from correct_matches.yaml)
            if match_type == "exact":
                total_exact_matches += 1
                total_confirmed += 1
                continue

            # Count other confirmed matches (from previous manual marking)
            match_key = self.correct_matches_manager.create_match_key(field, original, matched)
            if self.correct_matches_manager.is_match_correct(match_key):
                total_confirmed += 1
            else:
                total_unconfirmed += 1

        self.console.print("\n[bold][Summary][/bold]")
        if total_exact_matches > 0:
            self.console.print(
                f"  • Exact matches (from correct_matches.yaml): "
                f"[green]{total_exact_matches}[/green]"
            )
        if total_confirmed > total_exact_matches:
            self.console.print(
                f"  • Previously confirmed: [green]{total_confirmed - total_exact_matches}[/green]"
            )
        self.console.print(f"  • Remaining unconfirmed: [yellow]{total_unconfirmed}[/yellow]")
        self.console.print("")


def get_parser() -> BaseCLIParser:
    """Get CLI parser for mismatch analysis tool."""
    analyzer = MismatchAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the mismatch analysis tool."""
    analyzer = MismatchAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the mismatch analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
