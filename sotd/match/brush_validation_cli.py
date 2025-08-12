"""Brush CLI validation interface for validating brush matching results."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from sotd.match.brush_user_actions import BrushUserActionsManager
from sotd.match.brush_validation_counting_service import BrushValidationCountingService
from sotd.utils.file_io import load_json_data


class BrushValidationCLI:
    """CLI interface for validating brush matching results."""

    def __init__(self, data_path: Optional[Path] = None):
        """Initialize CLI with data path and brush system integration."""
        if data_path is None:
            data_path = Path("data")

        self.data_path = Path(data_path)
        # Pass the correct correct_matches.yaml path to ensure consistency
        correct_matches_path = self.data_path / "correct_matches.yaml"
        self.user_actions_manager = BrushUserActionsManager(
            base_path=self.data_path / "learning", correct_matches_path=correct_matches_path
        )

        # Initialize the shared counting service
        self.counting_service = BrushValidationCountingService(data_path)

        # Lazy-load brush matcher entry point only when needed
        self._brush_entry_point = None

    @property
    def brush_entry_point(self):
        """Lazy-load brush matcher entry point when first accessed."""
        if self._brush_entry_point is None:
            from sotd.match.brush_matcher_entry import BrushMatcherEntryPoint

            self._brush_entry_point = BrushMatcherEntryPoint()
        return self._brush_entry_point

    def load_month_data(self, month: str, system: str) -> List[Dict[str, Any]]:
        """Load monthly brush data for validation.

        Args:
            month: Month in YYYY-MM format
            system: 'legacy', 'scoring', or 'both'

        Returns:
            List of brush entries with system metadata
        """
        # Use correct directories for each system
        if system == "legacy":
            file_path = self.data_path / "matched_legacy" / f"{month}.json"
        elif system == "scoring":
            file_path = self.data_path / "matched" / f"{month}.json"
        else:
            raise ValueError(f"Invalid system for single load: {system}")

        try:
            data = load_json_data(file_path)

            # Handle new file structure with metadata and data array
            if "data" in data:
                records = data.get("data", [])
            else:
                # Fallback to old structure
                records = data.get("brush", [])

            if not records:
                return []

            # Normalize data structure for validation interface
            entries = []
            for record in records:
                if "brush" not in record:
                    continue

                brush_entry = record["brush"]

                # Get comment ID from the record
                comment_id = record.get("id")
                comment_ids = [comment_id] if comment_id else []

                if system == "legacy":
                    entry = {
                        # Use normalized field for matching
                        "input_text": brush_entry.get("normalized", ""),
                        "system_used": "legacy",
                        "matched": brush_entry.get("matched"),
                        "match_type": brush_entry.get("match_type"),
                        "all_strategies": [],  # Legacy system doesn't track all strategies
                        "comment_ids": comment_ids,
                    }
                else:  # scoring system
                    # Filter out entries that come from correct_matches.yaml
                    # These are already validated and don't need user validation
                    matched = brush_entry.get("matched")
                    strategy = ""

                    # Only check strategy if matched exists
                    if matched is not None:
                        strategy = matched.get("strategy", "")

                    # Skip entries with correct_complete_brush or correct_split_brush strategies
                    if strategy in ["correct_complete_brush", "correct_split_brush"]:
                        continue

                    entry = {
                        # Use normalized field for matching
                        "input_text": brush_entry.get("normalized", ""),
                        "normalized_text": brush_entry.get("normalized", ""),
                        "system_used": "scoring",
                        "matched": brush_entry.get("matched"),  # Now contains strategy and score
                        "all_strategies": brush_entry.get("all_strategies", []),
                        "comment_ids": comment_ids,
                    }

                entries.append(entry)

            return entries

        except Exception as e:
            print(f"Error loading data for {month} ({system}): {e}")
            return []

    def get_comment_ids_for_input_text(self, input_text: str, month: str, system: str) -> List[str]:
        """Get comment IDs for a specific input text from the matched data.

        Args:
            input_text: The input text to search for
            month: Month in YYYY-MM format
            system: 'legacy' or 'scoring'

        Returns:
            List of comment IDs where this input text was found
        """
        # Use correct directories for each system
        if system == "legacy":
            file_path = self.data_path / "matched_legacy" / f"{month}.json"
        elif system == "scoring":
            file_path = self.data_path / "matched" / f"{month}.json"
        else:
            return []

        try:
            data = load_json_data(file_path)

            # Handle new file structure with metadata and data array
            if "data" in data:
                records = data.get("data", [])
            else:
                # Fallback to old structure
                records = data.get("brush", [])

            if not records:
                return []

            comment_ids = []
            normalized_input = input_text.lower().strip()

            for record in records:
                if "brush" not in record:
                    continue

                brush_entry = record["brush"]
                brush_text = brush_entry.get("original", "").lower().strip()

                # Case-insensitive comparison
                if brush_text == normalized_input:
                    comment_id = record.get("id")
                    if comment_id:
                        comment_ids.append(comment_id)

            return comment_ids

        except Exception as e:
            print(f"Error getting comment IDs for {input_text}: {e}")
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
        # Use case-insensitive comparison like in MismatchAnalyzer
        validated_texts = {action.input_text.lower().strip() for action in existing_actions}

        # Separate validated and unvalidated entries
        validated = []
        unvalidated = []

        for entry in entries:
            # Case-insensitive comparison
            entry_text = entry["input_text"].lower().strip()
            if entry_text in validated_texts:
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
                    handle_brand = matched["handle"].get("brand", "N/A")
                    handle_model = matched["handle"].get("model", "N/A")
                    print(f"  Handle: {handle_brand} {handle_model}")
                if matched.get("knot"):
                    knot_brand = matched["knot"].get("brand", "N/A")
                    knot_model = matched["knot"].get("model", "N/A")
                    print(f"  Knot: {knot_brand} {knot_model}")
            else:
                print("Result: No match")

        else:  # scoring system
            best_result = entry.get("best_result")
            if best_result:
                print(f"Best Strategy: {best_result.get('strategy', 'N/A')}")
                print(f"Score: {best_result.get('score', 'N/A')}")

                result = best_result.get("result", {})
                if result:
                    brand = result.get("brand", "N/A")
                    model = result.get("model", "N/A")
                    print(f"Result: {brand} {model}")
                    if result.get("handle"):
                        handle_brand = result["handle"].get("brand", "N/A")
                        handle_model = result["handle"].get("model", "N/A")
                        print(f"  Handle: {handle_brand} {handle_model}")
                    if result.get("knot"):
                        knot_brand = result["knot"].get("brand", "N/A")
                        knot_model = result["knot"].get("model", "N/A")
                        print(f"  Knot: {knot_brand} {knot_model}")

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
        comment_ids = entry.get("comment_ids", [])

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
                comment_ids=comment_ids,
            )
        elif action == "override":
            self.user_actions_manager.record_override(
                input_text=input_text,
                month=month,
                system_used=system_used,
                system_choice=system_choice,
                user_choice=choice,
                all_brush_strategies=all_strategies,
                comment_ids=comment_ids,
            )

    def get_validation_statistics(self, month: str) -> Dict[str, Union[int, float]]:
        """Get validation statistics for month."""
        # Delegate to the shared counting service for consistent statistics
        return self.counting_service.get_validation_statistics(month)

    def get_validation_statistics_no_matcher(self, month: str) -> Dict[str, Union[int, float]]:
        """Get validation statistics for month without loading brush matcher.

        This method provides the same functionality as get_validation_statistics
        but avoids loading the brush matcher, making it suitable for API endpoints
        that don't need matching functionality.

        Now delegates to the shared counting service for consistent statistics.
        """
        # Delegate to the shared counting service for consistent statistics
        return self.counting_service.get_validation_statistics(month)

    def get_strategy_distribution_statistics(self, month: str) -> Dict[str, Any]:
        """Get strategy distribution statistics for validation interface.

        This method provides detailed counts of entries by strategy type
        to help debug filter count mismatches.

        Now delegates to the shared counting service for consistent statistics.
        """
        # Delegate to the shared counting service for consistent statistics
        return self.counting_service.get_strategy_distribution_statistics(month)

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
        print("\nValidation Statistics:")
        print(f"  Total entries: {stats['total_entries']}")
        print(f"  Validated: {stats['validated_count']}")
        print(f"  Overridden: {stats['overridden_count']}")
        print(f"  Unvalidated: {stats['unvalidated_count']}")
        print(f"  Validation rate: {stats['validation_rate']:.1%}")

        # Process entries
        entries_processed = 0
        action = "skip"  # Initialize action to avoid unbound variable
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
        print("\n📊 Final Statistics:")
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
                    f"\n{system.title()} system validation: "
                    f"{result['entries_processed']} entries processed"
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
