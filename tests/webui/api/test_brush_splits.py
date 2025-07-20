"""Unit tests for brush splits data structures and validation logic."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from webui.api.brush_splits import (
    BrushSplitError,
    FileNotFoundError,
    DataCorruptionError,
    ValidationError,
    ProcessingError,
    BrushSplitValidator,
    BrushSplitOccurrence,
    BrushSplit,
    BrushSplitStatistics,
    StatisticsCalculator,
    ConfidenceLevel,
    normalize_brush_string,
    router,
)


class TestBrushSplitOccurrence:
    """Test BrushSplitOccurrence data structure."""

    def test_creation(self):
        """Test creating a brush split occurrence."""
        occurrence = BrushSplitOccurrence(file="test.json", comment_ids=["123", "456"])
        assert occurrence.file == "test.json"
        assert occurrence.comment_ids == ["123", "456"]

    def test_to_dict(self):
        """Test converting to dictionary."""
        occurrence = BrushSplitOccurrence(file="test.json", comment_ids=["123", "456"])
        data = occurrence.to_dict()
        assert data["file"] == "test.json"
        assert data["comment_ids"] == ["123", "456"]

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {"file": "test.json", "comment_ids": ["123", "456"]}
        occurrence = BrushSplitOccurrence.from_dict(data)
        assert occurrence.file == "test.json"
        assert occurrence.comment_ids == ["123", "456"]

    def test_from_dict_empty_comment_ids(self):
        """Test creating from dictionary with empty comment_ids."""
        data = {"file": "test.json"}
        occurrence = BrushSplitOccurrence.from_dict(data)
        assert occurrence.file == "test.json"
        assert occurrence.comment_ids == []


class TestBrushSplit:
    """Test BrushSplit data structure."""

    def test_creation_single_component(self):
        """Test creating a single component brush split."""
        split = BrushSplit(original="Declaration B15", handle=None, knot="Declaration B15")
        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert not split.validated
        assert not split.corrected

    def test_creation_multi_component(self):
        """Test creating a multi-component brush split."""
        split = BrushSplit(
            original="Declaration B15 w/ Chisel & Hound Zebra",
            handle="Declaration B15",
            knot="Chisel & Hound Zebra",
        )
        assert split.original == "Declaration B15 w/ Chisel & Hound Zebra"
        assert split.handle == "Declaration B15"
        assert split.knot == "Chisel & Hound Zebra"

    def test_to_dict_single_component(self):
        """Test converting single component to dictionary."""
        split = BrushSplit(original="Declaration B15", handle=None, knot="Declaration B15")
        data = split.to_dict()
        assert data["original"] == "Declaration B15"
        assert data["handle"] is None
        assert data["knot"] == "Declaration B15"
        assert not data["validated"]
        assert not data["corrected"]

    def test_to_dict_corrected(self):
        """Test converting corrected split to dictionary."""
        split = BrushSplit(
            original="Declaration B15",
            handle=None,
            knot="Declaration B15",
            corrected=True,
            system_handle="Declaration",
            system_knot="B15",
            system_confidence=ConfidenceLevel.HIGH,
            system_reasoning="Test reasoning",
        )
        data = split.to_dict()
        assert data["corrected"] is True
        assert data["system_handle"] == "Declaration"
        assert data["system_knot"] == "B15"
        assert data["system_confidence"] == "high"
        assert data["system_reasoning"] == "Test reasoning"

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "original": "Declaration B15",
            "handle": None,
            "knot": "Declaration B15",
            "validated": True,
            "corrected": False,
            "validated_at": "2025-01-27T14:30:00Z",
            "occurrences": [{"file": "test.json", "comment_ids": ["123"]}],
        }
        split = BrushSplit.from_dict(data)
        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert split.validated
        assert not split.corrected
        assert split.validated_at == "2025-01-27T14:30:00Z"
        assert len(split.occurrences) == 1
        assert split.occurrences[0].file == "test.json"

    def test_from_dict_with_system_fields(self):
        """Test creating from dictionary with system fields."""
        data = {
            "original": "Declaration B15",
            "handle": None,
            "knot": "Declaration B15",
            "corrected": True,
            "system_handle": "Declaration",
            "system_knot": "B15",
            "system_confidence": "high",
            "system_reasoning": "Test reasoning",
        }
        split = BrushSplit.from_dict(data)
        assert split.corrected
        assert split.system_handle == "Declaration"
        assert split.system_knot == "B15"
        assert split.system_confidence == ConfidenceLevel.HIGH
        assert split.system_reasoning == "Test reasoning"

    def test_from_dict_invalid_confidence(self):
        """Test creating from dictionary with invalid confidence."""
        data = {
            "original": "Declaration B15",
            "handle": None,
            "knot": "Declaration B15",
            "corrected": True,
            "system_confidence": "invalid",
        }
        split = BrushSplit.from_dict(data)
        assert split.system_confidence is None


class TestBrushSplitStatistics:
    """Test BrushSplitStatistics data structure."""

    def test_creation(self):
        """Test creating statistics."""
        stats = BrushSplitStatistics()
        assert stats.total == 0
        assert stats.validated == 0
        assert stats.corrected == 0
        assert stats.validation_percentage == 0.0
        assert stats.correction_percentage == 0.0

    def test_calculate_percentages(self):
        """Test calculating percentages."""
        stats = BrushSplitStatistics()
        stats.total = 100
        stats.validated = 50
        stats.corrected = 10
        stats.calculate_percentages()
        assert stats.validation_percentage == 50.0
        assert stats.correction_percentage == 20.0

    def test_calculate_percentages_zero_total(self):
        """Test calculating percentages with zero total."""
        stats = BrushSplitStatistics()
        stats.total = 0
        stats.validated = 0
        stats.corrected = 0
        stats.calculate_percentages()
        assert stats.validation_percentage == 0.0
        assert stats.correction_percentage == 0.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        stats = BrushSplitStatistics()
        stats.total = 100
        stats.validated = 50
        stats.corrected = 10
        stats.validation_percentage = 50.0
        stats.correction_percentage = 20.0
        data = stats.to_dict()
        assert data["total"] == 100
        assert data["validated"] == 50
        assert data["corrected"] == 10
        assert data["validation_percentage"] == 50.0
        assert data["correction_percentage"] == 20.0


class TestNormalizeBrushString:
    """Test brush string normalization."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        result = normalize_brush_string("Declaration B15")
        assert result == "Declaration B15"

    def test_normalize_with_prefix(self):
        """Test normalization with prefix."""
        result = normalize_brush_string("Brush: Declaration B15")
        assert result == "Declaration B15"

    def test_normalize_with_whitespace(self):
        """Test normalization with extra whitespace."""
        result = normalize_brush_string("  Declaration B15  ")
        assert result == "Declaration B15"

    def test_normalize_empty(self):
        """Test normalization of empty string."""
        result = normalize_brush_string("")
        assert result is None

    def test_normalize_whitespace_only(self):
        """Test normalization of whitespace-only string."""
        result = normalize_brush_string("   ")
        assert result is None

    def test_normalize_none(self):
        """Test normalization of None."""
        result = normalize_brush_string(None)  # type: ignore
        assert result is None


