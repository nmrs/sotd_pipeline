"""
Tests for brush system comparator.

This module tests the brush system comparator for Phase 2 Step 7
of the multi-strategy scoring system implementation.
"""

import pytest

from sotd.match.brush_system_comparator import BrushSystemComparator


class TestBrushSystemComparator:
    """Test brush system comparator."""

    def test_comparator_initialization(self):
        """Test that comparator initializes correctly."""
        old_data = {"data": [], "metadata": {}}
        new_data = {"data": [], "metadata": {}}

        comparator = BrushSystemComparator(old_data, new_data)
        assert comparator.old_data == old_data
        assert comparator.new_data == new_data
        assert comparator.comparison_results == {}

    def test_compare_matches_identical_data(self):
        """Test comparison with identical data."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Test", "model": "Brush", "fiber": "badger"},
                        "match_type": "exact",
                        "pattern": "test_pattern",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Test", "model": "Brush", "fiber": "badger"},
                        "match_type": "exact",
                        "pattern": "test_pattern",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert results["total_records"] == 1
        assert results["matching_results"] == 1
        assert results["different_results"] == 0
        assert results["old_only_matches"] == 0
        assert results["new_only_matches"] == 0
        assert results["both_unmatched"] == 0

    def test_compare_matches_different_data(self):
        """Test comparison with different data."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Old", "model": "Brush", "fiber": "badger"},
                        "match_type": "exact",
                        "pattern": "old_pattern",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "New", "model": "Brush", "fiber": "badger"},
                        "match_type": "regex",
                        "pattern": "new_pattern",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert results["total_records"] == 1
        assert results["matching_results"] == 0
        assert results["different_results"] == 1
        assert results["old_only_matches"] == 0
        assert results["new_only_matches"] == 0
        assert results["both_unmatched"] == 0

    def test_compare_matches_old_only(self):
        """Test comparison where only old system matches."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Test", "model": "Brush", "fiber": "badger"},
                        "match_type": "exact",
                        "pattern": "test_pattern",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": None,
                        "match_type": None,
                        "pattern": None,
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert results["total_records"] == 1
        assert results["matching_results"] == 0
        assert results["different_results"] == 0
        assert results["old_only_matches"] == 1
        assert results["new_only_matches"] == 0
        assert results["both_unmatched"] == 0

    def test_compare_matches_new_only(self):
        """Test comparison where only new system matches."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": None,
                        "match_type": None,
                        "pattern": None,
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Test", "model": "Brush", "fiber": "badger"},
                        "match_type": "exact",
                        "pattern": "test_pattern",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert results["total_records"] == 1
        assert results["matching_results"] == 0
        assert results["different_results"] == 0
        assert results["old_only_matches"] == 0
        assert results["new_only_matches"] == 1
        assert results["both_unmatched"] == 0

    def test_compare_matches_both_unmatched(self):
        """Test comparison where both systems fail to match."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Unknown Brush",
                        "matched": None,
                        "match_type": None,
                        "pattern": None,
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Unknown Brush",
                        "matched": None,
                        "match_type": None,
                        "pattern": None,
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert results["total_records"] == 1
        assert results["matching_results"] == 0
        assert results["different_results"] == 0
        assert results["old_only_matches"] == 0
        assert results["new_only_matches"] == 0
        assert results["both_unmatched"] == 1

    def test_record_count_mismatch(self):
        """Test that record count mismatch raises error."""
        old_data = {"data": [{"brush": {}}], "metadata": {}}
        new_data = {"data": [{"brush": {}}, {"brush": {}}], "metadata": {}}

        comparator = BrushSystemComparator(old_data, new_data)

        with pytest.raises(ValueError, match="Record count mismatch"):
            comparator.compare_matches()

    def test_generate_report(self):
        """Test report generation."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Old", "model": "Brush"},
                        "match_type": "exact",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "New", "model": "Brush"},
                        "match_type": "regex",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        report = comparator.generate_report()

        assert "summary" in report
        assert "match_type_changes" in report
        assert "detailed_differences" in report
        assert "total_differences" in report

        summary = report["summary"]
        assert summary["total_records"] == 1
        assert summary["different_results"]["count"] == 1
        assert summary["different_results"]["percentage"] == 100.0

    def test_identify_differences(self):
        """Test difference identification."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Old", "model": "Brush"},
                        "match_type": "exact",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "New", "model": "Brush"},
                        "match_type": "regex",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        differences = comparator.identify_differences()

        assert len(differences) == 1
        difference = differences[0]
        assert difference["record_index"] == 0
        assert difference["input_text"] == "Test Brush"
        assert difference["old_match"]["brand"] == "Old"
        assert difference["new_match"]["brand"] == "New"

    def test_get_performance_comparison(self):
        """Test performance comparison."""
        old_data = {
            "data": [],
            "metadata": {
                "performance": {"total_time": 10.0, "processing_time": 8.0, "file_io_time": 2.0}
            },
        }
        new_data = {
            "data": [],
            "metadata": {
                "performance": {"total_time": 12.0, "processing_time": 10.0, "file_io_time": 2.0}
            },
        }

        comparator = BrushSystemComparator(old_data, new_data)
        performance = comparator.get_performance_comparison()

        assert "old_system_performance" in performance
        assert "new_system_performance" in performance
        assert "performance_differences" in performance

        differences = performance["performance_differences"]
        assert "total_time" in differences
        assert differences["total_time"]["difference"] == 2.0
        assert differences["total_time"]["percentage_change"] == 20.0

    def test_get_statistical_summary(self):
        """Test statistical summary generation."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Old", "model": "Brush"},
                        "match_type": "exact",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "New", "model": "Brush"},
                        "match_type": "regex",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        summary = comparator.get_statistical_summary()

        assert summary["total_records"] == 1
        assert summary["agreement_rate"] == 0.0
        assert summary["disagreement_rate"] == 100.0
        # No old_only_matches, only different_results
        assert summary["old_system_success_rate"] == 0.0
        # No new_only_matches, only different_results
        assert summary["new_system_success_rate"] == 0.0
        assert "difference_categories" in summary

    def test_save_comparison_report(self, tmp_path):
        """Test saving comparison report to file."""
        old_data = {"data": [], "metadata": {}}
        new_data = {"data": [], "metadata": {}}

        comparator = BrushSystemComparator(old_data, new_data)
        output_path = tmp_path / "comparison_report.json"

        comparator.save_comparison_report(output_path)

        assert output_path.exists()

        # Verify file contains valid JSON
        with open(output_path, "r") as f:
            import json

            report = json.load(f)
            assert "summary" in report

    def test_match_type_changes_tracking(self):
        """Test that match type changes are tracked correctly."""
        old_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "Old", "model": "Brush"},
                        "match_type": "exact",
                        "pattern": "exact_pattern",
                    }
                }
            ],
            "metadata": {},
        }
        new_data = {
            "data": [
                {
                    "brush": {
                        "original": "Test Brush",
                        "matched": {"brand": "New", "model": "Brush"},
                        "match_type": "regex",
                        "pattern": "regex_pattern",
                    }
                }
            ],
            "metadata": {},
        }

        comparator = BrushSystemComparator(old_data, new_data)
        results = comparator.compare_matches()

        assert "exact_to_regex" in results["match_type_changes"]
        assert results["match_type_changes"]["exact_to_regex"] == 1
