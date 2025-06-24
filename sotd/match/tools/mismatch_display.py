#!/usr/bin/env python3
"""Display and reporting utilities for mismatch analysis."""

from typing import Dict, List

from rich.console import Console
from rich.table import Table


class MismatchDisplay:
    """Handles display and reporting of mismatch analysis results."""

    def __init__(self, console: Console):
        self.console = console

    def _get_table(self, title: str = ""):
        """Lazy load Rich Table to reduce startup time."""
        return Table(title=title)

    def display_mismatches(self, mismatches: Dict[str, List[Dict]], field: str, args) -> None:
        """Display mismatches in a formatted table."""
        # Group duplicate mismatches
        grouped_mismatches = self._group_duplicate_mismatches(mismatches, field)

        if not grouped_mismatches:
            self.console.print("[green]No mismatches found![/green]")
            return

        # Create table
        table = self._get_table(f"Mismatches for {field.capitalize()} ({args.month})")
        table.add_column("Original", style="cyan")
        table.add_column("Matched", style="magenta")
        table.add_column("Reasons", style="yellow")
        table.add_column("Count", style="red")

        # Add rows (limit to args.limit)
        for i, mismatch in enumerate(grouped_mismatches[: args.limit]):
            field_data = mismatch["field_data"]
            original = field_data.get("original", "")
            matched = field_data.get("matched", {})

            # Format matched text
            if field == "soap":
                maker = matched.get("maker", "")
                scent = matched.get("scent", "")
                matched_text = f"{maker} {scent}".strip()
            else:
                brand = matched.get("brand", "")
                model = matched.get("model", "")
                matched_text = f"{brand} {model}".strip()

            # Format reasons
            reasons = mismatch["reasons"]
            reason_text = "; ".join(reasons[:3])  # Show first 3 reasons
            if len(reasons) > 3:
                reason_text += f" (+{len(reasons) - 3} more)"

            table.add_row(
                original[:50] + ("..." if len(original) > 50 else ""),
                matched_text[:50] + ("..." if len(matched_text) > 50 else ""),
                reason_text,
                str(len(reasons)),
            )

        self.console.print(table)
        self._display_summary(mismatches, len(grouped_mismatches), args)

    def display_all_matches(
        self, data: Dict, field: str, mismatches: Dict[str, List[Dict]], args
    ) -> None:
        """Display all matches with mismatch indicators."""
        records = data.get("data", [])
        if not records:
            self.console.print("[yellow]No records found[/yellow]")
            return

        # Create mismatch lookup
        mismatch_lookup = {}
        for mismatch_type, mismatch_list in mismatches.items():
            for mismatch in mismatch_list:
                match_key = mismatch["match_key"]
                if match_key not in mismatch_lookup:
                    mismatch_lookup[match_key] = []
                mismatch_lookup[match_key].extend(mismatch["reason"])

        # Create table
        table = self._get_table(f"All {field.capitalize()} Matches ({args.month})")
        table.add_column("Original", style="cyan")
        table.add_column("Matched", style="magenta")
        table.add_column("Type", style="blue")
        table.add_column("Issues", style="red")

        # Track displayed matches for potential marking as correct
        displayed_matches = []

        # Add rows
        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue

            original = field_data.get("original", "")
            matched = field_data.get("matched", {})
            match_type = field_data.get("match_type", "")

            if not original or not matched:
                continue

            # Format matched text
            if field == "soap":
                maker = matched.get("maker", "")
                scent = matched.get("scent", "")
                matched_text = f"{maker} {scent}".strip()
            else:
                brand = matched.get("brand", "")
                model = matched.get("model", "")
                matched_text = f"{brand} {model}".strip()

            # Check for issues
            match_key = f"{field}:{original.lower().strip()}|{matched_text.lower().strip()}"
            issues = mismatch_lookup.get(match_key, [])

            if issues:
                issue_text = "; ".join(issues[:2])  # Show first 2 issues
                if len(issues) > 2:
                    issue_text += f" (+{len(issues) - 2} more)"
                issue_style = "red"
            else:
                issue_text = "✓"
                issue_style = "green"

            table.add_row(
                original[:50] + ("..." if len(original) > 50 else ""),
                matched_text[:50] + ("..." if len(matched_text) > 50 else ""),
                match_type,
                issue_text,
                style=issue_style,
            )

            # Track for potential marking
            displayed_matches.append(
                {
                    "original": original,
                    "matched": matched,
                    "match_key": match_key,
                    "has_issues": bool(issues),
                }
            )

        self.console.print(table)

        # Show summary
        total_matches = len(displayed_matches)
        matches_with_issues = sum(1 for m in displayed_matches if m["has_issues"])
        self.console.print(
            "\n[bold]Summary:[/bold] {total_matches} total matches, "
            "{matches_with_issues} with issues".format(
                total_matches=total_matches, matches_with_issues=matches_with_issues
            )
        )

        # Mark as correct if requested
        if args.mark_correct:
            self._mark_displayed_matches_as_correct(displayed_matches, field)

    def _count_filtered_matches(self, data: List[Dict], field: str) -> int:
        """Count matches that have the specified field."""
        count = 0
        for record in data:
            field_data = record.get(field)
            if isinstance(field_data, dict):
                original = field_data.get("original", "")
                matched = field_data.get("matched", {})
                if original and matched:
                    count += 1
        return count

    def _display_summary(
        self, mismatches: Dict[str, List[Dict]], filtered_count: int, args
    ) -> None:
        """Display summary of mismatch analysis."""
        total_mismatches = sum(len(mismatch_list) for mismatch_list in mismatches.values())

        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  • Total mismatches found: [red]{total_mismatches}[/red]")
        self.console.print(f"  • Showing first: [yellow]{args.limit}[/yellow]")

        if total_mismatches > args.limit:
            self.console.print(f"  • Remaining: [yellow]{total_mismatches - args.limit}[/yellow]")

    def _group_duplicate_mismatches(
        self, mismatches: Dict[str, List[Dict]], field: str
    ) -> List[Dict]:
        """Group duplicate mismatches by their match key."""
        grouped = {}

        for mismatch_type, mismatch_list in mismatches.items():
            for mismatch in mismatch_list:
                match_key = mismatch["match_key"]
                if match_key not in grouped:
                    grouped[match_key] = {
                        "record": mismatch["record"],
                        "field_data": mismatch["field_data"],
                        "reasons": [],
                        "match_key": match_key,
                    }
                grouped[match_key]["reasons"].append(mismatch["reason"])

        # Convert to list and sort by number of reasons (most problematic first)
        result = list(grouped.values())
        result.sort(key=lambda x: len(x["reasons"]), reverse=True)

        return result

    def _mark_displayed_matches_as_correct(
        self, displayed_matches: List[Dict], field: str = "razor"
    ) -> None:
        """Mark displayed matches as correct."""
        # This would need to be implemented with the correct matches manager
        # For now, just show a message
        self.console.print(
            "\n[yellow]Note: Mark as correct functionality would be implemented here[/yellow]"
        )
        self.console.print(
            f"[yellow]Would mark {len(displayed_matches)} matches as correct for {field}[/yellow]"
        )