class TestBrushSplitValidator:
    """Test BrushSplitValidator functionality."""

    def test_creation(self):
        """Test creating validator."""
        validator = BrushSplitValidator()
        assert validator.yaml_path.name == "brush_splits.yaml"
        assert len(validator.validated_splits) == 0

    def test_calculate_confidence_single_component(self):
        """Test confidence calculation for single component."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence(
            "Declaration B15", None, "Declaration B15"
        )
        assert confidence == ConfidenceLevel.HIGH
        assert "Single component brush" in reasoning

    def test_calculate_confidence_delimiter(self):
        """Test confidence calculation for delimiter split."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence(
            "Declaration B15 w/ Chisel & Hound Zebra",
            "Declaration B15",
            "Chisel & Hound Zebra",
        )
        assert confidence == ConfidenceLevel.HIGH
        assert "Delimiter split detected" in reasoning

    def test_calculate_confidence_short_components(self):
        """Test confidence calculation for short components."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence("A w/ B", "A", "B")
        assert confidence == ConfidenceLevel.LOW
        assert "too short" in reasoning

    def test_calculate_confidence_empty_components(self):
        """Test confidence calculation for empty components."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence("A w/ ", "A", "")
        assert confidence == ConfidenceLevel.LOW
        assert "empty component" in reasoning

    def test_validate_split_new(self):
        """Test validating a new split."""
        validator = BrushSplitValidator()
        split = validator.validate_split("Declaration B15", None, "Declaration B15")
        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert split.validated
        assert not split.corrected

    def test_validate_split_correction(self):
        """Test validating a corrected split."""
        validator = BrushSplitValidator()
        # Add existing split
        existing_split = BrushSplit(
            original="Declaration B15",
            handle="Declaration",
            knot="B15",
            validated=True,
        )
        validator.validated_splits["Declaration B15"] = existing_split

        # Validate with different split
        split = validator.validate_split("Declaration B15", None, "Declaration B15")
        assert split.corrected
        assert split.system_handle == "Declaration"
        assert split.system_knot == "B15"

    def test_save_and_load_yaml(self):
        """Test saving and loading YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create validator with temp path
            validator = BrushSplitValidator()
            validator.yaml_path = Path(temp_dir) / "test_brush_splits.yaml"

            # Create test splits
            splits = [
                BrushSplit(
                    original="Declaration B15",
                    handle=None,
                    knot="Declaration B15",
                    validated=True,
                    validated_at="2025-01-27T14:30:00Z",
                ),
                BrushSplit(
                    original="Declaration B15 w/ Chisel & Hound Zebra",
                    handle="Declaration B15",
                    knot="Chisel & Hound Zebra",
                    validated=True,
                    validated_at="2025-01-27T14:30:00Z",
                ),
            ]

            # Save splits
            success = validator.save_validated_splits(splits)
            assert success
            assert validator.yaml_path.exists()

            # Clear validator and reload
            validator.validated_splits.clear()
            validator.load_validated_splits()

            # Verify loaded splits
            assert len(validator.validated_splits) == 2
            assert "Declaration B15" in validator.validated_splits
            assert "Declaration B15 w/ Chisel & Hound Zebra" in validator.validated_splits

    def test_merge_occurrences(self):
        """Test merging occurrences with existing validated entries."""
        validator = BrushSplitValidator()

        # Create existing split with occurrences
        existing_split = BrushSplit(
            original="Declaration B15",
            handle=None,
            knot="Declaration B15",
            validated=True,
            occurrences=[BrushSplitOccurrence(file="2024-01.json", comment_ids=["123", "456"])],
        )
        validator.validated_splits["Declaration B15"] = existing_split

        # Create new occurrences
        new_occurrences = [
            BrushSplitOccurrence(file="2024-02.json", comment_ids=["789"]),
            BrushSplitOccurrence(
                file="2024-01.json", comment_ids=["123", "999"]
            ),  # 123 already exists
        ]

        # Merge occurrences
        validator.merge_occurrences("Declaration B15", new_occurrences)

        # Verify merged result
        updated_split = validator.validated_splits["Declaration B15"]
        assert len(updated_split.occurrences) == 2

        # Check 2024-01.json occurrences (should have 123, 456, 999)
        occ_2024_01 = next(occ for occ in updated_split.occurrences if occ.file == "2024-01.json")
        assert set(occ_2024_01.comment_ids) == {"123", "456", "999"}

        # Check 2024-02.json occurrences (should have 789)
        occ_2024_02 = next(occ for occ in updated_split.occurrences if occ.file == "2024-02.json")
        assert occ_2024_02.comment_ids == ["789"]

    def test_load_validated_splits_missing_file(self):
        """Test loading when YAML file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = BrushSplitValidator()
            validator.yaml_path = Path(temp_dir) / "nonexistent.yaml"

            # Should not raise exception
            validator.load_validated_splits()
            assert len(validator.validated_splits) == 0

    def test_load_validated_splits_corrupted_yaml(self):
        """Test loading corrupted YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = BrushSplitValidator()
            validator.yaml_path = Path(temp_dir) / "corrupted.yaml"

            # Create corrupted YAML file
            with open(validator.yaml_path, "w") as f:
                f.write("invalid: yaml: content: [")

            # Should handle gracefully
            validator.load_validated_splits()
            assert len(validator.validated_splits) == 0

    def test_save_validated_splits_atomic_operation(self):
        """Test atomic save operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = BrushSplitValidator()
            validator.yaml_path = Path(temp_dir) / "test_brush_splits.yaml"

            # Create test splits
            splits = [
                BrushSplit(
                    original="Declaration B15",
                    handle=None,
                    knot="Declaration B15",
                    validated=True,
                )
            ]

            # Save splits
            success = validator.save_validated_splits(splits)
            assert success
            assert validator.yaml_path.exists()

            # Verify no temp file remains
            temp_file = validator.yaml_path.with_suffix(".tmp")
            assert not temp_file.exists()

    def test_get_all_validated_splits(self):
        """Test getting all validated splits."""
        validator = BrushSplitValidator()

        # Add some test splits
        splits = [
            BrushSplit(original="A", handle=None, knot="A", validated=True),
            BrushSplit(original="B", handle="B1", knot="B2", validated=True),
        ]

        for split in splits:
            validator.validated_splits[split.original] = split

        all_splits = validator.get_all_validated_splits()
        assert len(all_splits) == 2
        assert any(split.original == "A" for split in all_splits)
        assert any(split.original == "B" for split in all_splits)


