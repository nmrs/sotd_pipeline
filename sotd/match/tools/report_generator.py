#!/usr/bin/env python3
"""Report generation for product matching validation."""

from collections import Counter
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sotd.match.tools.confidence_analyzer import analyze_match_confidence


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

            if confidence["is_potential_mismatch"]:
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
    table.add_column("Issues/Warnings", style="red", width=40)

    for mismatch in mismatches[:limit]:
        issues_text = "; ".join(mismatch["issues"] + mismatch["warnings"])
        if len(issues_text) > 38:
            issues_text = issues_text[:35] + "..."

        confidence_style = (
            "red"
            if mismatch["confidence"] < 50
            else "yellow" if mismatch["confidence"] < 60 else "white"
        )

        table.add_row(
            mismatch["original"],  # Show full original text without truncation
            mismatch["matched"],
            mismatch["match_type"],
            f"[{confidence_style}]{mismatch['confidence']:.0f}[/{confidence_style}]",
            issues_text,
        )

    console.print(table)

    if len(mismatches) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(mismatches)} potential mismatches[/dim]")


def show_pattern_examples(
    data: List[Dict[str, Any]], pattern_name: str, field: str = "brush", limit: int = 10
) -> None:
    """Show specific examples of matches for a given pattern."""
    console = Console()
    examples = []

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            # Check if this matches the pattern we're looking for
            matched_pattern = f"{brand} {model}".strip()
            if pattern_name.lower() in matched_pattern.lower():
                confidence = analyze_match_confidence(original, brand, model, match_type)
                examples.append(
                    {
                        "original": original,
                        "matched": matched_pattern,
                        "match_type": match_type,
                        "confidence": confidence["score"],
                        "issues": confidence["issues"],
                        "warnings": confidence["warnings"],
                    }
                )

    if not examples:
        console.print(f"[yellow]No examples found for pattern '{pattern_name}'[/yellow]")
        return

    # Sort by confidence (lowest first)
    examples.sort(key=lambda x: x["confidence"])

    table = Table(title=f"Examples for '{pattern_name}' Pattern")
    table.add_column("Original", style="cyan", width=70)
    table.add_column("Matched", style="yellow", width=20)
    table.add_column("Type", width=10)
    table.add_column("Conf%", justify="right", width=6)
    table.add_column("Issues/Warnings", style="red", width=35)

    for example in examples[:limit]:
        issues_text = "; ".join(example["issues"] + example["warnings"])
        if len(issues_text) > 33:
            issues_text = issues_text[:30] + "..."

        confidence_style = (
            "red"
            if example["confidence"] < 50
            else "yellow" if example["confidence"] < 60 else "white"
        )

        table.add_row(
            example["original"],  # Show full original text without truncation
            example["matched"],
            example["match_type"],
            f"[{confidence_style}]{example['confidence']:.0f}[/{confidence_style}]",
            issues_text,
        )

    console.print(table)

    if len(examples) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(examples)} examples[/dim]")


def generate_summary_panel(
    total_matches: int,
    match_type_counts: Counter[str],
    avg_confidence: float,
    potential_mismatches: int,
    field: str,
) -> Panel:
    """Generate a summary panel for the analysis."""
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


def generate_pattern_effectiveness_table(pattern_stats: Dict[str, Dict[str, Any]]) -> Table:
    """Generate a table showing pattern effectiveness."""
    pattern_table = Table(title="Pattern Effectiveness Analysis")
    pattern_table.add_column("Pattern", style="cyan")
    pattern_table.add_column("Total Uses", justify="right")
    pattern_table.add_column("Exact Rate", justify="right")
    pattern_table.add_column("Avg Conf%", justify="right")
    pattern_table.add_column("Effectiveness", style="bold")

    sorted_patterns = sorted(
        pattern_stats.items(), key=lambda x: x[1].get("combined_score", 0), reverse=True
    )

    for pattern, stats in sorted_patterns:
        if stats["total"] >= 2:  # Only show patterns used multiple times
            effectiveness_style = (
                "green"
                if stats["effectiveness"] == "high"
                else "yellow" if stats["effectiveness"] == "medium" else "red"
            )

            pattern_table.add_row(
                pattern[:40] + ("..." if len(pattern) > 40 else ""),
                str(stats["total"]),
                f"{stats['exact_rate']:.1%}",
                f"{stats['avg_confidence']:.0f}%",
                f"[{effectiveness_style}]{stats['effectiveness']}[/{effectiveness_style}]",
            )

    return pattern_table


def generate_opportunities_table(opportunities: List[Dict[str, Any]]) -> Table:
    """Generate a table showing improvement opportunities."""
    opp_table = Table(title="Improvement Opportunities")
    opp_table.add_column("Priority", width=8)
    opp_table.add_column("Issue", style="cyan", width=50)
    opp_table.add_column("Count", justify="right", width=6)
    opp_table.add_column("Suggestion", style="yellow", width=50)

    for opp in opportunities[:15]:  # Show top 15
        priority_style = "red" if opp.get("priority") == "high" else "yellow"
        opp_table.add_row(
            f"[{priority_style}]{opp.get('priority', 'medium').upper()}[/{priority_style}]",
            opp["description"],
            str(opp["count"]),
            opp["suggestion"],
        )

    return opp_table


def generate_confidence_analysis_panel(confidence_scores: List[float], total_matches: int) -> Panel:
    """Generate a panel showing confidence distribution."""
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
