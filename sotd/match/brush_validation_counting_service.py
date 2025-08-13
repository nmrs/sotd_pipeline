"""Shared counting service for brush validation statistics."""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Union

import yaml

from sotd.utils.file_io import load_json_data


class BrushValidationCountingService:
    """Shared counting service for brush validation statistics.

    This service provides consistent, accurate counts across CLI and webui interfaces.
    It implements proper mathematical relationships, case-insensitive grouping, and
    handles all validation states correctly.
    """

    def __init__(self, data_path: Path | None = None):
        """Initialize the counting service.

        Args:
            data_path: Path to data directory. Defaults to "data".
        """
        if data_path is None:
            data_path = Path("data")

        self.data_path = Path(data_path)
        self.logger = logging.getLogger(__name__)

    def get_validation_statistics(self, month: str) -> Dict[str, Union[int, float]]:
        """Get validation statistics for a month with unified classification.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with validation statistics including:
            - total_entries: Total unique brush strings
            - correct_entries: Count of correct entries (from correct_matches.yaml)
            - user_validations: Count of user validation actions
            - unvalidated_count: Count of unvalidated entries
            - validation_rate: Percentage of processed entries (correct + user validations)
        """
        start_time = time.time()
        try:
            # Load data from all sources
            matched_data = self._load_matched_data(month)
            learning_data = self._load_learning_data(month)

            # Count unique brush strings (case-insensitive)
            total_entries = self._count_unique_brush_strings(matched_data)

            # Count correct matches (already validated)
            correct_entries = self._count_correct_matches(matched_data)

            # Count user actions
            user_stats = self._count_user_actions(matched_data, learning_data)
            user_validations = user_stats["validated_count"]
            overridden_count = user_stats["overridden_count"]

            # Calculate unvalidated count
            # Only correct entries and user validations count as "processed"
            total_processed = correct_entries + user_validations
            unvalidated_count = max(0, total_entries - total_processed)

            # Calculate validation rate (correct entries + user validations)
            validation_rate = total_processed / total_entries if total_entries > 0 else 0.0

            processing_time = time.time() - start_time
            self.logger.info(
                f"Validation statistics for {month} completed in {processing_time:.3f}s "
                f"(total: {total_entries}, correct: {correct_entries}, "
                f"user_validations: {user_validations}, unvalidated: {unvalidated_count})"
            )

            return {
                "total_entries": total_entries,
                "correct_entries": correct_entries,
                "user_validations": user_validations,
                "overridden_count": overridden_count,
                "total_processed": total_processed,
                "unvalidated_count": unvalidated_count,
                "validation_rate": validation_rate,
                # Legacy fields for backward compatibility
                "validated_count": total_processed,
                "total_actions": total_processed + overridden_count,
            }

        except Exception as e:
            self.logger.error(f"Error getting validation statistics for {month}: {e}")
            return {
                "total_entries": 0,
                "correct_entries": 0,
                "user_validations": 0,
                "overridden_count": 0,
                "total_processed": 0,
                "unvalidated_count": 0,
                "validation_rate": 0.0,
                # Legacy fields for backward compatibility
                "validated_count": 0,
                "total_actions": 0,
            }

    def get_strategy_distribution_statistics(self, month: str) -> Dict[str, Any]:
        """Get strategy distribution statistics for UNVALIDATED entries only.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with strategy distribution statistics for unvalidated entries
        """
        start_time = time.time()

        try:
            # Load data
            matched_data = self._load_matched_data(month)
            correct_matches = self._load_correct_matches()
            learning_data = self._load_learning_data(month)

            # Count total brush records
            total_brush_records = self._count_unique_brush_strings(matched_data)
            correct_matches_count = self._count_correct_matches(matched_data)
            remaining_entries = total_brush_records - correct_matches_count

            # Count strategies and all_strategies lengths for UNVALIDATED entries only
            strategy_counts, all_strategies_lengths = self._analyze_strategies(
                matched_data, correct_matches, learning_data, only_unvalidated=True
            )

            processing_time = time.time() - start_time
            self.logger.info(
                f"Strategy distribution for {month} completed in {processing_time:.3f}s "
                f"(total: {total_brush_records}, strategies: {len(strategy_counts)}, "
                f"remaining: {remaining_entries})"
            )

            return {
                "total_brush_records": total_brush_records,
                "correct_matches_count": correct_matches_count,
                "remaining_entries": remaining_entries,
                "strategy_counts": strategy_counts,
                "all_strategies_lengths": all_strategies_lengths,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"Error getting strategy distribution statistics for {month} "
                f"(after {processing_time:.3f}s): {e}"
            )
            return {
                "total_brush_records": 0,
                "correct_matches_count": 0,
                "remaining_entries": 0,
                "strategy_counts": {},
                "all_strategies_lengths": {},
            }

    def get_all_entries_strategy_distribution_statistics(self, month: str) -> Dict[str, Any]:
        """Get strategy distribution statistics for ALL entries (validated + unvalidated).

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with strategy distribution statistics for all entries
        """
        start_time = time.time()

        try:
            # Load data
            matched_data = self._load_matched_data(month)
            correct_matches = self._load_correct_matches()
            learning_data = self._load_learning_data(month)

            # Count total brush records
            total_brush_records = self._count_unique_brush_strings(matched_data)
            correct_matches_count = self._count_correct_matches(matched_data)
            remaining_entries = total_brush_records - correct_matches_count

            # Count strategies and all_strategies lengths for ALL entries
            strategy_counts, all_strategies_lengths = self._analyze_strategies(
                matched_data, correct_matches, learning_data, only_unvalidated=False
            )

            processing_time = time.time() - start_time
            self.logger.info(
                f"All entries strategy distribution for {month} completed in "
                f"{processing_time:.3f}s (total: {total_brush_records}, "
                f"strategies: {len(strategy_counts)})"
            )

            return {
                "total_brush_records": total_brush_records,
                "correct_matches_count": correct_matches_count,
                "remaining_entries": remaining_entries,
                "strategy_counts": strategy_counts,
                "all_strategies_lengths": all_strategies_lengths,
            }

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"Error getting all entries strategy distribution statistics for {month} "
                f"(after {processing_time:.3f}s): {e}"
            )
            return {
                "total_brush_records": 0,
                "correct_matches_count": 0,
                "remaining_entries": 0,
                "strategy_counts": {},
                "all_strategies_lengths": {},
            }

    def _load_matched_data(self, month: str) -> Dict[str, Any]:
        """Load matched data for a month from both legacy and scoring systems.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary containing combined matched data from both systems
        """
        combined_data = {"data": []}

        # Load scoring system data
        scoring_file_path = self.data_path / "matched" / f"{month}.json"
        if scoring_file_path.exists():
            try:
                scoring_data = load_json_data(scoring_file_path)
                if "data" in scoring_data:
                    combined_data["data"].extend(scoring_data.get("data", []))
                else:
                    # Fallback to old structure
                    combined_data["data"].extend(scoring_data.get("brush", []))
            except Exception as e:
                self.logger.error(f"Error loading scoring data for {month}: {e}")

        # Load legacy system data
        legacy_file_path = self.data_path / "matched_legacy" / f"{month}.json"
        if legacy_file_path.exists():
            try:
                legacy_data = load_json_data(legacy_file_path)
                if "data" in legacy_data:
                    combined_data["data"].extend(legacy_data.get("data", []))
                else:
                    # Fallback to old structure
                    combined_data["data"].extend(legacy_data.get("brush", []))
            except Exception as e:
                self.logger.error(f"Error loading legacy data for {month}: {e}")

        if not combined_data["data"]:
            self.logger.warning(f"No matched data found for {month} in either system")

        return combined_data

    def _load_learning_data(self, month: str) -> Dict[str, Any]:
        """Load learning data for a month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary containing learning data
        """
        file_path = self.data_path / "learning" / "brush_user_actions" / f"{month}.yaml"

        if not file_path.exists():
            self.logger.warning(f"Learning data file not found: {file_path}")
            return {"brush_user_actions": []}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if data else {"brush_user_actions": []}

        except Exception as e:
            self.logger.error(f"Error loading learning data for {month}: {e}")
            return {"brush_user_actions": []}

    def _load_correct_matches(self) -> Dict[str, Any]:
        """Load correct_matches.yaml data.

        Returns:
            Dictionary containing correct matches data
        """
        file_path = self.data_path / "correct_matches.yaml"

        if not file_path.exists():
            self.logger.warning(f"Correct matches file not found: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if data else {}

        except Exception as e:
            self.logger.error(f"Error loading correct matches: {e}")
            return {}

    def _count_unique_brush_strings(self, matched_data: Dict[str, Any]) -> int:
        """Count unique brush strings (case-insensitive).

        Args:
            matched_data: Matched data dictionary

        Returns:
            Count of unique brush strings
        """
        unique_strings = set()
        records = matched_data.get("data", [])

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            normalized_text = brush_entry.get("normalized", "")

            if normalized_text:
                # Case-insensitive grouping
                unique_strings.add(normalized_text.lower().strip())

        return len(unique_strings)

    def _count_correct_matches(self, matched_data: Dict[str, Any]) -> int:
        """Count unique brush strings that are correct matches.

        Args:
            matched_data: Matched data dictionary

        Returns:
            Count of unique correct match brush strings
        """
        correct_matches_strings = set()
        records = matched_data.get("data", [])

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            # Strategy is available at both brush.strategy and brush.matched.strategy
            # Use brush.strategy for consistency with CLI and other consumers
            strategy = brush_entry.get("strategy")

            if strategy in [
                "correct_complete_brush",
            ]:
                normalized_text = brush_entry.get("normalized", "")
                if normalized_text:
                    correct_matches_strings.add(normalized_text.lower().strip())

        return len(correct_matches_strings)

    def _count_user_actions(
        self, matched_data: Dict[str, Any], learning_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Count user validation actions, excluding those already counted as correct matches.

        Args:
            matched_data: Matched data dictionary (to identify correct matches)
            learning_data: Learning data dictionary

        Returns:
            Dictionary with validated_count and overridden_count
        """
        validated_count = 0
        overridden_count = 0

        # Get the set of normalized texts that are already correct matches
        correct_match_texts = set()
        records = matched_data.get("data", [])
        for record in records:
            if "brush" not in record:
                continue
            brush_entry = record["brush"]
            # Strategy is available at both brush.strategy and brush.matched.strategy
            # Use brush.strategy for consistency with CLI and other consumers
            strategy = brush_entry.get("strategy")
            if strategy in [
                "correct_complete_brush",
            ]:
                normalized_text = brush_entry.get("normalized", "")
                if normalized_text:
                    correct_match_texts.add(normalized_text.lower().strip())

        actions = learning_data.get("brush_user_actions", [])

        for action in actions:
            if action.get("action") == "validated":
                input_text = action.get("input_text", "")
                if input_text:
                    normalized_input = input_text.lower().strip()
                    # Only count if NOT already a correct match
                    if normalized_input not in correct_match_texts:
                        validated_count += 1
            elif action.get("action") == "overridden":
                overridden_count += 1

        return {
            "validated_count": validated_count,
            "overridden_count": overridden_count,
        }

    def _analyze_strategies(
        self,
        matched_data: Dict[str, Any],
        correct_matches: Dict[str, Any],
        learning_data: Dict[str, Any],
        only_unvalidated: bool = False,
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """Analyze strategies for entries.

        Args:
            matched_data: Matched data dictionary
            correct_matches: Correct matches dictionary
            learning_data: Learning data dictionary
            only_unvalidated: If True, only count unvalidated entries

        Returns:
            Tuple of (strategy_counts, all_strategies_lengths)
        """
        strategy_counts = {}
        all_strategies_lengths = {}

        records = matched_data.get("data", [])

        # Debug logging
        validated_count = 0
        unvalidated_count = 0

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            normalized_text = brush_entry.get("normalized", "")

            if not normalized_text:
                continue

            normalized_lower = normalized_text.lower().strip()

            # Check if this entry is validated and should be skipped
            if only_unvalidated:
                # Strategy is available at both brush.strategy and brush.matched.strategy
                # Use brush.strategy for consistency with CLI and other consumers
                strategy = brush_entry.get("strategy")
                if strategy in [
                    "correct_complete_brush",
                ]:
                    # This is a validated entry, skip it completely
                    validated_count += 1
                    print(
                        f"DEBUG: Skipping validated entry '{normalized_lower}' "
                        f"with strategy '{strategy}'"
                    )
                    continue  # Skip this entry completely

            # If we get here, the entry is not validated (or we're counting all entries)
            unvalidated_count += 1

            # Count strategies (only for unvalidated entries when only_unvalidated=True)
            if not only_unvalidated:
                # Strategy is available at both brush.strategy and brush.matched.strategy
                # Use brush.strategy for consistency with CLI and other consumers
                strategy = brush_entry.get("strategy", "unknown")
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            # Count all_strategies length for entries (only unvalidated when only_unvalidated=True)
            # Since we've already skipped validated entries above, we can safely count these
            all_strategies = brush_entry.get("all_strategies", [])
            if all_strategies is not None:
                length = len(all_strategies)
                length_key = str(length)
                if length_key not in all_strategies_lengths:
                    all_strategies_lengths[length_key] = set()
                all_strategies_lengths[length_key].add(normalized_lower)
                print(f"DEBUG: Counting entry '{normalized_lower}' with {length} strategies")
            else:
                if "None" not in all_strategies_lengths:
                    all_strategies_lengths["None"] = set()
                all_strategies_lengths["None"].add(normalized_lower)
                print(f"DEBUG: Counting entry '{normalized_lower}' with no strategies")

        # Debug logging
        if only_unvalidated:
            self.logger.info(
                f"Validation filtering: {validated_count} validated entries skipped, "
                f"{unvalidated_count} unvalidated entries counted"
            )

        # Convert sets to counts
        all_strategies_lengths_counts = {}
        for length, string_set in all_strategies_lengths.items():
            all_strategies_lengths_counts[length] = len(string_set)

        return strategy_counts, all_strategies_lengths_counts

    def get_performance_metrics(self, month: str) -> Dict[str, Any]:
        """Get performance metrics for the counting service.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with performance metrics
        """
        start_time = time.time()

        # Measure validation statistics performance
        stats_start = time.time()
        stats = self.get_validation_statistics(month)
        stats_time = time.time() - stats_start

        # Measure strategy distribution performance
        strategy_start = time.time()
        _ = self.get_strategy_distribution_statistics(month)  # Measure time, ignore result
        strategy_time = time.time() - strategy_start

        total_time = time.time() - start_time

        return {
            "month": month,
            "total_processing_time": total_time,
            "validation_statistics_time": stats_time,
            "strategy_distribution_time": strategy_time,
            "total_entries": stats["total_entries"],
            "performance_notes": {
                "validation_statistics": f"Completed in {stats_time:.3f}s",
                "strategy_distribution": f"Completed in {strategy_time:.3f}s",
                "total_workflow": f"Completed in {total_time:.3f}s",
            },
        }
