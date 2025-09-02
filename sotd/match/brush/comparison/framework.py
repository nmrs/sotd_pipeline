"""
Brush A/B comparison framework for comparing brush system outputs.

This module provides functionality for comparing outputs from the current
and new brush matching systems to analyze differences and agreement patterns.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


class BrushComparisonFramework:
    """
    Framework for comparing brush system outputs.

    Provides functionality for comparing outputs from current and new brush
    matching systems to analyze differences and agreement patterns.
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the brush comparison framework.

        Args:
            base_path: Base path for data directories (default: data/)
        """
        self.base_path = base_path or Path("data")
        self.current_dir = self.base_path / "matched"
        self.new_dir = self.base_path / "matched_new"

    def compare_month(self, month: str) -> Dict[str, Any]:
        """
        Compare brush matching results for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            Comparison result with agreement statistics and disagreements
        """
        try:
            # Load data from both systems
            current_data = self._load_system_data(month, "current")
            new_data = self._load_system_data(month, "new")

            # Validate data before accessing
            if not self._validate_comparison_data(current_data):
                return {
                    "month": month,
                    "status": "error",
                    "error": "current system data not found or invalid",
                }

            if not self._validate_comparison_data(new_data):
                return {
                    "month": month,
                    "status": "error",
                    "error": "new system data not found or invalid",
                }

            # Type assertion: we know data is not None after validation
            assert current_data is not None
            assert new_data is not None

            # Now we can safely access the data
            comparison_result = self._compare_brush_matches(current_data["data"], new_data["data"])

            # Add metadata
            comparison_result.update(
                {
                    "month": month,
                    "status": "completed",
                    "total_records": len(current_data["data"]),
                    "current_system_metadata": current_data["metadata"],
                    "new_system_metadata": new_data["metadata"],
                }
            )

            return comparison_result

        except Exception as e:
            return {"month": month, "status": "error", "error": str(e)}

    def compare_multiple_months(self, months: List[str]) -> List[Dict[str, Any]]:
        """
        Compare brush matching results for multiple months.

        Args:
            months: List of months in YYYY-MM format

        Returns:
            List of comparison results for each month
        """
        results = []
        for month in months:
            result = self.compare_month(month)
            results.append(result)
        return results

    def generate_comparison_report(self, comparison_results: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable comparison report.

        Args:
            comparison_results: List of comparison results

        Returns:
            Formatted comparison report
        """
        # Calculate overall statistics
        stats = self.get_comparison_statistics(comparison_results)

        # Generate report
        report = []
        report.append("=" * 60)
        report.append("Brush System A/B Comparison Report")
        report.append("=" * 60)
        report.append("")

        # Overall statistics
        report.append("Overall Statistics:")
        report.append(f"  Total Months: {stats['total_months']}")
        report.append(f"  Total Records: {stats['total_records']:,}")
        report.append(f"  Total Agreements: {stats['total_agreements']:,}")
        report.append(f"  Total Disagreements: {stats['total_disagreements']:,}")
        report.append(f"  Average Agreement: {stats['average_agreement_percentage']:.1f}%")
        report.append(f"  Completed Months: {stats['completed_months']}")
        report.append(f"  Error Months: {stats['error_months']}")
        report.append("")

        # Monthly breakdown
        report.append("Monthly Breakdown:")
        report.append("-" * 40)

        for result in comparison_results:
            if result["status"] == "completed":
                report.append(
                    f"  {result['month']}: "
                    f"{result['agreement_percentage']:.1f}% agreement "
                    f"({result['agreement_count']}/{result['total_records']} records)"
                )
            else:
                report.append(f"  {result['month']}: ERROR - {result['error']}")

        report.append("")

        # Disagreement analysis
        completed_results = [r for r in comparison_results if r["status"] == "completed"]
        if completed_results:
            patterns = self.analyze_disagreement_patterns(completed_results)
            report.append("Disagreement Analysis:")
            report.append("-" * 40)
            report.append(f"  Total Disagreements: {patterns['total_disagreements']}")

            if patterns["brand_patterns"]:
                report.append("  Top Disagreement Brands:")
                for brand, count in patterns["brand_patterns"][:5]:
                    report.append(f"    {brand}: {count} disagreements")

            if patterns["model_patterns"]:
                report.append("  Top Disagreement Models:")
                for model, count in patterns["model_patterns"][:5]:
                    report.append(f"    {model}: {count} disagreements")

        return "\n".join(report)

    def analyze_disagreement_patterns(
        self, comparison_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in disagreements between systems.

        Args:
            comparison_results: List of comparison results

        Returns:
            Analysis of disagreement patterns
        """
        brand_patterns = defaultdict(int)
        model_patterns = defaultdict(int)
        total_disagreements = 0

        for result in comparison_results:
            if result["status"] != "completed":
                continue

            total_disagreements += result["disagreement_count"]

            for disagreement in result.get("disagreements", []):
                current_brand = disagreement["current"]["brand"]
                new_brand = disagreement["new"]["brand"]

                if current_brand != new_brand:
                    brand_patterns[current_brand] += 1
                    brand_patterns[new_brand] += 1

                current_model = disagreement["current"]["model"]
                new_model = disagreement["new"]["model"]

                if current_model != new_model:
                    model_patterns[current_model] += 1
                    model_patterns[new_model] += 1

        return {
            "brand_patterns": sorted(brand_patterns.items(), key=lambda x: x[1], reverse=True),
            "model_patterns": sorted(model_patterns.items(), key=lambda x: x[1], reverse=True),
            "total_disagreements": total_disagreements,
        }

    def get_comparison_statistics(self, comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall statistics from comparison results.

        Args:
            comparison_results: List of comparison results

        Returns:
            Overall statistics
        """
        total_months = len(comparison_results)
        total_records = 0
        total_agreements = 0
        total_disagreements = 0
        completed_months = 0
        error_months = 0

        for result in comparison_results:
            if result["status"] == "completed":
                completed_months += 1
                total_records += result["total_records"]
                total_agreements += result["agreement_count"]
                total_disagreements += result["disagreement_count"]
            else:
                error_months += 1

        average_agreement_percentage = (
            (total_agreements / total_records * 100) if total_records > 0 else 0.0
        )

        return {
            "total_months": total_months,
            "total_records": total_records,
            "total_agreements": total_agreements,
            "total_disagreements": total_disagreements,
            "average_agreement_percentage": average_agreement_percentage,
            "completed_months": completed_months,
            "error_months": error_months,
        }

    def _load_system_data(self, month: str, system: str) -> Optional[Dict[str, Any]]:
        """
        Load data for a specific month and system.

        Args:
            month: Month in YYYY-MM format
            system: System name ('current' or 'new')

        Returns:
            Loaded data or None if not found
        """
        try:
            if system == "current":
                file_path = self.current_dir / f"{month}.json"
            else:
                file_path = self.new_dir / f"{month}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception:
            return None

    def _compare_brush_matches(
        self, current_data: List[Dict], new_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compare brush matches between current and new systems.

        Args:
            current_data: Data from current system
            new_data: Data from new system

        Returns:
            Comparison result
        """
        if len(current_data) != len(new_data):
            raise ValueError("Data length mismatch between systems")

        agreement_count = 0
        disagreement_count = 0
        disagreements = []

        for i, (current_record, new_record) in enumerate(zip(current_data, new_data)):
            current_brush = current_record.get("brush", {})
            new_brush = new_record.get("brush", {})

            current_matched = current_brush.get("matched", {})
            new_matched = new_brush.get("matched", {})

            # Compare brush matches
            if self._brush_matches_equal(current_matched, new_matched):
                agreement_count += 1
            else:
                disagreement_count += 1
                disagreements.append(
                    {"record_index": i, "current": current_matched, "new": new_matched}
                )

        agreement_percentage = (agreement_count / len(current_data) * 100) if current_data else 0.0

        return {
            "agreement_count": agreement_count,
            "disagreement_count": disagreement_count,
            "agreement_percentage": agreement_percentage,
            "disagreements": disagreements,
        }

    def _brush_matches_equal(self, current_match: Dict, new_match: Dict) -> bool:
        """
        Compare if two brush matches are equal.

        Args:
            current_match: Match from current system
            new_match: Match from new system

        Returns:
            True if matches are equal, False otherwise
        """
        # Handle None matches
        if current_match is None and new_match is None:
            return True
        if current_match is None or new_match is None:
            return False

        # Compare key fields
        key_fields = ["brand", "model", "fiber", "knot_size_mm", "handle_maker"]

        for field in key_fields:
            current_value = current_match.get(field)
            new_value = new_match.get(field)

            if current_value != new_value:
                return False

        return True

    def _validate_comparison_data(self, data: Optional[Dict[str, Any]]) -> bool:
        """
        Validate comparison data structure.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        if data is None:
            return False

        if "metadata" not in data or "data" not in data:
            return False

        return True

    def _save_test_data(
        self, month: str, current_data: Optional[Dict], new_data: Optional[Dict]
    ) -> None:
        """
        Save test data for testing purposes.

        Args:
            month: Month in YYYY-MM format
            current_data: Current system data
            new_data: New system data
        """
        # Create directories
        self.current_dir.mkdir(parents=True, exist_ok=True)
        self.new_dir.mkdir(parents=True, exist_ok=True)

        # Save current data
        if current_data:
            current_path = self.current_dir / f"{month}.json"
            with open(current_path, "w", encoding="utf-8") as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)

        # Save new data
        if new_data:
            new_path = self.new_dir / f"{month}.json"
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
