"""
Brush system comparator for A/B testing between old and new systems.

This module provides functionality for comparing the performance and results
of the legacy brush matching system against the new scoring-based system.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class BrushSystemComparator:
    """
    Comparator for analyzing differences between brush matching systems.

    Provides functionality for comparing match results, performance metrics,
    and generating statistical analysis reports between the legacy and new
    brush matching systems.
    """

    def __init__(self, old_system_data: Dict[str, Any], new_system_data: Dict[str, Any]):
        """
        Initialize the brush system comparator.

        Args:
            old_system_data: Data from the legacy brush system
            new_system_data: Data from the new scoring system
        """
        self.old_data = old_system_data
        self.new_data = new_system_data
        self.comparison_results = {}

    def compare_matches(self) -> Dict[str, Any]:
        """
        Compare match results between the two systems.

        Returns:
            Dictionary containing comparison metrics and differences
        """
        old_records = self.old_data.get("data", [])
        new_records = self.new_data.get("data", [])

        if len(old_records) != len(new_records):
            raise ValueError(
                f"Record count mismatch: old={len(old_records)}, new={len(new_records)}"
            )

        comparison_metrics = {
            "total_records": len(old_records),
            "matching_results": 0,
            "different_results": 0,
            "old_only_matches": 0,
            "new_only_matches": 0,
            "both_unmatched": 0,
            "match_type_changes": defaultdict(int),
            "detailed_differences": [],
        }

        for i, (old_record, new_record) in enumerate(zip(old_records, new_records)):
            old_brush = old_record.get("brush", {}) or {}
            new_brush = new_record.get("brush", {}) or {}

            old_matched = old_brush.get("matched") is not None
            new_matched = new_brush.get("matched") is not None

            # Count different scenarios
            if old_matched and new_matched:
                if self._are_matches_equal(old_brush, new_brush):
                    comparison_metrics["matching_results"] += 1
                else:
                    comparison_metrics["different_results"] += 1
                    self._record_detailed_difference(i, old_brush, new_brush, comparison_metrics)
            elif old_matched and not new_matched:
                comparison_metrics["old_only_matches"] += 1
            elif not old_matched and new_matched:
                comparison_metrics["new_only_matches"] += 1
            else:
                comparison_metrics["both_unmatched"] += 1

        self.comparison_results = comparison_metrics
        return comparison_metrics

    def _are_matches_equal(self, old_brush: Dict[str, Any], new_brush: Dict[str, Any]) -> bool:
        """
        Compare if two brush matches are equivalent.

        Args:
            old_brush: Brush match from old system
            new_brush: Brush match from new system

        Returns:
            True if matches are equivalent, False otherwise
        """
        old_matched = old_brush.get("matched", {})
        new_matched = new_brush.get("matched", {})

        # Compare key fields
        key_fields = ["brand", "model", "fiber", "knot_size_mm", "handle_maker"]

        for field in key_fields:
            old_value = old_matched.get(field)
            new_value = new_matched.get(field)

            if old_value != new_value:
                return False

        return True

    def _record_detailed_difference(
        self,
        record_index: int,
        old_brush: Dict[str, Any],
        new_brush: Dict[str, Any],
        metrics: Dict[str, Any],
    ) -> None:
        """
        Record detailed information about a difference between systems.

        Args:
            record_index: Index of the record being compared
            old_brush: Brush match from old system
            new_brush: Brush match from new system
            metrics: Metrics dictionary to update
        """
        old_matched = old_brush.get("matched", {})
        new_matched = new_brush.get("matched", {})

        # Track match type changes
        old_type = old_brush.get("match_type", "unknown")
        new_type = new_brush.get("match_type", "unknown")

        if old_type != new_type:
            change_key = f"{old_type}_to_{new_type}"
            metrics["match_type_changes"][change_key] += 1

        # Record detailed difference
        difference = {
            "record_index": record_index,
            "input_text": old_brush.get("original", "unknown"),
            "old_match": {
                "brand": old_matched.get("brand"),
                "model": old_matched.get("model"),
                "fiber": old_matched.get("fiber"),
                "match_type": old_brush.get("match_type"),
                "pattern": old_brush.get("pattern"),
            },
            "new_match": {
                "brand": new_matched.get("brand"),
                "model": new_matched.get("model"),
                "fiber": new_matched.get("fiber"),
                "match_type": new_brush.get("match_type"),
                "pattern": new_brush.get("pattern"),
            },
        }

        metrics["detailed_differences"].append(difference)

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive comparison report.

        Returns:
            Dictionary containing the comparison report
        """
        if not self.comparison_results:
            self.compare_matches()

        metrics = self.comparison_results
        total_records = metrics["total_records"]

        # Calculate percentages
        report = {
            "summary": {
                "total_records": total_records,
                "matching_results": {
                    "count": metrics["matching_results"],
                    "percentage": (
                        (metrics["matching_results"] / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                },
                "different_results": {
                    "count": metrics["different_results"],
                    "percentage": (
                        (metrics["different_results"] / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                },
                "old_only_matches": {
                    "count": metrics["old_only_matches"],
                    "percentage": (
                        (metrics["old_only_matches"] / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                },
                "new_only_matches": {
                    "count": metrics["new_only_matches"],
                    "percentage": (
                        (metrics["new_only_matches"] / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                },
                "both_unmatched": {
                    "count": metrics["both_unmatched"],
                    "percentage": (
                        (metrics["both_unmatched"] / total_records * 100)
                        if total_records > 0
                        else 0
                    ),
                },
            },
            "match_type_changes": dict(metrics["match_type_changes"]),
            "detailed_differences": metrics["detailed_differences"][:10],  # Limit to first 10
            "total_differences": len(metrics["detailed_differences"]),
        }

        return report

    def identify_differences(self) -> List[Dict[str, Any]]:
        """
        Identify specific cases where systems produce different results.

        Returns:
            List of detailed difference records
        """
        if not self.comparison_results:
            self.compare_matches()

        return self.comparison_results.get("detailed_differences", [])

    def get_performance_comparison(self) -> Dict[str, Any]:
        """
        Compare performance metrics between systems.

        Returns:
            Dictionary containing performance comparison
        """
        old_performance = self.old_data.get("metadata", {}).get("performance", {})
        new_performance = self.new_data.get("metadata", {}).get("performance", {})

        return {
            "old_system_performance": old_performance,
            "new_system_performance": new_performance,
            "performance_differences": self._compare_performance_metrics(
                old_performance, new_performance
            ),
        }

    def _compare_performance_metrics(
        self, old_performance: Dict[str, Any], new_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare performance metrics between systems.

        Args:
            old_performance: Performance data from old system
            new_performance: Performance data from new system

        Returns:
            Dictionary containing performance differences
        """
        differences = {}

        # Compare timing metrics
        timing_metrics = ["total_time", "processing_time", "file_io_time"]

        for metric in timing_metrics:
            old_value = old_performance.get(metric, 0)
            new_value = new_performance.get(metric, 0)

            if old_value != new_value:
                differences[metric] = {
                    "old": old_value,
                    "new": new_value,
                    "difference": new_value - old_value,
                    "percentage_change": (
                        ((new_value - old_value) / old_value * 100) if old_value > 0 else 0
                    ),
                }

        return differences

    def save_comparison_report(self, output_path: Path) -> None:
        """
        Save the comparison report to a file.

        Args:
            output_path: Path where to save the report
        """
        report = self.generate_report()

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def get_statistical_summary(self) -> Dict[str, Any]:
        """
        Generate a statistical summary of the comparison.

        Returns:
            Dictionary containing statistical summary
        """
        if not self.comparison_results:
            self.compare_matches()

        metrics = self.comparison_results
        total_records = metrics["total_records"]

        # Calculate statistical measures
        summary = {
            "total_records": total_records,
            "agreement_rate": (
                (metrics["matching_results"] / total_records * 100) if total_records > 0 else 0
            ),
            "disagreement_rate": (
                (metrics["different_results"] / total_records * 100) if total_records > 0 else 0
            ),
            "old_system_success_rate": (
                ((metrics["matching_results"] + metrics["old_only_matches"]) / total_records * 100)
                if total_records > 0
                else 0
            ),
            "new_system_success_rate": (
                ((metrics["matching_results"] + metrics["new_only_matches"]) / total_records * 100)
                if total_records > 0
                else 0
            ),
            "most_common_match_type_change": self._get_most_common_change(),
            "difference_categories": {
                "brand_changes": self._count_brand_changes(),
                "model_changes": self._count_model_changes(),
                "fiber_changes": self._count_fiber_changes(),
            },
        }

        return summary

    def _get_most_common_change(self) -> Optional[Tuple[str, int]]:
        """
        Get the most common match type change.

        Returns:
            Tuple of (change_type, count) or None if no changes
        """
        changes = self.comparison_results.get("match_type_changes", {})
        if not changes:
            return None

        most_common = max(changes.items(), key=lambda x: x[1])
        return most_common

    def _count_brand_changes(self) -> int:
        """Count the number of brand changes between systems."""
        count = 0
        for diff in self.comparison_results.get("detailed_differences", []):
            old_brand = diff["old_match"]["brand"]
            new_brand = diff["new_match"]["brand"]
            if old_brand != new_brand:
                count += 1
        return count

    def _count_model_changes(self) -> int:
        """Count the number of model changes between systems."""
        count = 0
        for diff in self.comparison_results.get("detailed_differences", []):
            old_model = diff["old_match"]["model"]
            new_model = diff["new_match"]["model"]
            if old_model != new_model:
                count += 1
        return count

    def _count_fiber_changes(self) -> int:
        """Count the number of fiber changes between systems."""
        count = 0
        for diff in self.comparison_results.get("detailed_differences", []):
            old_fiber = diff["old_match"]["fiber"]
            new_fiber = diff["new_match"]["fiber"]
            if old_fiber != new_fiber:
                count += 1
        return count
