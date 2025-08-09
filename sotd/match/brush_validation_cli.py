"""Brush CLI validation interface for validating brush matching results."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from sotd.match.brush_user_actions import BrushUserActionsManager
from sotd.utils.file_io import load_json_data


class BrushValidationCLI:
    """CLI interface for validating brush matching results."""

    def __init__(self, data_path: Optional[Path] = None):
        """Initialize CLI with data path and brush system integration."""
        if data_path is None:
            data_path = Path("data")

        self.data_path = Path(data_path)
        self.user_actions_manager = BrushUserActionsManager(base_path=self.data_path / "learning")

        # Initialize brush matcher entry point for system integration
        from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint

        self.brush_entry_point = BrushMatcherEntryPoint()

    def load_month_data(self, month: str, system: str) -> List[Dict[str, Any]]:
        """Load monthly brush data for validation.

        Args:
            month: Month in YYYY-MM format
            system: 'legacy', 'scoring', or 'both'

        Returns:
            List of brush entries with system metadata
        """
        if system == "legacy":
            file_path = self.data_path / "matched" / f"{month}.json"
        elif system == "scoring":
            file_path = self.data_path / "matched_new" / f"{month}.json"
        else:
            raise ValueError(f"Invalid system for single load: {system}")

        try:
            data = load_json_data(file_path)
            brush_data = data.get("brush", [])

            # Normalize data structure for validation interface
            entries = []
            for brush_entry in brush_data:
                if system == "legacy":
                    entry = {
                        "input_text": brush_entry.get("name", ""),
                        "system_used": "legacy",
                        "matched": brush_entry.get("matched"),
                        "match_type": brush_entry.get("match_type"),
                        "all_strategies": [],  # Legacy system doesn't track all strategies
                    }
                else:  # scoring system
                    entry = {
                        "input_text": brush_entry.get("name", ""),
                        "system_used": "scoring",
                        "best_result": brush_entry.get("best_result"),
                        "all_strategies": brush_entry.get("all_strategies", []),
                    }

                entries.append(entry)

            return entries

        except FileNotFoundError:
            print(f"Warning: No data file found for {month} ({system} system)")
            return []
        except Exception as e:
            print(f"Error loading data for {month} ({system}): {e}")
            return []

    def sort_entries(
        self, entries: List[Dict[str, Any]], month: str, sort_by: str
    ) -> List[Dict[str, Any]]:
        """Sort entries based on validation criteria.

        Args:
            entries: List of brush entries
            month: Month for validation status lookup
            sort_by: 'unvalidated', 'validated', or 'ambiguity'

        Returns:
            Sorted list of entries
        """
        if sort_by == "unvalidated":
            return self._sort_by_validation_status(entries, month, unvalidated_first=True)
        elif sort_by == "validated":
            return self._sort_by_validation_status(entries, month, unvalidated_first=False)
        elif sort_by == "ambiguity":
            return self._sort_by_ambiguity(entries)
        else:
            raise ValueError(f"Invalid sort_by option: {sort_by}")

    def _sort_by_validation_status(
        self, entries: List[Dict[str, Any]], month: str, unvalidated_first: bool
    ) -> List[Dict[str, Any]]:
        """Sort entries by validation status."""
        # Get existing user actions for this month
        existing_actions = self.user_actions_manager.get_monthly_actions(month)
        validated_texts = {action.input_text for action in existing_actions}

        # Separate validated and unvalidated entries
        validated = []
        unvalidated = []

        for entry in entries:
            if entry["input_text"] in validated_texts:
                validated.append(entry)
            else:
                unvalidated.append(entry)

        if unvalidated_first:
            return unvalidated + validated
        else:
            return validated + unvalidated

    def _sort_by_ambiguity(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort entries by ambiguity (smallest score difference first)."""

        def get_ambiguity_score(entry: Dict[str, Any]) -> float:
            """Calculate ambiguity score (lower = more ambiguous)."""
            if entry["system_used"] != "scoring":
                return float("inf")  # Legacy entries have no ambiguity score

            strategies = entry.get("all_strategies", [])
            if len(strategies) < 2:
                return float("inf")  # No ambiguity with < 2 strategies

            # Get top 2 scores
            scores = [s.get("score", 0) for s in strategies if s.get("score") is not None]
            scores.sort(reverse=True)

            if len(scores) < 2:
                return float("inf")

            return scores[0] - scores[1]  # Difference between top 2 scores

        return sorted(entries, key=get_ambiguity_score)

    def display_entry(self, entry: Dict[str, Any], index: int, total: int) -> None:
        """Display entry information for validation."""
        print(f"\n{'=' * 60}")
        print(f"Entry {index}/{total}")
        print(f"{'=' * 60}")
        print(f"Input: {entry['input_text']}")
        print(f"System: {entry['system_used']}")

        if entry["system_used"] == "legacy":
            matched = entry.get("matched")
            match_type = entry.get("match_type", "unknown")
            print(f"Match Type: {match_type}")

            if matched:
                print(f"Result: {matched.get('brand', 'N/A')} {matched.get('model', 'N/A')}")
                if matched.get("handle"):
                    print(
                        f"  Handle: {matched['handle'].get('brand', 'N/A')} {matched['handle'].get('model', 'N/A')}"
                    )
                if matched.get("knot"):
                    print(
                        f"  Knot: {matched['knot'].get('brand', 'N/A')} {matched['knot'].get('model', 'N/A')}"
                    )
            else:
                print("Result: No match")

        else:  # scoring system
            best_result = entry.get("best_result")
            if best_result:
                print(f"Best Strategy: {best_result.get('strategy', 'N/A')}")
                print(f"Score: {best_result.get('score', 'N/A')}")

                result = best_result.get("result", {})
                if result:
                    print(f"Result: {result.get('brand', 'N/A')} {result.get('model', 'N/A')}")
                    if result.get("handle"):
                        print(
                            f"  Handle: {result['handle'].get('brand', 'N/A')} {result['handle'].get('model', 'N/A')}"
                        )
                    if result.get("knot"):
                        print(
                            f"  Knot: {result['knot'].get('brand', 'N/A')} {result['knot'].get('model', 'N/A')}"
                        )

                # Show all strategies for context
                all_strategies = entry.get("all_strategies", [])
                if len(all_strategies) > 1:
                    print("\nAll Strategies:")
                    for i, strategy in enumerate(all_strategies):
                        score = strategy.get("score", "N/A")
                        name = strategy.get("strategy", "unknown")
                        print(f"  {i + 1}. {name} (Score: {score})")
            else:
                print("Result: No match")

    def get_user_choice(self, entry: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Get user validation choice.

        Returns:
            Tuple of (action, choice) where action is 'validate'/'override'/'skip'/'quit'
            and choice is the selected result dict
        """
        while True:
            print("\nOptions:")
            print("  (v) Validate current result")
            print("  (o) Override with different strategy")
            print("  (s) Skip this entry")
            print("  (q) Quit validation")

            choice = input("Your choice [v/o/s/q]: ").lower().strip()

            if choice == "v":
                # Validate current best result
                if entry["system_used"] == "legacy":
                    result_dict = {
                        "strategy": "legacy",
                        "score": None,
                        "result": entry.get("matched", {}),
                    }
                else:
                    result_dict = entry.get("best_result", {})
                return "validate", result_dict

            elif choice == "o":
                # Override with different strategy
                if entry["system_used"] == "legacy":
                    print("Override not available for legacy system")
                    continue

                strategies = entry.get("all_strategies", [])
                if not strategies:
                    print("No alternative strategies available")
                    continue

                print("\nAvailable strategies:")
                for i, strategy in enumerate(strategies):
                    score = strategy.get("score", "N/A")
                    name = strategy.get("strategy", "unknown")
                    print(f"  {i + 1}. {name} (Score: {score})")

                try:
                    selection = int(input("Select strategy number: ")) - 1
                    if 0 <= selection < len(strategies):
                        return "override", strategies[selection]
                    else:
                        print("Invalid selection")
                        continue
                except ValueError:
                    print("Invalid input, please enter a number")
                    continue

            elif choice == "s":
                return "skip", {}

            elif choice == "q":
                return "quit", {}

            else:
                print("Invalid choice, please try again")

    def record_user_action(
        self, entry: Dict[str, Any], action: str, choice: Dict[str, Any], month: str
    ) -> None:
        """Record user validation action."""
        if action == "skip" or action == "quit":
            return

        input_text = entry["input_text"]
        system_used = entry["system_used"]

        # Get system choice
        if system_used == "legacy":
            system_choice = {
                "strategy": "legacy",
                "score": None,
                "result": entry.get("matched", {}),
            }
        else:
            system_choice = entry.get("best_result", {})

        # Get all strategies
        all_strategies = entry.get("all_strategies", [])

        if action == "validate":
            self.user_actions_manager.record_validation(
                input_text=input_text,
                month=month,
                system_used=system_used,
                system_choice=system_choice,
                user_choice=choice,
                all_brush_strategies=all_strategies,
            )
        elif action == "override":
            self.user_actions_manager.record_override(
                input_text=input_text,
                month=month,
                system_used=system_used,
                system_choice=system_choice,
                user_choice=choice,
                all_brush_strategies=all_strategies,
            )

    def get_validation_statistics(self, month: str) -> Dict[str, Union[int, float]]:
        """Get validation statistics for month."""
        # Get total entries from data files
        legacy_entries = self.load_month_data(month, "legacy")
        scoring_entries = self.load_month_data(month, "scoring")
        total_entries = len(legacy_entries) + len(scoring_entries)

        # Get user action statistics
        user_stats = self.user_actions_manager.get_statistics(month)

        # Calculate combined statistics
        validated_count = user_stats["validated_count"]
        overridden_count = user_stats["overridden_count"]
        total_actions = validated_count + overridden_count
        unvalidated_count = max(0, total_entries - total_actions)

        validation_rate = total_actions / total_entries if total_entries > 0 else 0.0

        return {
            "total_entries": total_entries,
            "validated_count": validated_count,
            "overridden_count": overridden_count,
            "total_actions": total_actions,
            "unvalidated_count": unvalidated_count,
            "validation_rate": validation_rate,
        }

    def run_validation_workflow(
        self, month: str, system: str, sort_by: str
    ) -> Dict[str, Union[bool, int]]:
        """Run complete validation workflow.

        Args:
            month: Month to validate (YYYY-MM)
            system: 'legacy', 'scoring', or 'both'
            sort_by: Sort order for entries

        Returns:
            Dict with completion status and entries processed
        """
        print(f"\n🔍 Brush Validation Interface - {month}")
        print(f"System: {system}, Sort: {sort_by}")
        print("=" * 60)

        # Load and sort entries
        if system == "both":
            print("Error: 'both' system should be handled by caller")
            return {"completed": False, "entries_processed": 0}

        entries = self.load_month_data(month, system)
        if not entries:
            print(f"No entries found for {month} ({system} system)")
            return {"completed": True, "entries_processed": 0}

        sorted_entries = self.sort_entries(entries, month, sort_by)

        # Show initial statistics
        stats = self.get_validation_statistics(month)
        print(f"\nValidation Statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Validated: {stats['validated_count']}")
        print(f"  Overridden: {stats['overridden_count']}")
        print(f"  Unvalidated: {stats['unvalidated_count']}")
        print(f"  Validation rate: {stats['validation_rate']:.1%}")

        # Process entries
        entries_processed = 0
        try:
            for i, entry in enumerate(sorted_entries, 1):
                self.display_entry(entry, i, len(sorted_entries))

                action, choice = self.get_user_choice(entry)

                if action == "quit":
                    print("\nValidation stopped by user")
                    break
                elif action == "skip":
                    print("Skipped")
                    continue
                else:
                    self.record_user_action(entry, action, choice, month)
                    print(f"Recorded {action}")
                    entries_processed += 1

        except KeyboardInterrupt:
            print("\n\nValidation interrupted by user")

        # Show final statistics
        final_stats = self.get_validation_statistics(month)
        print(f"\n📊 Final Statistics:")
        print(f"  Entries processed: {entries_processed}")
        print(f"  Validation rate: {final_stats['validation_rate']:.1%}")

        return {"completed": action != "quit", "entries_processed": entries_processed}


def setup_validation_cli() -> argparse.ArgumentParser:
    """Set up CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Brush Validation Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate scoring system results for August 2025
  python -m sotd.match.brush_validation_cli --month 2025-08 --system scoring
  
  # Validate with ambiguity sorting
  python -m sotd.match.brush_validation_cli --month 2025-08 --sort-by ambiguity
  
  # Validate both systems
  python -m sotd.match.brush_validation_cli --month 2025-08 --system both
        """,
    )

    parser.add_argument(
        "--system",
        choices=["legacy", "scoring", "both"],
        default="both",
        help="Brush system to validate (default: both)",
    )

    parser.add_argument(
        "--sort-by",
        choices=["unvalidated", "validated", "ambiguity"],
        default="unvalidated",
        help="Sort order for validation (default: unvalidated)",
    )

    parser.add_argument("--month", required=True, help="Month to validate in YYYY-MM format")

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = setup_validation_cli()
    args = parser.parse_args()

    try:
        cli = BrushValidationCLI()

        if args.system == "both":
            # Validate both systems sequentially
            for system in ["legacy", "scoring"]:
                print(f"\n{'=' * 60}")
                print(f"Validating {system.upper()} system")
                print(f"{'=' * 60}")

                result = cli.run_validation_workflow(args.month, system, args.sort_by)
                print(
                    f"\n{system.title()} system validation: {result['entries_processed']} entries processed"
                )
        else:
            # Validate single system
            result = cli.run_validation_workflow(args.month, args.system, args.sort_by)
            print(f"\nValidation complete: {result['entries_processed']} entries processed")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