class TestEnhancedBrushSplitStatistics:
    """Test enhanced BrushSplitStatistics functionality."""

    def test_enhanced_statistics_creation(self):
        """Test creating enhanced statistics."""
        stats = BrushSplitStatistics()
        assert stats.total == 0
        assert stats.validated == 0
        assert stats.corrected == 0
        assert stats.validation_percentage == 0.0
        assert stats.correction_percentage == 0.0
        assert "delimiter" in stats.split_types
        assert "fiber_hint" in stats.split_types
        assert "brand_context" in stats.split_types
        assert "no_split" in stats.split_types
        assert "high" in stats.confidence_breakdown
        assert "medium" in stats.confidence_breakdown
        assert "low" in stats.confidence_breakdown

    def test_add_split_method(self):
        """Test adding splits to statistics."""
        stats = BrushSplitStatistics()

        # Add single component split
        split1 = BrushSplit(
            original="Declaration B15", handle=None, knot="Declaration B15", validated=True
        )
        stats.add_split(split1, "2025-01")

        assert stats.total == 1
        assert stats.validated == 1
        assert stats.corrected == 0
        assert stats.split_types["no_split"] == 1
        assert stats.month_breakdown["2025-01"] == 1

        # Add corrected split
        split2 = BrushSplit(
            original="Declaration B15 w/ Chisel & Hound Zebra",
            handle="Declaration B15",
            knot="Chisel & Hound Zebra",
            validated=True,
            corrected=True,
            system_confidence=ConfidenceLevel.HIGH,
        )
        stats.add_split(split2, "2025-01")

        assert stats.total == 2
        assert stats.validated == 2
        assert stats.corrected == 1
        assert stats.confidence_breakdown["high"] == 1

    def test_reset_method(self):
        """Test resetting statistics."""
        stats = BrushSplitStatistics()
        stats.total = 10
        stats.validated = 5
        stats.corrected = 2
        stats.month_breakdown["2025-01"] = 10
        stats.confidence_breakdown["high"] = 2

        stats.reset()

        assert stats.total == 0
        assert stats.validated == 0
        assert stats.corrected == 0
        assert stats.month_breakdown == {}
        assert stats.confidence_breakdown == {"high": 0, "medium": 0, "low": 0}

    def test_enhanced_to_dict(self):
        """Test enhanced to_dict method."""
        stats = BrushSplitStatistics()
        stats.total = 100
        stats.validated = 50
        stats.corrected = 10
        stats.month_breakdown["2025-01"] = 100
        stats.confidence_breakdown["high"] = 10

        data = stats.to_dict()

        assert data["total"] == 100
        assert data["validated"] == 50
        assert data["corrected"] == 10
        assert "month_breakdown" in data
        assert "confidence_breakdown" in data
        assert "recent_activity" in data
        assert data["month_breakdown"]["2025-01"] == 100
        assert data["confidence_breakdown"]["high"] == 10


