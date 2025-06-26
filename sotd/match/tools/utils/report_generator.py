#!/usr/bin/env python3
"""Report generation functionality for analysis tools."""

from collections import Counter
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sotd.match.tools.analyzers.confidence_analyzer import analyze_match_confidence


def generate_summary_panel(
    total_matches: int,
    match_type_counts: Counter[str],
    avg_confidence: float,
    potential_mismatches: int,
    field: str = "brush",
) -> Panel:
    """Generate a summary panel with key statistics."""
    summary_content = f"""
[bold]Total Matches:[/bold] {total_matches}
[bold]Match Type Distribution:[/bold]
"""
    for match_type, count in match_type_counts.most_common():
        percentage = (count / total_matches) * 100
        summary_content += f"  • {match_type}: {count} ({percentage:.1f}%)\n"

    summary_content += f"\n[bold]Average Confidence Score:[/bold] {avg_confidence:.1f}/100"
    mismatch_percentage = potential_mismatches / total_matches * 100
    summary_content += (
        f"\n[bold]Potential Mismatches:[/bold] {potential_mismatches} ({mismatch_percentage:.1f}%)"
    )

    title = f"{field.capitalize()} Matching Summary"
    return Panel(summary_content, title=title, border_style="blue")


def generate_confidence_analysis_panel(confidence_scores: List[float], total_matches: int) -> Panel:
    """Generate a panel showing confidence score distribution."""
    high_conf = sum(1 for score in confidence_scores if score >= 80)
    med_conf = sum(1 for score in confidence_scores if 60 <= score < 80)
    low_conf = sum(1 for score in confidence_scores if score < 60)

    quality_content = f"""
[bold]Confidence Distribution:[/bold]
  • High Confidence (80-100%): {high_conf} ({high_conf / total_matches * 100:.1f}%)
  • Medium Confidence (60-79%): {med_conf} ({med_conf / total_matches * 100:.1f}%)
  • Low Confidence (0-59%): {low_conf} ({low_conf / total_matches * 100:.1f}%)
"""
    return Panel(quality_content, title="Confidence Analysis", border_style="green")


def generate_pattern_effectiveness_table(pattern_stats: Dict[str, Dict[str, Any]]) -> Table:
    """Generate a table showing pattern effectiveness statistics."""
    table = Table(title="Pattern Effectiveness Analysis")
    table.add_column("Pattern", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Exact%", justify="right")
    table.add_column("Conf%", justify="right")
    table.add_column("Effect.", style="bold")

    for pattern, stats in sorted(
        pattern_stats.items(), key=lambda x: x[1]["combined_score"], reverse=True
    ):
        exact_rate = stats["exact_rate"] * 100 if "exact_rate" in stats else 0
        avg_conf = stats["avg_confidence"] if "avg_confidence" in stats else 0
        effectiveness = stats.get("effectiveness", "low")

        effect_style = {
            "high": "green",
            "medium": "yellow",
            "low": "red",
        }.get(effectiveness, "")

        table.add_row(
            pattern,
            str(stats["total"]),
            f"{exact_rate:.1f}%",
            f"{avg_conf:.1f}",
            effectiveness,
            style=effect_style,
        )

    return table


def generate_opportunities_table(opportunities: List[Dict[str, Any]]) -> Table:
    """Generate a table showing improvement opportunities."""
    table = Table(title="Improvement Opportunities")
    table.add_column("Pattern", style="cyan")
    table.add_column("Issue", style="yellow")
    table.add_column("Count", justify="right")
    table.add_column("Impact", style="bold")

    for opp in sorted(opportunities, key=lambda x: x["impact_score"], reverse=True):
        impact_style = {
            "high": "red",
            "medium": "yellow",
            "low": "green",
        }.get(opp["impact"], "")

        table.add_row(
            opp["pattern"],
            opp["issue"],
            str(opp["count"]),
            opp["impact"],
            style=impact_style,
        )

    return table


def show_pattern_examples(
    data: List[Dict[str, Any]], pattern: str, field: str = "brush", limit: int = 15
) -> None:
    """Show examples of matches for a specific pattern."""
    console = Console()
    examples = []

    for record in data:
        field_data = record.get(field, {})
        if (
            isinstance(field_data, dict)
            and field_data.get("matched")
            and field_data.get("pattern") == pattern
        ):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            confidence = analyze_match_confidence(original, brand, model, match_type)
            examples.append(
                {
                    "original": original,
                    "matched": f"{brand} {model}",
                    "match_type": match_type,
                    "confidence": confidence["score"],
                }
            )

    if not examples:
        console.print(f"[yellow]No examples found for pattern: {pattern}[/yellow]")
        return

    table = Table(title=f"Examples for Pattern: {pattern}")
    table.add_column("Original", style="cyan", width=60)
    table.add_column("Matched", style="yellow", width=25)
    table.add_column("Type", width=12)
    table.add_column("Conf%", justify="right", width=6)

    # Sort by confidence (highest first) and take top examples
    for example in sorted(examples, key=lambda x: x["confidence"], reverse=True)[:limit]:
        table.add_row(
            example["original"],
            example["matched"],
            example["match_type"],
            f"{example['confidence']:.0f}",
        )

    console.print(table)


def show_potential_mismatches(
    data: List[Dict[str, Any]], field: str = "brush", limit: int = 20
) -> None:
    """Show potential mismatches for manual review."""
    console = Console()
    mismatches = []

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            confidence = analyze_match_confidence(original, brand, model, match_type)

            if confidence["score"] < 70:
                mismatches.append(
                    {
                        "original": original,
                        "matched": f"{brand} {model}",
                        "match_type": match_type,
                        "confidence": confidence["score"],
                        "issues": confidence["issues"],
                        "warnings": confidence["warnings"],
                    }
                )

    # Sort by confidence (lowest first)
    mismatches.sort(key=lambda x: x["confidence"])

    if not mismatches:
        console.print("[green]No potential mismatches found![/green]")
        return

    table = Table(title=f"Potential {field.capitalize()} Mismatches (Confidence < 70%)")
    table.add_column("Original", style="cyan", width=60)
    table.add_column("Matched", style="yellow", width=25)
    table.add_column("Type", width=12)
    table.add_column("Conf%", justify="right", width=6)
    table.add_column("Issues", style="red")

    for mismatch in mismatches[:limit]:
        issues = ", ".join(mismatch["issues"] + mismatch["warnings"])
        table.add_row(
            mismatch["original"],
            mismatch["matched"],
            mismatch["match_type"],
            f"{mismatch['confidence']:.0f}",
            issues,
        )

    console.print(table)
