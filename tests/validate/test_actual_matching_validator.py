"""
Tests for ActualMatchingValidator.

This module tests the actual matching validation functionality for all field types.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from sotd.validate.actual_matching_validator import (
    ActualMatchingValidator,
    ValidationIssue,
    ValidationResult,
)


class TestActualMatchingValidator:
    """Test cases for ActualMatchingValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ActualMatchingValidator(data_path=Path("data"))
        self.mock_correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "razor": {"Koraat": {"Moarteen": ["koraat moarteen"]}},
            "blade": {"Feather": {"ProGuard": ["feather proguard"]}},
            "soap": {"Barrister and Mann": {"Adagio": ["barrister & mann - adagio"]}},
        }

    def test_init(self):
        """Test validator initialization."""
        validator = ActualMatchingValidator()
        assert validator.data_path == Path("data")
        assert validator._matchers == {}
        assert validator._correct_matches_checker is None

    def test_init_with_custom_data_path(self):
        """Test validator initialization with custom data path."""
        custom_path = Path("/custom/data")
        validator = ActualMatchingValidator(data_path=custom_path)
        assert validator.data_path == custom_path

    def test_get_matcher_brush(self):
        """Test getting brush matcher."""
        matcher = self.validator._get_matcher("brush")
        assert matcher is not None
        assert "brush" in self.validator._matchers

    def test_get_matcher_razor(self):
        """Test getting razor matcher."""
        matcher = self.validator._get_matcher("razor")
        assert matcher is not None
        assert "razor" in self.validator._matchers

    def test_get_matcher_blade(self):
        """Test getting blade matcher."""
        matcher = self.validator._get_matcher("blade")
        assert matcher is not None
        assert "blade" in self.validator._matchers

    def test_get_matcher_soap(self):
        """Test getting soap matcher."""
        matcher = self.validator._get_matcher("soap")
        assert matcher is not None
        assert "soap" in self.validator._matchers

    def test_get_matcher_unsupported_field(self):
        """Test getting matcher for unsupported field."""
        with pytest.raises(ValueError, match="Unsupported field type"):
            self.validator._get_matcher("unsupported")

    def test_validate_data_structure_duplicate_strings(self):
        """Test data structure validation for duplicate strings."""
        correct_matches = {
            "brush": {
                "AP Shave Co": {
                    "Mixed Badger/Boar": [
                        "ap shaveco 24mm luxury mixed knot",
                        "ap shaveco 24mm luxury mixed knot",  # Duplicate
                    ]
                }
            }
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        assert issues[0].issue_type == "duplicate_string"
        assert issues[0].severity == "low"
        assert "ap shaveco 24mm luxury mixed knot" in issues[0].correct_match

    def test_validate_data_structure_cross_section_conflict(self):
        """Test data structure validation for cross-section conflicts."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "handle": {
                "AP Shave Co": {"Unspecified": ["ap shaveco 24mm luxury mixed knot"]}  # Conflict
            },
        }

        issues = self.validator._validate_data_structure(correct_matches)

        assert len(issues) == 1
        assert issues[0].issue_type == "cross_section_conflict"
        assert issues[0].severity == "high"
        assert "ap shaveco 24mm luxury mixed knot" in issues[0].correct_match

    def test_validate_data_structure_no_issues(self):
        """Test data structure validation with no issues."""
        correct_matches = {
            "brush": {"AP Shave Co": {"Mixed Badger/Boar": ["ap shaveco 24mm luxury mixed knot"]}},
            "handle": {
                "Chisel & Hound": {
                    "Unspecified": ["chisel & hound tahitian pearl 26mm maggard shd"]
                }
            },
            "knot": {"Maggard": {"Badger": ["chisel & hound tahitian pearl 26mm maggard shd"]}},
        }

        issues = self.validator._validate_data_structure(correct_matches)
        assert len(issues) == 0

    @patch("sotd.validate.actual_matching_validator.BrushMatcher")
    def test_validate_brush_entry_no_match(self, mock_brush_matcher_class):
        """Test brush entry validation when no match is found."""
        mock_matcher = Mock()
        mock_matcher.match.return_value = None
        mock_brush_matcher_class.return_value = mock_matcher

        expected_data = {"brand": "AP Shave Co", "model": "Mixed Badger/Boar"}
        issues = self.validator._validate_brush_entry(
            "ap shaveco 24mm luxury mixed knot", expected_data, "brush"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "no_match"
        assert issues[0].severity == "high"
        assert "ap shaveco 24mm luxury mixed knot" in issues[0].correct_match

    @patch("sotd.validate.actual_matching_validator.BrushMatcher")
    def test_validate_brush_entry_data_mismatch(self, mock_brush_matcher_class):
        """Test brush entry validation when data doesn't match."""
        mock_matcher = Mock()
        mock_result = Mock()
        mock_result.matched = {
            "brand": "AP Shave Co",
            "model": "Luxury Mixed",  # Different from expected
        }
        mock_matcher.match.return_value = mock_result
        mock_brush_matcher_class.return_value = mock_matcher

        expected_data = {"brand": "AP Shave Co", "model": "Mixed Badger/Boar"}
        issues = self.validator._validate_brush_entry(
            "ap shaveco 24mm luxury mixed knot", expected_data, "brush"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "data_mismatch"
        assert issues[0].severity == "high"
        assert issues[0].expected_model == "Mixed Badger/Boar"
        assert issues[0].actual_model == "Luxury Mixed"

    @patch("sotd.validate.actual_matching_validator.BrushMatcher")
    def test_validate_brush_entry_structural_change(self, mock_brush_matcher_class):
        """Test brush entry validation when structural type changes."""
        mock_matcher = Mock()
        mock_result = Mock()
        mock_result.matched = {
            "handle": {"brand": "AP Shave Co", "model": "Luxury Mixed"},
            "knot": {"brand": "AP Shave Co", "model": "Mixed Badger/Boar"},
        }
        mock_matcher.match.return_value = mock_result
        mock_brush_matcher_class.return_value = mock_matcher

        expected_data = {"brand": "AP Shave Co", "model": "Mixed Badger/Boar"}
        issues = self.validator._validate_brush_entry(
            "ap shaveco 24mm luxury mixed knot", expected_data, "brush"
        )

        # Should have structural change issue
        structural_issues = [i for i in issues if i.issue_type == "structural_change"]
        assert len(structural_issues) == 1
        assert structural_issues[0].severity == "high"
        assert structural_issues[0].expected_section == "brush"
        assert structural_issues[0].actual_section == "handle_knot"

    @patch("sotd.validate.actual_matching_validator.RazorMatcher")
    def test_validate_simple_entry_no_match(self, mock_razor_matcher_class):
        """Test simple entry validation when no match is found."""
        mock_matcher = Mock()
        mock_matcher.match.return_value = None
        mock_razor_matcher_class.return_value = mock_matcher

        issues = self.validator._validate_simple_entry(
            "razor", "koraat moarteen", "Koraat", "Moarteen"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "no_match"
        assert issues[0].severity == "high"
        assert "koraat moarteen" in issues[0].correct_match

    @patch("sotd.validate.actual_matching_validator.RazorMatcher")
    def test_validate_simple_entry_data_mismatch(self, mock_razor_matcher_class):
        """Test simple entry validation when data doesn't match."""
        mock_matcher = Mock()
        mock_result = Mock()
        mock_result.matched = {
            "brand": "Koraat",
            "model": "Different Model",  # Different from expected
        }
        mock_matcher.match.return_value = mock_result
        mock_razor_matcher_class.return_value = mock_matcher

        issues = self.validator._validate_simple_entry(
            "razor", "koraat moarteen", "Koraat", "Moarteen"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "data_mismatch"
        assert issues[0].severity == "high"
        assert issues[0].expected_model == "Moarteen"
        assert issues[0].actual_model == "Different Model"

    @patch("yaml.safe_load")
    @patch("sotd.validate.actual_matching_validator.BrushMatcher")
    def test_validate_brush_field(self, mock_brush_matcher_class, mock_yaml_load):
        """Test validation for brush field."""
        mock_yaml_load.return_value = self.mock_correct_matches

        mock_matcher = Mock()
        mock_result = Mock()
        mock_result.matched = {"brand": "AP Shave Co", "model": "Mixed Badger/Boar"}
        mock_matcher.match.return_value = mock_result
        mock_brush_matcher_class.return_value = mock_matcher

        result = self.validator.validate("brush")

        assert isinstance(result, ValidationResult)
        assert result.field == "brush"
        assert result.validation_mode == "actual_matching"
        assert result.total_entries == 1
        assert len(result.issues) == 0  # No issues since data matches

    @patch("yaml.safe_load")
    @patch("sotd.validate.actual_matching_validator.RazorMatcher")
    def test_validate_razor_field(self, mock_razor_matcher_class, mock_yaml_load):
        """Test validation for razor field."""
        mock_yaml_load.return_value = self.mock_correct_matches

        mock_matcher = Mock()
        mock_result = Mock()
        mock_result.matched = {"brand": "Koraat", "model": "Moarteen"}
        mock_matcher.match.return_value = mock_result
        mock_razor_matcher_class.return_value = mock_matcher

        result = self.validator.validate("razor")

        assert isinstance(result, ValidationResult)
        assert result.field == "razor"
        assert result.validation_mode == "actual_matching"
        assert result.total_entries == 1
        assert len(result.issues) == 0  # No issues since data matches

    def test_validation_issue_creation(self):
        """Test ValidationIssue creation and properties."""
        issue = ValidationIssue(
            issue_type="data_mismatch",
            severity="high",
            correct_match="test string",
            expected_brand="Expected Brand",
            expected_model="Expected Model",
            actual_brand="Actual Brand",
            actual_model="Actual Model",
            details="Test details",
            suggested_action="Test action",
        )

        assert issue.issue_type == "data_mismatch"
        assert issue.severity == "high"
        assert issue.correct_match == "test string"
        assert issue.expected_brand == "Expected Brand"
        assert issue.expected_model == "Expected Model"
        assert issue.actual_brand == "Actual Brand"
        assert issue.actual_model == "Actual Model"
        assert issue.details == "Test details"
        assert issue.suggested_action == "Test action"

    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties."""
        issues = [
            ValidationIssue("data_mismatch", "high", "test string"),
            ValidationIssue("no_match", "medium", "test string 2"),
        ]

        result = ValidationResult(
            field="brush",
            total_entries=10,
            issues=issues,
            processing_time=1.5,
            validation_mode="actual_matching",
            strategy_stats={"strategy1": 5, "strategy2": 3},
            performance_metrics={"memory_usage": "100MB"},
        )

        assert result.field == "brush"
        assert result.total_entries == 10
        assert len(result.issues) == 2
        assert result.processing_time == 1.5
        assert result.validation_mode == "actual_matching"
        assert result.strategy_stats == {"strategy1": 5, "strategy2": 3}
        assert result.performance_metrics == {"memory_usage": "100MB"}

    def test_validation_result_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult(field="razor", total_entries=5, issues=[], processing_time=0.5)

        assert result.field == "razor"
        assert result.total_entries == 5
        assert len(result.issues) == 0
        assert result.processing_time == 0.5
        assert result.validation_mode == "actual_matching"
        assert result.strategy_stats == {}
        assert result.performance_metrics == {}


class TestValidationIssue:
    """Test cases for ValidationIssue class."""

    def test_validation_issue_minimal(self):
        """Test ValidationIssue with minimal required fields."""
        issue = ValidationIssue(
            issue_type="test_issue", severity="low", correct_match="test string"
        )

        assert issue.issue_type == "test_issue"
        assert issue.severity == "low"
        assert issue.correct_match == "test string"
        assert issue.expected_brand is None
        assert issue.actual_brand is None

    def test_validation_issue_complete(self):
        """Test ValidationIssue with all fields."""
        issue = ValidationIssue(
            issue_type="data_mismatch",
            severity="high",
            correct_match="test string",
            expected_brand="Expected Brand",
            expected_model="Expected Model",
            actual_brand="Actual Brand",
            actual_model="Actual Model",
            expected_handle_brand="Expected Handle Brand",
            expected_handle_model="Expected Handle Model",
            actual_handle_brand="Actual Handle Brand",
            actual_handle_model="Actual Handle Model",
            expected_knot_brand="Expected Knot Brand",
            expected_knot_model="Expected Knot Model",
            actual_knot_brand="Actual Knot Brand",
            actual_knot_model="Actual Knot Model",
            expected_section="brush",
            actual_section="handle_knot",
            details="Test details",
            suggested_action="Test action",
        )

        assert issue.issue_type == "data_mismatch"
        assert issue.severity == "high"
        assert issue.correct_match == "test string"
        assert issue.expected_brand == "Expected Brand"
        assert issue.expected_model == "Expected Model"
        assert issue.actual_brand == "Actual Brand"
        assert issue.actual_model == "Actual Model"
        assert issue.expected_handle_brand == "Expected Handle Brand"
        assert issue.expected_handle_model == "Expected Handle Model"
        assert issue.actual_handle_brand == "Actual Handle Brand"
        assert issue.actual_handle_model == "Actual Handle Model"
        assert issue.expected_knot_brand == "Expected Knot Brand"
        assert issue.expected_knot_model == "Expected Knot Model"
        assert issue.actual_knot_brand == "Actual Knot Brand"
        assert issue.actual_knot_model == "Actual Knot Model"
        assert issue.expected_section == "brush"
        assert issue.actual_section == "handle_knot"
        assert issue.details == "Test details"
        assert issue.suggested_action == "Test action"
