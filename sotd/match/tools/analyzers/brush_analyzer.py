#!/usr/bin/env python3
"""Focused module for brush-specific analysis functionality."""

from collections import defaultdict
from typing import Dict, List

from rich.table import Table

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.utils.analysis_base import AnalysisTool
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI


class BrushAnalyzer(AnalysisTool):
    """Analyzer for brush-specific analysis functionality."""

    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for brush analysis tool."""
        parser = BaseCLIParser(
            description="Analyze brush matches for patterns and improvements",
            add_help=True,
        )

        # Add brush-specific arguments
        BaseAnalysisCLI.add_common_arguments(parser)
        BaseAnalysisCLI.add_pattern_arguments(parser)
        BaseAnalysisCLI.add_confidence_arguments(parser)
        BaseAnalysisCLI.add_field_analysis_arguments(parser)

        # Override default field to brush
        parser.set_defaults(field="brush")

        return parser

    def run(self, args) -> None:
        """Run the brush analysis tool."""
        # Load data
        all_data = self.load_matched_data(args)

        if not all_data:
            self.console.print("[red]No data found for the specified time period[/red]")
            return

        # Extract brush data
        brush_matches, match_types, confidence_scores = self.extract_field_data(all_data, "brush")

        if not brush_matches:
            self.console.print("[yellow]No brush matches found in the data[/yellow]")
            return

        # Show summary statistics
        self._show_summary_stats(brush_matches, match_types, confidence_scores)

        # Show pattern analysis if requested
        if args.show_patterns:
            self._show_pattern_analysis(all_data)

        # Show confidence analysis if requested
        if args.show_confidence_distribution:
            self._show_confidence_analysis(confidence_scores)

        # Show field breakdown if requested
        if args.show_field_breakdown:
            self._show_field_breakdown(brush_matches)

        # Show potential mismatches if requested
        if args.show_mismatches:
            self._show_potential_mismatches(all_data, args.mismatch_limit)

    def _show_summary_stats(
        self, brush_matches: List[Dict], match_types: List[str], confidence_scores: List[float]
    ) -> None:
        """Show summary statistics for brush matches."""
        total_matches = len(brush_matches)
        match_type_counts = defaultdict(int)
        for match_type in match_types:
            match_type_counts[match_type] += 1

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        low_confidence_count = sum(1 for score in confidence_scores if score < 70)

        table = Table(title="Brush Matching Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Matches", str(total_matches))
        table.add_row("Average Confidence", f"{avg_confidence:.1f}%")
        table.add_row("Low Confidence (<70%)", f"{low_confidence_count}")

        for match_type, count in sorted(match_type_counts.items()):
            percentage = (count / total_matches) * 100
            table.add_row(f"{match_type.title()} Matches", f"{count} ({percentage:.1f}%)")

        self.console.print(table)

    def _show_pattern_analysis(self, all_data: List[Dict]) -> None:
        """Show pattern analysis for brushes."""
        pattern_stats = defaultdict(lambda: {"count": 0, "exact": 0, "confidence_sum": 0})

        for record in all_data:
            brush = record.get("brush", {})
            if isinstance(brush, dict) and brush.get("matched"):
                pattern = brush.get("pattern", "")
                match_type = brush.get("match_type", "")
                confidence = brush.get("confidence", 0)

                pattern_stats[pattern]["count"] += 1
                pattern_stats[pattern]["confidence_sum"] += confidence
                if match_type == "exact":
                    pattern_stats[pattern]["exact"] += 1

        table = Table(title="Brush Pattern Analysis")
        table.add_column("Pattern", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Exact%", justify="right")
        table.add_column("Avg Conf", justify="right")

        for pattern, stats in sorted(
            pattern_stats.items(), key=lambda x: x[1]["count"], reverse=True
        ):
            exact_rate = (stats["exact"] / stats["count"]) * 100 if stats["count"] > 0 else 0
            avg_confidence = stats["confidence_sum"] / stats["count"] if stats["count"] > 0 else 0

            table.add_row(
                pattern,
                str(stats["count"]),
                f"{exact_rate:.1f}%",
                f"{avg_confidence:.1f}",
            )

        self.console.print(table)

    def _show_confidence_analysis(self, confidence_scores: List[float]) -> None:
        """Show confidence score distribution."""
        if not confidence_scores:
            return

        high_conf = sum(1 for score in confidence_scores if score >= 80)
        med_conf = sum(1 for score in confidence_scores if 60 <= score < 80)
        low_conf = sum(1 for score in confidence_scores if score < 60)
        total = len(confidence_scores)

        table = Table(title="Brush Confidence Distribution")
        table.add_column("Range", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        table.add_row("High (80-100%)", str(high_conf), f"{(high_conf / total) * 100:.1f}%")
        table.add_row("Medium (60-79%)", str(med_conf), f"{(med_conf / total) * 100:.1f}%")
        table.add_row("Low (0-59%)", str(low_conf), f"{(low_conf / total) * 100:.1f}%")

        self.console.print(table)

    def _show_field_breakdown(self, brush_matches: List[Dict]) -> None:
        """Show breakdown of brush field components."""
        brands = defaultdict(int)
        handle_makers = defaultdict(int)
        fibers = defaultdict(int)
        knot_sizes = defaultdict(int)

        for match in brush_matches:
            matched = match.get("matched", {})
            brands[matched.get("brand", "Unknown")] += 1
            handle_makers[matched.get("handle_maker", "Unknown")] += 1
            fibers[matched.get("fiber", "Unknown")] += 1
            knot_sizes[matched.get("knot_size_mm", "Unknown")] += 1

        # Show top brands
        table = Table(title="Top Brush Brands")
        table.add_column("Brand", style="cyan")
        table.add_column("Count", justify="right")

        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
            table.add_row(brand, str(count))

        self.console.print(table)

        # Show handle makers
        table = Table(title="Brush Handle Makers")
        table.add_column("Handle Maker", style="cyan")
        table.add_column("Count", justify="right")

        for maker, count in sorted(handle_makers.items(), key=lambda x: x[1], reverse=True)[:10]:
            table.add_row(maker, str(count))

        self.console.print(table)

        # Show fibers
        table = Table(title="Brush Fiber Distribution")
        table.add_column("Fiber", style="cyan")
        table.add_column("Count", justify="right")

        for fiber, count in sorted(fibers.items(), key=lambda x: x[1], reverse=True):
            table.add_row(fiber, str(count))

        self.console.print(table)

        # Show knot sizes
        table = Table(title="Brush Knot Size Distribution")
        table.add_column("Knot Size (mm)", style="cyan")
        table.add_column("Count", justify="right")

        for size, count in sorted(knot_sizes.items(), key=lambda x: x[1], reverse=True):
            table.add_row(str(size), str(count))

        self.console.print(table)

    def _show_potential_mismatches(self, all_data: List[Dict], limit: int) -> None:
        """Show potential brush mismatches."""
        mismatches = []

        for record in all_data:
            brush = record.get("brush", {})
            if isinstance(brush, dict) and brush.get("matched"):
                confidence = brush.get("confidence", 0)
                if confidence < 70:
                    original = brush.get("original", "")
                    matched = brush.get("matched", {})
                    match_type = brush.get("match_type", "")

                    matched_name = f"{matched.get('brand', '')} {matched.get('model', '')}".strip()
                    mismatches.append(
                        {
                            "original": original,
                            "matched": matched_name,
                            "match_type": match_type,
                            "confidence": confidence,
                            "source": record.get("_source_file", ""),
                        }
                    )

        if not mismatches:
            self.console.print("[green]No low-confidence brush matches found[/green]")
            return

        # Sort by confidence (lowest first) and take top examples
        mismatches.sort(key=lambda x: x["confidence"])
        mismatches = mismatches[:limit]

        table = Table(title=f"Potential Brush Mismatches (Top {len(mismatches)})")
        table.add_column("Original", style="cyan", width=50)
        table.add_column("Matched", style="yellow", width=30)
        table.add_column("Type", width=12)
        table.add_column("Conf%", justify="right", width=6)
        table.add_column("Source", width=12)

        for mismatch in mismatches:
            table.add_row(
                mismatch["original"],
                mismatch["matched"],
                mismatch["match_type"],
                f"{mismatch['confidence']:.0f}",
                mismatch["source"],
            )

        self.console.print(table)


def get_parser() -> BaseCLIParser:
    """Get CLI parser for brush analysis tool."""
    analyzer = BrushAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the brush analysis tool."""
    analyzer = BrushAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the brush analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
