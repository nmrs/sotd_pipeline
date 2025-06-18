#!/usr/bin/env python3
"""Enhanced analysis tool for validating brush matching performance."""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sotd.cli_utils.date_span import month_span


def analyze_match_confidence(
    original: str, matched_brand: str, matched_model: str, match_type: str
) -> Dict[str, Any]:
    """Analyze the confidence of a match and detect potential mismatches."""
    confidence_score = 100
    issues = []
    warnings = []

    original_lower = original.lower()

    # Basic confidence based on match type
    if match_type == "exact":
        confidence_score = 95
    elif match_type == "brand_default":
        confidence_score = 60  # Lower confidence for generic matches
    else:
        confidence_score = 40

    # Check if matched brand appears in original text
    brand_in_original = matched_brand.lower() in original_lower
    if not brand_in_original and match_type != "brand_default":
        confidence_score -= 20
        issues.append("matched_brand_not_in_original")

    # Check for competing brand names in original
    competing_brands = detect_competing_brands(original, matched_brand)
    if competing_brands:
        confidence_score -= 30
        warnings.append(f"competing_brands_found: {', '.join(competing_brands)}")

    # Check for knot maker vs handle maker confusion
    knot_maker_issues = detect_knot_maker_confusion(original, matched_brand)
    if knot_maker_issues:
        confidence_score -= 25
        warnings.append(f"possible_knot_maker_confusion: {knot_maker_issues}")

    # Check for generic model fallbacks
    if matched_model in ["Synthetic", "Badger", "Boar"] and match_type == "brand_default":
        confidence_score -= 10
        issues.append("generic_model_fallback")

    # Check for specific model in original but generic match
    if match_type == "brand_default" and has_specific_model_info(original):
        confidence_score -= 15
        warnings.append("specific_model_info_ignored")

    # Boost confidence for well-established patterns
    if match_type == "exact" and brand_in_original:
        confidence_score = min(100, confidence_score + 10)

    confidence_level = (
        "high" if confidence_score >= 80 else "medium" if confidence_score >= 60 else "low"
    )

    return {
        "score": max(0, confidence_score),
        "level": confidence_level,
        "issues": issues,
        "warnings": warnings,
        "is_potential_mismatch": confidence_score < 70,
    }


def detect_competing_brands(original: str, matched_brand: str) -> List[str]:
    """Detect if there are other brand names in the original that might be more relevant."""
    # Common brush/knot brands that might be confused
    brush_brands = [
        "maggard",
        "declaration",
        "chisel",
        "hound",
        "ap shave",
        "zenith",
        "omega",
        "semogue",
        "yaqi",
        "oumo",
        "muhle",
        "simpson",
        "stirling",
        "dogwood",
        "grizzly bay",
        "turn.n.shave",
        "wolf whiskers",
        "summer break",
        "elite",
        "farvour",
        "rubberset",
        "ever.ready",
        "parker",
        "kent",
        "vulfix",
    ]

    original_lower = original.lower()
    matched_lower = matched_brand.lower()
    competing = []

    for brand in brush_brands:
        brand_clean = brand.replace(".", "").replace(" ", "")
        original_clean = original_lower.replace(" ", "").replace("-", "").replace(".", "")
        matched_clean = matched_lower.replace(" ", "").replace("-", "").replace(".", "")
        if brand_clean in original_clean:
            if brand_clean != matched_clean:
                competing.append(brand.title())

    return competing


def detect_knot_maker_confusion(original: str, matched_brand: str) -> str:
    """Detect if we might have confused knot maker with handle maker."""
    original_lower = original.lower()

    # Common patterns indicating knot maker
    knot_patterns = [
        r"w/\s*(\w+(?:\s+\w+)?)\s+(?:knot|shd|badger|boar|synthetic)",
        r"with\s+(\w+(?:\s+\w+)?)\s+(?:knot|shd|badger|boar|synthetic)",
        r"(\w+(?:\s+\w+)?)\s+(?:knot|shd)\s+(?:badger|boar|synthetic)",
        r"(\w+)\s+(?:26mm|24mm|28mm|30mm)\s+(?:knot|shd|badger|boar|synthetic)",
    ]

    for pattern in knot_patterns:
        matches = re.findall(pattern, original_lower, re.IGNORECASE)
        for match in matches:
            potential_knot_maker = match.strip()
            if (
                potential_knot_maker
                and potential_knot_maker != matched_brand.lower()
                and len(potential_knot_maker) > 2
            ):
                return potential_knot_maker.title()

    return ""


def has_specific_model_info(original: str) -> bool:
    """Check if original contains specific model information that might be ignored."""
    original_lower = original.lower()

    # Look for specific model indicators
    model_indicators = [
        r"\b(?:tuxedo|cashmere|synbad|g5[abc]|pure\s*bliss|gelousy|titanium)\b",
        r"\b(?:chubby|trafalgar|manchurian|silvertip|finest)\b",
        r"\b(?:v\d+|b\d+|t\d+)\b",  # Version/batch numbers
        r"\b\d{4,5}\b",  # Model numbers like 10048, 20102
    ]

    for pattern in model_indicators:
        if re.search(pattern, original_lower):
            return True

    return False


