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

    def _get_validated_normalized_texts(self, month: str) -> set[str]:
        """Get all validated normalized texts (correct matches + user validations).

        Args:
            month: Month in YYYY-MM format

        Returns:
            Set of normalized texts that are already validated
        """
        validated_texts = set()

        try:
            # Get correct matches from matched data
            file_path = self.data_path / "matched" / f"{month}.json"
            if file_path.exists():
                data = load_json_data(file_path)
                records = data.get("data", [])

                if records:  # Only iterate if records is not None and not empty
                    for record in records:
                        if "brush" not in record:
                            continue

                        brush_entry = record["brush"]
                        matched = brush_entry.get("matched")

                        # Check if it's a correct match (from correct_matches.yaml)
                        # Check both matched strategy and all_strategies
                        is_correct_match = False
                        if matched and matched.get("strategy") in [
                            "correct_complete_brush",
                        ]:
                            is_correct_match = True
                        else:
                            # Also check all_strategies for correct matches
                            all_strategies = brush_entry.get("all_strategies", [])
                            if all_strategies:
                                for strategy_info in all_strategies:
                                    if (
                                        isinstance(strategy_info, dict)
                                        and strategy_info.get("strategy")
                                        == "correct_complete_brush"
                                    ):
                                        is_correct_match = True
                                        break
                                    elif (
                                        isinstance(strategy_info, str)
                                        and strategy_info == "correct_complete_brush"
                                    ):
                                        is_correct_match = True
                                        break

                        if is_correct_match:
                            normalized_text = brush_entry.get("normalized", "")
                            if normalized_text:
                                validated_texts.add(normalized_text.lower().strip())

            # Get user validations from learning data, excluding those already counted
            learning_file_path = (
                self.data_path / "learning" / "brush_user_actions" / f"{month}.yaml"
            )
            if learning_file_path.exists():
                try:
                    import yaml

                    with open(learning_file_path, "r", encoding="utf-8") as f:
                        learning_data = yaml.safe_load(f) or {}

                    actions = learning_data.get("brush_user_actions", [])
                    if actions and isinstance(actions, list):
                        for action in actions:
                            if action.get("action") == "validated":
                                input_text = action.get("input_text", "")
                                if input_text:
                                    normalized_input = input_text.lower().strip()
                                    # Only add if NOT already counted as a correct match
                                    if normalized_input not in validated_texts:
                                        validated_texts.add(normalized_input)
                except Exception as e:
                    print(f"Warning: Could not load validation data: {e}")

        except Exception as e:
            print(f"Warning: Could not load validation data: {e}")

        return validated_texts

    def load_month_data(self, month: str, system: str) -> List[Dict[str, Any]]:
        """Load monthly brush data for validation using unified classification.

        Args:
            month: Month in YYYY-MM format
            system: 'legacy', 'scoring', or 'both'

        Returns:
            List of brush entries with system metadata, deduplicated by normalized text.
            For scoring system, filters out both correct entries and user validations.
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

            # Get validated normalized texts (correct matches + user validations)
            validated_normalized_texts = self._get_validated_normalized_texts(month)

            # Normalize data structure for validation interface
            entries = []
            seen_normalized_texts = set()  # Track seen normalized texts for deduplication

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

                    # Add legacy entry to entries list
                    entries.append(entry)
                else:  # scoring system
                    # Get normalized text for validation check
                    normalized_text = brush_entry.get("normalized", "")
                    if normalized_text:
                        normalized_lower = normalized_text.lower().strip()

                        # Skip if this entry is already validated (correct match or user validation)
                        if normalized_lower in validated_normalized_texts:
                            continue  # Skip to next record
                        else:
                            pass  # No debug print for unvalidated entries

                    # For scoring system, use matched field directly
                    # (contains the best result)
                    matched_data = brush_entry.get("matched", {})

                    entry = {
                        # Use normalized field for matching
                        "input_text": brush_entry.get("normalized", ""),
                        "normalized_text": brush_entry.get("normalized", ""),
                        "system_used": "scoring",
                        "matched": matched_data,  # Use matched field directly
                        "all_strategies": brush_entry.get("all_strategies", []),
                        "comment_ids": comment_ids,
                    }

                    # Deduplicate by normalized text (case-insensitive)
                    if normalized_text:
                        normalized_lower = normalized_text.lower().strip()
                        if normalized_lower not in seen_normalized_texts:
                            seen_normalized_texts.add(normalized_lower)
                            entries.append(entry)
                        else:
                            pass  # Skipping duplicate
                    else:
                        pass  # No normalized text, skipping entry

            # For scoring system, verify we have the correct count
            if system == "scoring":
                try:
                    counting_service = BrushValidationCountingService()
                    stats = counting_service.get_validation_statistics(month)
                    expected_unvalidated = stats["unvalidated_count"]

                    if len(entries) != expected_unvalidated:
                        print(
                            f"Warning: CLI loaded {len(entries)} entries, but counting "
                            f"service expects {expected_unvalidated} unvalidated entries"
                        )
                        print("This suggests some user validations may not be properly filtered")

                except Exception as e:
                    print(f"Warning: Could not verify unvalidated count: {e}")

            return entries

        except Exception as e:
            print(f"Error loading data for {month} ({system}): {e}")
            return []

    def get_comment_ids_for_input_text(self, input_text: str, month: str, system: str) -> List[str]:
        """Get comment IDs for a specific input text from matched data."""
        try:
            # Load the matched data for the month
            if system == "legacy":
                file_path = self.data_path / "matched_legacy" / f"{month}.json"
            elif system == "scoring":
                file_path = self.data_path / "matched" / f"{month}.json"
            else:
                return []

            if not file_path.exists():
                return []

            data = load_json_data(file_path)

            # Handle new file structure with metadata and data array
            if "data" in data:
                records = data.get("data", [])
            else:
                # Fallback to old structure
                records = data.get("brush", [])

            # Find the record with matching input text
            for record in records:
                if "brush" in record:
                    brush_entry = record["brush"]
                    normalized_text = brush_entry.get("normalized", "")
                    if normalized_text.lower() == input_text.lower():
                        comment_id = record.get("id")
                        return [comment_id] if comment_id else []

            return []
        except Exception as e:
            print(f"Error getting comment IDs for input text: {e}")
            return []

    def load_brush_data_for_input_text(
        self, input_text: str, month: str, system: str
    ) -> Optional[Dict[str, Any]]:
        """Load brush data for a specific input text to determine field type and process dual-component brushes."""
        try:
            # Load the matched data for the month
            if system == "legacy":
                file_path = self.data_path / "matched_legacy" / f"{month}.json"
            elif system == "scoring":
                file_path = self.data_path / "matched" / f"{month}.json"
            else:
                return None

            if not file_path.exists():
                return None

            data = load_json_data(file_path)

            # Handle new file structure with metadata and data array
            if "data" in data:
                records = data.get("data", [])
            else:
                # Fallback to old structure
                records = data.get("brush", [])

            # Find the record with matching input text
            for record in records:
                if "brush" in record:
                    brush_entry = record["brush"]
                    normalized_text = brush_entry.get("normalized", "")
                    if normalized_text.lower() == input_text.lower():
                        # Return the matched data and all strategies
                        return {
                            "matched": brush_entry.get("matched"),
                            "all_strategies": brush_entry.get("all_strategies", []),
                            "input_text": input_text,
                            "normalized_text": normalized_text,
                        }

            return None
        except Exception as e:
            print(f"Error loading brush data for input text: {e}")
            return None

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
            # Use the actual data structure: strategy and score are at brush level
            strategy = entry.get("matched", {}).get("strategy", "N/A")
            score = entry.get("matched", {}).get("score", "N/A")
            print(f"Best Strategy: {strategy}")
            print(f"Score: {score}")

            # The matched field contains the actual result data
            matched_data = entry.get("matched", {})
            if matched_data:
                brand = matched_data.get("brand", "N/A")
                model = matched_data.get("model", "N/A")
                print(f"Result: {brand} {model}")
                if matched_data.get("handle"):
                    handle_brand = matched_data["handle"].get("brand", "N/A")
                    handle_model = matched_data["handle"].get("model", "N/A")
                    print(f"  Handle: {handle_brand} {handle_model}")
                if matched_data.get("knot"):
                    knot_brand = matched_data["knot"].get("brand", "N/A")
                    knot_model = matched_data["knot"].get("model", "N/A")
                    print(f"  Knot: {knot_brand} {knot_model}")

            # Show all strategies for context
            all_strategies = entry.get("all_strategies", [])
            if len(all_strategies) > 1:
                print("\nAll Strategies:")
                for i, strategy in enumerate(all_strategies):
                    score = strategy.get("score", "N/A")
                    name = strategy.get("strategy", "unknown")
                    print(f"  {i + 1}. {name} (Score: {score})")

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
                    # Use the actual data structure: matched field contains the result
                    result_dict = {
                        "strategy": entry.get("matched", {}).get("strategy", "unknown"),
                        "score": entry.get("matched", {}).get("score", None),
                        "result": entry.get("matched", {}),
                    }
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
            # Use the actual data structure: matched field contains the result
            system_choice = {
                "strategy": entry.get("matched", {}).get("strategy", "unknown"),
                "score": entry.get("matched", {}).get("score", None),
                "result": entry.get("matched", {}),
            }

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
        """Get validation statistics for a month using the counting service.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with validation statistics from counting service
        """
        # Use the CLI's counting service instance that was initialized with the correct data path
        return self.counting_service.get_validation_statistics(month)

    def get_validation_statistics_no_matcher(self, month: str) -> Dict[str, Union[int, float]]:
        """Get validation statistics without matcher dependency.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with validation statistics from counting service
        """
        # Use the CLI's counting service instance that was initialized with the correct data path
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
        self, month: str, system: str, sort_by: str = "unvalidated"
    ) -> Dict[str, Union[bool, int]]:
        """Run the validation workflow for a month.

        Args:
            month: Month in YYYY-MM format
            system: 'legacy', 'scoring', or 'both'
            sort_by: Sort order for entries ('unvalidated', 'validated', 'all')

        Returns:
            Dictionary with completion status and entries processed
        """
        # Load data
        entries = self.load_month_data(month, system)

        if not entries:
            print(f"No entries found for {month} with system {system}")
            return {"completed": True, "entries_processed": 0}

        # Get validation statistics from counting service
        stats = self.counting_service.get_validation_statistics(month)

        # Display statistics
        print(f"\n=== Brush Validation Statistics for {month} ===")
        print(f"Total unique brush strings: {stats['total_entries']}")
        print(f"Validated entries: {stats['validated_count']}")
        print(f"Overridden entries: {stats['overridden_count']}")
        print(f"Unvalidated entries: {stats['unvalidated_count']}")
        print(f"Validation rate: {stats['validation_rate']:.1%}")

        # Display CLI-specific statistics
        print("\n=== CLI Processing Statistics ===")
        print(f"Entries loaded after deduplication: {len(entries)}")
        print("Note: CLI shows individual brush records for validation, not unique brush strings")

        # Sort entries based on sort_by parameter
        if sort_by == "unvalidated":
            # Sort by validation status (unvalidated first)
            entries.sort(
                key=lambda x: (
                    x.get("matched", {}).get("strategy") in ["correct_complete_brush"],
                    x.get("normalized_text", "").lower(),
                )
            )
        elif sort_by == "validated":
            # Sort by validation status (validated first)
            entries.sort(
                key=lambda x: (
                    x.get("matched", {}).get("strategy") not in ["correct_complete_brush"],
                    x.get("normalized_text", "").lower(),
                )
            )
        else:  # sort_by == "all"
            # Sort alphabetically by normalized text
            entries.sort(key=lambda x: x.get("normalized_text", "").lower())

        # Process entries
        print(f"\n=== Processing {len(entries)} Entries ===")
        print("Press Enter to continue to next entry, 'q' to quit, 's' to skip, 'v' to validate")

        entries_processed = 0
        workflow_completed = True  # Track if workflow completed or was terminated

        for i, entry in enumerate(entries, 1):
            self.display_entry(entry, i, len(entries))

            # Get user input
            action = input("\nAction (Enter/q/s/v): ").strip().lower()

            if action == "q":
                print("Validation workflow terminated by user.")
                workflow_completed = False  # User terminated early
                break
            elif action == "s":
                print("Skipping entry...")
                continue
            elif action == "v":
                # For now, just mark as validated (placeholder)
                print("Validation functionality not yet implemented")
                entries_processed += 1
            else:
                # Default action (Enter) - continue to next
                pass

        print(f"\nValidation workflow completed. Processed {entries_processed} entries.")
        return {"completed": workflow_completed, "entries_processed": entries_processed}


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
