"""Shared counting service for brush validation statistics."""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Union

from sotd.utils.file_io import load_json_data
import yaml


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
        """Get validation statistics for a month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with validation statistics including:
            - total_entries: Total unique brush strings
            - validated_count: Count of validated entries (correct_matches + user_validated)
            - overridden_count: Count of overridden entries
            - unvalidated_count: Count of unvalidated entries
            - validation_rate: Percentage of validated entries
        """
        start_time = time.time()
        try:
            # Load data from all sources
            matched_data = self._load_matched_data(month)
            learning_data = self._load_learning_data(month)

            # Count unique brush strings (case-insensitive)
            total_entries = self._count_unique_brush_strings(matched_data)

            # Count correct matches (already validated)
            correct_matches_count = self._count_correct_matches(matched_data)

            # Count user actions
            user_stats = self._count_user_actions(learning_data)
            validated_count = correct_matches_count + user_stats["validated_count"]
            overridden_count = user_stats["overridden_count"]

            # Calculate unvalidated count
            # Both validated and overridden count as "processed" for this calculation
            total_processed = validated_count + overridden_count
            unvalidated_count = max(0, total_entries - total_processed)

            # Calculate validation rate
            validation_rate = total_processed / total_entries if total_entries > 0 else 0.0

            processing_time = time.time() - start_time
            self.logger.info(
                f"Validation statistics for {month} completed in {processing_time:.3f}s "
                f"(entries: {total_entries}, validated: {validated_count}, "
                f"overridden: {overridden_count}, unvalidated: {unvalidated_count})"
            )

            return {
                "total_entries": total_entries,
                "validated_count": validated_count,
                "overridden_count": overridden_count,
                "total_actions": total_processed,
                "unvalidated_count": unvalidated_count,
                "validation_rate": validation_rate,
            }

        except Exception as e:
            self.logger.error(f"Error getting validation statistics for {month}: {e}")
            return {
                "total_entries": 0,
                "validated_count": 0,
                "overridden_count": 0,
                "total_actions": 0,
                "unvalidated_count": 0,
                "validation_rate": 0.0,
            }

    def get_strategy_distribution_statistics(self, month: str) -> Dict[str, Any]:
        """Get strategy distribution statistics for validation interface.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary with strategy distribution statistics including:
            - total_brush_records: Total unique brush strings
            - correct_matches_count: Count of entries from correct_matches.yaml
            - remaining_entries: Count of unvalidated entries
            - strategy_counts: Count of each strategy type
            - all_strategies_lengths: Distribution of strategy array lengths
        """
        start_time = time.time()
        try:
            # Load data from all sources
            matched_data = self._load_matched_data(month)
            learning_data = self._load_learning_data(month)
            correct_matches = self._load_correct_matches()

            # Count unique brush strings (case-insensitive)
            total_brush_records = self._count_unique_brush_strings(matched_data)

            # Count correct matches (already validated)
            correct_matches_count = self._count_correct_matches(matched_data)

            # Count user actions to get truly unvalidated count
            user_stats = self._count_user_actions(learning_data)
            total_user_actions = user_stats["validated_count"] + user_stats["overridden_count"]

            # Remaining entries are those not in correct_matches and not user-validated
            remaining_entries = max(
                0, total_brush_records - correct_matches_count - total_user_actions
            )

            # Count strategies and all_strategies lengths for unvalidated entries only
            strategy_counts, all_strategies_lengths = self._analyze_strategies(
                matched_data, correct_matches, learning_data
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

    def _load_matched_data(self, month: str) -> Dict[str, Any]:
        """Load matched data for a month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary containing matched data
        """
        file_path = self.data_path / "matched" / f"{month}.json"

        if not file_path.exists():
            self.logger.warning(f"Matched data file not found: {file_path}")
            return {"data": []}

        try:
            data = load_json_data(file_path)

            # Handle new file structure with metadata and data array
            if "data" in data:
                return data
            else:
                # Fallback to old structure
                return {"data": data.get("brush", [])}

        except Exception as e:
            self.logger.error(f"Error loading matched data for {month}: {e}")
            return {"data": []}

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
        """Count entries that are already validated (from correct_matches.yaml).

        Args:
            matched_data: Matched data dictionary

        Returns:
            Count of correct matches
        """
        correct_matches_strings = set()
        records = matched_data.get("data", [])

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            matched = brush_entry.get("matched")

            if matched and matched.get("strategy") in [
                "correct_complete_brush",
                "correct_split_brush",
            ]:
                normalized_text = brush_entry.get("normalized", "")
                if normalized_text:
                    correct_matches_strings.add(normalized_text.lower().strip())

        return len(correct_matches_strings)

    def _count_user_actions(self, learning_data: Dict[str, Any]) -> Dict[str, int]:
        """Count user validation actions.

        Args:
            learning_data: Learning data dictionary

        Returns:
            Dictionary with validated_count and overridden_count
        """
        validated_count = 0
        overridden_count = 0

        actions = learning_data.get("brush_user_actions", [])

        for action in actions:
            if action.get("action") == "validated":
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
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """Analyze strategies for all entries.

        Args:
            matched_data: Matched data dictionary
            correct_matches: Correct matches dictionary
            learning_data: Learning data dictionary

        Returns:
            Tuple of (strategy_counts, all_strategies_lengths)
        """
        strategy_counts = {}
        all_strategies_lengths = {}

        records = matched_data.get("data", [])

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            normalized_text = brush_entry.get("normalized", "")

            if not normalized_text:
                continue

            normalized_lower = normalized_text.lower().strip()

            # Count ALL strategies (not just unvalidated ones)
            matched = brush_entry.get("matched")
            if matched:
                strategy = matched.get("strategy", "unknown")
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            # Count all_strategies length for ALL entries
            all_strategies = brush_entry.get("all_strategies", [])
            if all_strategies is not None:
                length = len(all_strategies)
                length_key = str(length)
                if length_key not in all_strategies_lengths:
                    all_strategies_lengths[length_key] = set()
                all_strategies_lengths[length_key].add(normalized_lower)
            else:
                if "None" not in all_strategies_lengths:
                    all_strategies_lengths["None"] = set()
                all_strategies_lengths["None"].add(normalized_lower)

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