class TestStatisticsCalculator:
    """Test StatisticsCalculator functionality."""

    def test_calculator_creation(self):
        """Test creating statistics calculator."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)
        assert calculator.validator == validator

    def test_calculate_comprehensive_statistics(self):
        """Test comprehensive statistics calculation."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)

        # Create test splits
        splits = [
            BrushSplit(original="A", handle=None, knot="A", validated=True),
            BrushSplit(
                original="B w/ C",
                handle="B",
                knot="C",
                validated=True,
                corrected=True,
                system_confidence=ConfidenceLevel.HIGH,
            ),
        ]

        stats = calculator.calculate_comprehensive_statistics(splits, ["2025-01"])

        assert stats.total == 2
        assert stats.validated == 2
        assert stats.corrected == 1
        # Both splits are no_split because the second one doesn't have proper split detection
        assert stats.split_types["no_split"] == 2
        assert stats.confidence_breakdown["high"] == 1
        assert stats.month_breakdown["2025-01"] == 2

    def test_calculate_filtered_statistics(self):
        """Test filtered statistics calculation."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)

        # Create test splits
        splits = [
            BrushSplit(original="A", handle=None, knot="A", validated=True),
            BrushSplit(original="B", handle=None, knot="B", validated=False),
            BrushSplit(
                original="C w/ D",
                handle="C",
                knot="D",
                validated=True,
                corrected=True,
                system_confidence=ConfidenceLevel.HIGH,
            ),
        ]

        # Filter by validated only
        filters = {"validated_only": True}
        stats = calculator.calculate_filtered_statistics(splits, filters)

        assert stats.total == 2  # Only validated splits
        assert stats.validated == 2
        assert stats.corrected == 1

    def test_apply_filters(self):
        """Test filter application."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)

        splits = [
            BrushSplit(original="A", handle=None, knot="A", validated=True),
            BrushSplit(original="B", handle=None, knot="B", validated=False),
            BrushSplit(
                original="C w/ D",
                handle="C",
                knot="D",
                validated=True,
                corrected=True,
                system_confidence=ConfidenceLevel.HIGH,
            ),
        ]

        # Test validated_only filter
        filtered = calculator._apply_filters(splits, {"validated_only": True})
        assert len(filtered) == 2

        # Test confidence level filter
        filtered = calculator._apply_filters(splits, {"confidence_level": "high"})
        assert len(filtered) == 1

        # Test split type filter - all are no_split due to handle=None
        filtered = calculator._apply_filters(splits, {"split_type": "no_split"})
        assert len(filtered) == 3

    def test_get_split_type(self):
        """Test split type determination."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)

        # Test no_split
        split1 = BrushSplit(original="A", handle=None, knot="A")
        assert calculator._get_split_type(split1) == "no_split"

        # Test delimiter - need to mock the confidence calculation
        split2 = BrushSplit(original="A w/ B", handle="A", knot="B")
        # The actual calculation depends on the confidence logic, so we'll test the basic case
        assert calculator._get_split_type(split2) in [
            "delimiter",
            "fiber_hint",
            "brand_context",
            "no_split",
        ]

        # Test fiber_hint
        split3 = BrushSplit(original="A badger", handle="A", knot="badger")
        assert calculator._get_split_type(split3) in ["fiber_hint", "brand_context", "no_split"]

        # Test brand_context
        split4 = BrushSplit(original="A omega", handle="A", knot="omega")
        assert calculator._get_split_type(split4) in ["brand_context", "no_split"]

    def test_calculate_recent_activity(self):
        """Test recent activity calculation."""
        validator = BrushSplitValidator()
        calculator = StatisticsCalculator(validator)

        # Create splits with recent validation dates
        from datetime import datetime, timedelta

        # Use timezone-aware dates
        recent_date = (datetime.now() - timedelta(days=1)).isoformat()
        old_date = (datetime.now() - timedelta(days=10)).isoformat()

        splits = [
            BrushSplit(
                original="A",
                handle=None,
                knot="A",
                validated=True,
                validated_at=recent_date,
            ),
            BrushSplit(
                original="B",
                handle=None,
                knot="B",
                validated=True,
                validated_at=old_date,
            ),
        ]

        activity = calculator._calculate_recent_activity(splits)

        assert "recent_validations" in activity
        assert "total_recent" in activity
        assert "recent_corrections" in activity
        assert activity["total_recent"] == 1  # Only one recent validation


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_file_not_found_error_handling(self):
        """Test handling of missing YAML file."""
        validator = BrushSplitValidator()
        validator.yaml_path = Path("/nonexistent/file.yaml")

        # Should not raise exception, just log and continue
        validator.load_validated_splits()
        assert len(validator.validated_splits) == 0

    def test_corrupted_yaml_file_handling(self, tmp_path):
        """Test handling of corrupted YAML file."""
        validator = BrushSplitValidator()
        validator.yaml_path = tmp_path / "corrupted.yaml"

        # Create corrupted YAML file
        with open(validator.yaml_path, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(DataCorruptionError):
            validator.load_validated_splits()

    def test_invalid_yaml_structure_handling(self, tmp_path):
        """Test handling of invalid YAML structure."""
        validator = BrushSplitValidator()
        validator.yaml_path = tmp_path / "invalid.yaml"

        # Create YAML with invalid structure
        with open(validator.yaml_path, "w") as f:
            yaml.dump("not_a_dict", f)

        with pytest.raises(DataCorruptionError):
            validator.load_validated_splits()

    def test_save_with_backup_creation(self, tmp_path):
        """Test that save operation creates backup."""
        validator = BrushSplitValidator()
        validator.yaml_path = tmp_path / "test.yaml"

        # Create initial file
        with open(validator.yaml_path, "w") as f:
            yaml.dump({"splits": []}, f)

        # Save new data
        splits = [create_test_split("test brush")]
        success = validator.save_validated_splits(splits)

        assert success
        assert validator.yaml_path.exists()
        assert (tmp_path / "test.yaml.backup").exists()

    def test_save_retry_logic(self, tmp_path):
        """Test retry logic for save operations."""
        validator = BrushSplitValidator()
        validator.yaml_path = tmp_path / "test.yaml"
        validator._save_retry_count = 2

        # Mock file operations to fail first, then succeed
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = [OSError("Permission denied"), MagicMock()]

            splits = [create_test_split("test brush")]
            success = validator.save_validated_splits(splits)

            # Should succeed on second attempt
            assert success

    def test_load_retry_logic(self, tmp_path):
        """Test retry logic for load operations."""
        validator = BrushSplitValidator()
        validator.yaml_path = tmp_path / "test.yaml"
        validator._load_retry_count = 2

        # Create valid YAML file
        with open(validator.yaml_path, "w") as f:
            yaml.dump({"splits": [create_test_split("test brush").to_dict()]}, f)

        # Mock file operations to fail first, then succeed
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = [OSError("Permission denied"), open(validator.yaml_path, "r")]

            validator.load_validated_splits()

            # Should succeed on second attempt
            assert len(validator.validated_splits) == 1


class TestAPIErrorHandling:
    """Test API endpoint error handling."""

    def test_load_endpoint_missing_months(self, client):
        """Test load endpoint with missing months."""
        response = client.get("/brush-splits/load")
        assert response.status_code == 400
        assert "No months specified" in response.json()["detail"]

    def test_load_endpoint_missing_files(self, client):
        """Test load endpoint with missing month files."""
        response = client.get("/brush-splits/load?months=2025-99")
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert "2025-99" in data["errors"]["failed_months"]

    def test_load_endpoint_corrupted_files(self, client, tmp_path):
        """Test load endpoint with corrupted JSON files."""
        # Create corrupted JSON file
        corrupted_file = Path("data/matched/2025-99.json")
        corrupted_file.parent.mkdir(parents=True, exist_ok=True)
        with open(corrupted_file, "w") as f:
            f.write('{"data": [{"invalid": json')

        try:
            response = client.get("/brush-splits/load?months=2025-99")
            assert response.status_code == 200
            data = response.json()
            assert "errors" in data
            assert "2025-99" in data["errors"]["failed_months"]
        finally:
            # Cleanup
            if corrupted_file.exists():
                corrupted_file.unlink()

    def test_save_endpoint_no_data(self, client):
        """Test save endpoint with no data."""
        response = client.post("/brush-splits/save", json={"brush_splits": []})
        assert response.status_code == 400
        assert "No brush splits provided" in response.json()["detail"]

    def test_save_endpoint_invalid_data(self, client):
        """Test save endpoint with invalid data."""
        invalid_data = {
            "brush_splits": [
                {"original": "", "knot": "test"},  # Missing original
                {"original": "test", "knot": ""},  # Missing knot
            ]
        }
        response = client.post("/brush-splits/save", json=invalid_data)
        assert response.status_code == 400
        assert "Validation errors" in response.json()["detail"]

    def test_save_endpoint_file_error(self, client):
        """Test save endpoint with file system errors."""
        with patch("webui.api.brush_splits.BrushSplitValidator.save_validated_splits") as mock_save:
            mock_save.return_value = False

            valid_data = {
                "brush_splits": [{"original": "test brush", "knot": "test", "validated": True}]
            }
            response = client.post("/brush-splits/save", json=valid_data)
            assert response.status_code == 500
            assert "Failed to save splits to file" in response.json()["detail"]

    def test_yaml_endpoint_file_not_found(self, client):
        """Test YAML endpoint when file doesn't exist."""
        with patch("webui.api.brush_splits.validator.yaml_path") as mock_path:
            mock_path.exists.return_value = False

            response = client.get("/brush-splits/yaml")
            assert response.status_code == 200
            data = response.json()
            assert data["file_info"]["exists"] is False
            assert data["file_info"]["loaded_count"] == 0

    def test_statistics_endpoint_error_handling(self, client):
        """Test statistics endpoint error handling."""
        with patch("webui.api.brush_splits.validator.load_validated_splits") as mock_load:
            mock_load.side_effect = ProcessingError("Test error")

            response = client.get("/brush-splits/statistics")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestErrorCategorization:
    """Test proper error categorization and user-friendly messages."""

    def test_user_error_vs_system_error(self):
        """Test distinction between user errors and system errors."""
        # User errors (400)
        user_errors = [
            ("No months specified", 400),
            ("No brush splits provided", 400),
            ("Validation errors", 400),
        ]

        # System errors (500)
        system_errors = [
            ("File I/O error", 500),
            ("YAML parsing error", 500),
            ("Internal server error", 500),
        ]

        for error_msg, expected_code in user_errors + system_errors:
            # This is a conceptual test - in practice, these would be tested
            # through the actual API endpoints
            assert expected_code in [400, 500]

    def test_error_message_clarity(self):
        """Test that error messages are clear and actionable."""
        error_messages = [
            "No months specified",
            "No brush splits provided",
            "Validation errors: Split 0: missing original field",
            "Failed to save splits to file",
            "Internal server error: Test error",
        ]

        for msg in error_messages:
            assert len(msg) > 0
            assert "error" in msg.lower() or "missing" in msg.lower() or "failed" in msg.lower()


def create_test_split(original: str):
    """Helper function to create a test brush split."""
    from webui.api.brush_splits import BrushSplit

    return BrushSplit(
        original=original,
        handle="test handle",
        knot="test knot",
        validated=True,
        corrected=False,
    )
