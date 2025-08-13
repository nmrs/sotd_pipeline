"""
Unit tests for brush A/B comparison framework.

Tests the framework for comparing old and new brush system outputs.
"""

from pathlib import Path

from sotd.match.brush_comparison_framework import BrushComparisonFramework


class TestBrushComparisonFramework:
    """Test brush A/B comparison framework."""

    def test_init_default_paths(self):
        """Test initialization with default paths."""
        framework = BrushComparisonFramework()

        assert framework.base_path == Path("data")
        assert framework.current_dir == Path("data/matched")
        assert framework.new_dir == Path("data/matched_new")

    def test_init_custom_paths(self):
        """Test initialization with custom paths."""
        custom_base = Path("/custom/data")
        framework = BrushComparisonFramework(base_path=custom_base)

        assert framework.base_path == custom_base
        assert framework.current_dir == custom_base / "matched"
        assert framework.new_dir == custom_base / "matched_new"

    def test_compare_month_both_systems_available(self, tmp_path):
        """Test comparing a month when both systems have data."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test data for both systems
        current_data = {
            "metadata": {"month": "2025-05", "record_count": 100},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}}},
            ],
        }

        new_data = {
            "metadata": {"month": "2025-05", "record_count": 100},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}}},
            ],
        }

        # Save test data
        framework._save_test_data("2025-05", current_data, new_data)

        # Compare
        result = framework.compare_month("2025-05")

        assert result["month"] == "2025-05"
        assert result["total_records"] == 2  # Fixed: test data has 2 records, not 100
        assert result["agreement_count"] == 2
        assert result["disagreement_count"] == 0
        assert result["agreement_percentage"] == 100.0
        assert result["status"] == "completed"

    def test_compare_month_with_disagreements(self, tmp_path):
        """Test comparing a month when systems disagree on some matches."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test data with disagreements
        current_data = {
            "metadata": {"month": "2025-05", "record_count": 3},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}}},
                {"brush": {"matched": {"brand": "Declaration", "model": "B2"}}},
            ],
        }

        new_data = {
            "metadata": {"month": "2025-05", "record_count": 3},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 1"}}},  # Different
                {"brush": {"matched": {"brand": "Declaration", "model": "B2"}}},
            ],
        }

        # Save test data
        framework._save_test_data("2025-05", current_data, new_data)

        # Compare
        result = framework.compare_month("2025-05")

        assert result["month"] == "2025-05"
        assert result["total_records"] == 3
        assert result["agreement_count"] == 2
        assert result["disagreement_count"] == 1
        # Fixed: use approximate comparison for floating-point precision
        assert abs(result["agreement_percentage"] - 66.67) < 0.01
        assert result["status"] == "completed"
        assert len(result["disagreements"]) == 1

    def test_compare_month_missing_current_system(self, tmp_path):
        """Test comparing when current system data is missing."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test data for new system only
        new_data = {
            "metadata": {"month": "2025-05", "record_count": 100},
            "data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}],
        }

        # Save test data
        framework._save_test_data("2025-05", None, new_data)

        # Compare
        result = framework.compare_month("2025-05")

        assert result["month"] == "2025-05"
        assert result["status"] == "error"
        assert "current system data not found" in result["error"]

    def test_compare_month_missing_new_system(self, tmp_path):
        """Test comparing when new system data is missing."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test data for current system only
        current_data = {
            "metadata": {"month": "2025-05", "record_count": 100},
            "data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}],
        }

        # Save test data
        framework._save_test_data("2025-05", current_data, None)

        # Compare
        result = framework.compare_month("2025-05")

        assert result["month"] == "2025-05"
        assert result["status"] == "error"
        assert "new system data not found" in result["error"]

    def test_compare_multiple_months(self, tmp_path):
        """Test comparing multiple months."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        months = ["2025-01", "2025-02", "2025-03"]

        for month in months:
            current_data = {
                "metadata": {"month": month, "record_count": 10},
                "data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}],
            }

            new_data = {
                "metadata": {"month": month, "record_count": 10},
                "data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}],
            }

            framework._save_test_data(month, current_data, new_data)

        # Compare multiple months
        results = framework.compare_multiple_months(months)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"
            assert result["agreement_percentage"] == 100.0

    def test_generate_comparison_report(self, tmp_path):
        """Test generating a comparison report."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test comparison results
        comparison_results = [
            {
                "month": "2025-01",
                "total_records": 100,
                "agreement_count": 95,
                "disagreement_count": 5,
                "agreement_percentage": 95.0,
                "status": "completed",
            },
            {
                "month": "2025-02",
                "total_records": 100,
                "agreement_count": 98,
                "disagreement_count": 2,
                "agreement_percentage": 98.0,
                "status": "completed",
            },
        ]

        # Generate report
        report = framework.generate_comparison_report(comparison_results)

        assert "Brush System A/B Comparison Report" in report
        assert "2025-01" in report
        assert "2025-02" in report
        assert "95.0%" in report
        assert "98.0%" in report
        assert "Total Records: 200" in report

    def test_analyze_disagreement_patterns(self, tmp_path):
        """Test analyzing disagreement patterns."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test data with specific disagreement patterns
        current_data = {
            "metadata": {"month": "2025-05", "record_count": 3},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}}},
                {"brush": {"matched": {"brand": "Declaration", "model": "B2"}}},
            ],
        }

        new_data = {
            "metadata": {"month": "2025-05", "record_count": 3},
            "data": [
                {"brush": {"matched": {"brand": "Omega", "model": "10049"}}},
                {"brush": {"matched": {"brand": "Simpson", "model": "Chubby 1"}}},
                {"brush": {"matched": {"brand": "Declaration", "model": "B3"}}},
            ],
        }

        # Save test data
        framework._save_test_data("2025-05", current_data, new_data)

        # Compare and analyze patterns
        result = framework.compare_month("2025-05")
        patterns = framework.analyze_disagreement_patterns([result])

        assert "brand_patterns" in patterns
        assert "model_patterns" in patterns
        assert "total_disagreements" in patterns
        assert patterns["total_disagreements"] == 2

    def test_get_comparison_statistics(self, tmp_path):
        """Test getting comparison statistics."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Create test comparison results
        comparison_results = [
            {
                "month": "2025-01",
                "total_records": 100,
                "agreement_count": 95,
                "disagreement_count": 5,
                "agreement_percentage": 95.0,
                "status": "completed",
            },
            {
                "month": "2025-02",
                "total_records": 100,
                "agreement_count": 98,
                "disagreement_count": 2,
                "agreement_percentage": 98.0,
                "status": "completed",
            },
        ]

        # Get statistics
        stats = framework.get_comparison_statistics(comparison_results)

        assert stats["total_months"] == 2
        assert stats["total_records"] == 200
        assert stats["total_agreements"] == 193
        assert stats["total_disagreements"] == 7
        assert stats["average_agreement_percentage"] == 96.5
        assert stats["completed_months"] == 2
        assert stats["error_months"] == 0

    def test_validate_comparison_data(self, tmp_path):
        """Test validating comparison data structure."""
        framework = BrushComparisonFramework(base_path=tmp_path)

        # Valid data
        valid_data = {
            "metadata": {"month": "2025-05", "record_count": 100},
            "data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}],
        }

        assert framework._validate_comparison_data(valid_data) is True

        # Invalid data - missing metadata
        invalid_data = {"data": [{"brush": {"matched": {"brand": "Omega", "model": "10049"}}}]}

        assert framework._validate_comparison_data(invalid_data) is False

        # Invalid data - missing data
        invalid_data2 = {"metadata": {"month": "2025-05", "record_count": 100}}

        assert framework._validate_comparison_data(invalid_data2) is False