def get_pattern_effectiveness(
    data: List[Dict[str, Any]], field: str = "brush"
) -> Dict[str, Dict[str, Any]]:
    """Analyze which patterns are most/least effective."""
    pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "exact": 0, "brand_default": 0, "confidence_scores": []}
    )

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            pattern = field_data.get("pattern", "unknown")
            match_type = field_data.get("match_type", "unknown")

            original = field_data.get("original", "")
            matched = field_data["matched"]
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            confidence = analyze_match_confidence(original, brand, model, match_type)

            pattern_stats[pattern]["total"] += 1
            pattern_stats[pattern][match_type] += 1
            pattern_stats[pattern]["confidence_scores"].append(confidence["score"])

    # Calculate effectiveness scores
    for pattern, stats in pattern_stats.items():
        if stats["total"] > 0:
            stats["exact_rate"] = stats["exact"] / stats["total"]
            stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(
                stats["confidence_scores"]
            )

            # Combined effectiveness based on exact rate and confidence
            combined_score = (stats["exact_rate"] * 0.6) + (stats["avg_confidence"] / 100 * 0.4)

            effectiveness = (
                "high" if combined_score >= 0.8 else "medium" if combined_score >= 0.6 else "low"
            )
            stats["effectiveness"] = effectiveness
            stats["combined_score"] = combined_score

    return dict(pattern_stats)


def identify_improvement_opportunities(
    data: List[Dict[str, Any]], field: str = "brush"
) -> List[Dict[str, Any]]:
    """Identify specific opportunities for improving matches."""
    opportunities = []
    brand_model_counts = defaultdict(int)
    low_confidence_patterns = defaultdict(list)

    for record in data:
        field_data = record.get(field, {})
        if isinstance(field_data, dict) and field_data.get("matched"):
            original = field_data.get("original", "")
            matched = field_data["matched"]
            match_type = field_data.get("match_type", "")
            brand = matched.get("brand", "")
            model = matched.get("model", "")

            # Analyze confidence
            confidence = analyze_match_confidence(original, brand, model, match_type)

            # Track low confidence matches
            if confidence["is_potential_mismatch"]:
                low_confidence_patterns[f"{brand} {model}"].append(
                    {"original": original, "confidence": confidence, "match_type": match_type}
                )

            # Count brand+model combinations that fall back to brand_default
            if match_type == "brand_default":
                key = f"{brand} {model}".strip()
                brand_model_counts[key] += 1

    # Find high-frequency brand_default matches
    for combo, count in brand_model_counts.items():
        if count >= 3:
            opportunities.append(
                {
                    "type": "frequent_brand_default",
                    "description": f"{combo} appears {count} times as brand_default",
                    "suggestion": f"Consider adding specific pattern for '{combo}'",
                    "count": count,
                    "priority": "high" if count >= 10 else "medium",
                }
            )

    # Find patterns with low confidence
    for pattern, matches in low_confidence_patterns.items():
        if len(matches) >= 2:
            avg_confidence = sum(m["confidence"]["score"] for m in matches) / len(matches)
            sample_warnings = []
            for match in matches[:2]:  # Show first 2 examples
                sample_warnings.extend(match["confidence"]["warnings"])

            opportunities.append(
                {
                    "type": "low_confidence_pattern",
                    "description": (
                        f"{pattern} has {len(matches)} low-confidence matches "
                        f"(avg: {avg_confidence:.1f}%)"
                    ),
                    "suggestion": (f"Review pattern accuracy: {'; '.join(set(sample_warnings))}"),
                    "count": len(matches),
                    "priority": "high" if avg_confidence < 50 else "medium",
                }
            )

    return sorted(
        opportunities, key=lambda x: (x.get("priority") == "high", x["count"]), reverse=True
    )


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

    title = f"{args.field.capitalize()} Matching Summary"
    console.print(Panel(summary_content, title=title, border_style="blue"))

    # Show potential mismatches
    if args.show_mismatches:
        console.print()
        show_potential_mismatches(all_data, args.field, args.mismatch_limit)

    # Pattern effectiveness analysis
    if args.show_patterns:
        pattern_stats = get_pattern_effectiveness(all_data, args.field)

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

        console.print(pattern_table)

    # Improvement opportunities
    if args.show_opportunities:
        opportunities = identify_improvement_opportunities(all_data, args.field)

        if opportunities:
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

            console.print(opp_table)
        else:
            console.print("[green]No improvement opportunities identified![/green]")

    # Quality distribution
    if args.show_details:
        high_conf = sum(1 for score in confidence_scores if score >= 80)
        med_conf = sum(1 for score in confidence_scores if 60 <= score < 80)
        low_conf = sum(1 for score in confidence_scores if score < 60)

        quality_content = f"""
[bold]Confidence Distribution:[/bold]
  • High Confidence (80-100%): {high_conf} ({high_conf / total_matches * 100:.1f}%)
  • Medium Confidence (60-79%): {med_conf} ({med_conf / total_matches * 100:.1f}%)
  • Low Confidence (0-59%): {low_conf} ({low_conf / total_matches * 100:.1f}%)
"""
        console.print(Panel(quality_content, title="Confidence Analysis", border_style="green"))


if __name__ == "__main__":
    main()
