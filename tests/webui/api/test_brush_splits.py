"""Unit tests for brush splits data structures and validation logic."""

import tempfile
from pathlib import Path

from webui.api.brush_splits import (
    BrushSplitOccurrence,
    BrushSplit,
    BrushSplitStatistics,
    BrushSplitValidator,
    ConfidenceLevel,
    normalize_brush_string,
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
