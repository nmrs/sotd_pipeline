"""Tests for brush split validator data structures and API endpoints."""

from pathlib import Path
import tempfile

from webui.api.brush_splits import (
    BrushSplitOccurrence,
    BrushSplit,
    BrushSplitStatistics,
    BrushSplitValidator,
    ConfidenceLevel,
    normalize_brush_string,
)


class TestBrushSplitOccurrence:
    """Test BrushSplitOccurrence dataclass."""

    def test_creation(self):
        """Test creating a BrushSplitOccurrence."""
        occurrence = BrushSplitOccurrence(file="2025-01.json", comment_ids=["abc123", "def456"])

        assert occurrence.file == "2025-01.json"
        assert occurrence.comment_ids == ["abc123", "def456"]

    def test_to_dict(self):
        """Test serialization to dictionary."""
        occurrence = BrushSplitOccurrence(file="2025-01.json", comment_ids=["abc123"])

        data = occurrence.to_dict()
        assert data["file"] == "2025-01.json"
        assert data["comment_ids"] == ["abc123"]

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"file": "2025-01.json", "comment_ids": ["abc123", "def456"]}

        occurrence = BrushSplitOccurrence.from_dict(data)
        assert occurrence.file == "2025-01.json"
        assert occurrence.comment_ids == ["abc123", "def456"]

    def test_from_dict_empty_comment_ids(self):
        """Test from_dict with missing comment_ids."""
        data = {"file": "2025-01.json"}

        occurrence = BrushSplitOccurrence.from_dict(data)
        assert occurrence.file == "2025-01.json"
        assert occurrence.comment_ids == []


class TestBrushSplit:
    """Test BrushSplit dataclass."""

    def test_creation_single_component(self):
        """Test creating a single component brush split."""
        split = BrushSplit(
            original="Declaration B15",
            handle=None,
            knot="Declaration B15",
            validated=True,
            corrected=False,
            validated_at="2025-01-27T14:30:00Z",
            occurrences=[BrushSplitOccurrence(file="2025-01.json", comment_ids=["abc123"])],
        )

        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert split.validated is True
        assert split.corrected is False

    def test_creation_multi_component(self):
        """Test creating a multi component brush split."""
        split = BrushSplit(
            original="Declaration B15 w/ Chisel & Hound Zebra",
            handle="Chisel & Hound Zebra",
            knot="Declaration B15",
            validated=True,
            corrected=True,
            validated_at="2025-01-27T14:30:00Z",
            system_handle="Declaration B15",
            system_knot="Chisel & Hound Zebra",
            system_confidence=ConfidenceLevel.HIGH,
            system_reasoning="Delimiter split: w/ detected",
            occurrences=[BrushSplitOccurrence(file="2025-01.json", comment_ids=["abc123"])],
        )

        assert split.original == "Declaration B15 w/ Chisel & Hound Zebra"
        assert split.handle == "Chisel & Hound Zebra"
        assert split.knot == "Declaration B15"
        assert split.corrected is True
        assert split.system_confidence == ConfidenceLevel.HIGH

    def test_to_dict_single_component(self):
        """Test serialization of single component brush."""
        split = BrushSplit(
            original="Declaration B15",
            handle=None,
            knot="Declaration B15",
            validated=True,
            corrected=False,
            validated_at="2025-01-27T14:30:00Z",
            occurrences=[],
        )

        data = split.to_dict()
        assert data["original"] == "Declaration B15"
        assert data["handle"] is None
        assert data["knot"] == "Declaration B15"
        assert data["validated"] is True
        assert data["corrected"] is False
        assert "system_handle" not in data  # Should not be included for non-corrected

    def test_to_dict_corrected(self):
        """Test serialization of corrected brush split."""
        split = BrushSplit(
            original="Declaration B15 w/ Chisel & Hound Zebra",
            handle="Chisel & Hound Zebra",
            knot="Declaration B15",
            validated=True,
            corrected=True,
            validated_at="2025-01-27T14:30:00Z",
            system_handle="Declaration B15",
            system_knot="Chisel & Hound Zebra",
            system_confidence=ConfidenceLevel.HIGH,
            system_reasoning="Delimiter split: w/ detected",
            occurrences=[],
        )

        data = split.to_dict()
        assert data["corrected"] is True
        assert data["system_handle"] == "Declaration B15"
        assert data["system_knot"] == "Chisel & Hound Zebra"
        assert data["system_confidence"] == "high"
        assert data["system_reasoning"] == "Delimiter split: w/ detected"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "original": "Declaration B15",
            "handle": None,
            "knot": "Declaration B15",
            "validated": True,
            "corrected": False,
            "validated_at": "2025-01-27T14:30:00Z",
            "occurrences": [{"file": "2025-01.json", "comment_ids": ["abc123"]}],
        }

        split = BrushSplit.from_dict(data)
        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert split.validated is True
        assert split.corrected is False

    def test_from_dict_with_system_fields(self):
        """Test deserialization with system fields."""
        data = {
            "original": "Declaration B15 w/ Chisel & Hound Zebra",
            "handle": "Chisel & Hound Zebra",
            "knot": "Declaration B15",
            "validated": True,
            "corrected": True,
            "validated_at": "2025-01-27T14:30:00Z",
            "system_handle": "Declaration B15",
            "system_knot": "Chisel & Hound Zebra",
            "system_confidence": "high",
            "system_reasoning": "Delimiter split: w/ detected",
            "occurrences": [],
        }

        split = BrushSplit.from_dict(data)
        assert split.corrected is True
        assert split.system_handle == "Declaration B15"
        assert split.system_confidence == ConfidenceLevel.HIGH

    def test_from_dict_invalid_confidence(self):
        """Test handling of invalid confidence level."""
        data = {
            "original": "Declaration B15",
            "handle": None,
            "knot": "Declaration B15",
            "validated": True,
            "corrected": True,
            "system_confidence": "invalid",
            "occurrences": [],
        }

        split = BrushSplit.from_dict(data)
        assert split.system_confidence is None


class TestBrushSplitStatistics:
    """Test BrushSplitStatistics dataclass."""

    def test_creation(self):
        """Test creating statistics."""
        stats = BrushSplitStatistics(total=100, validated=50, corrected=10)

        assert stats.total == 100
        assert stats.validated == 50
        assert stats.corrected == 10

    def test_calculate_percentages(self):
        """Test percentage calculation."""
        stats = BrushSplitStatistics(total=100, validated=50, corrected=10)

        stats.calculate_percentages()
        assert stats.validation_percentage == 50.0
        assert stats.correction_percentage == 20.0

    def test_calculate_percentages_zero_total(self):
        """Test percentage calculation with zero total."""
        stats = BrushSplitStatistics(total=0, validated=0, corrected=0)

        stats.calculate_percentages()
        assert stats.validation_percentage == 0.0
        assert stats.correction_percentage == 0.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        stats = BrushSplitStatistics(total=100, validated=50, corrected=10)
        stats.calculate_percentages()

        data = stats.to_dict()
        assert data["total"] == 100
        assert data["validated"] == 50
        assert data["corrected"] == 10
        assert data["validation_percentage"] == 50.0
        assert data["correction_percentage"] == 20.0
        assert "split_types" in data


class TestNormalizeBrushString:
    """Test brush string normalization function."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        result = normalize_brush_string("Declaration B15")
        assert result == "Declaration B15"

    def test_normalize_with_prefix(self):
        """Test normalization with brush prefix."""
        result = normalize_brush_string("brush: Declaration B15")
        assert result == "Declaration B15"

    def test_normalize_with_whitespace(self):
        """Test normalization with extra whitespace."""
        result = normalize_brush_string("  Declaration   B15  ")
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
    """Test BrushSplitValidator class."""

    def test_creation(self):
        """Test creating validator."""
        validator = BrushSplitValidator()
        assert validator.validated_splits == {}
        assert validator.yaml_path == Path("data/brush_splits.yaml")

    def test_calculate_confidence_single_component(self):
        """Test confidence calculation for single component."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence(
            "Declaration B15", None, "Declaration B15"
        )

        assert confidence == ConfidenceLevel.HIGH
        assert reasoning == "Single component brush"

    def test_calculate_confidence_delimiter(self):
        """Test confidence calculation for delimiter split."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence(
            "Declaration B15 w/ Chisel & Hound Zebra", "Chisel & Hound Zebra", "Declaration B15"
        )

        assert confidence == ConfidenceLevel.HIGH
        assert "Delimiter split detected" in reasoning

    def test_calculate_confidence_short_components(self):
        """Test confidence calculation for short components."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence("A B", "A", "B")

        assert confidence == ConfidenceLevel.LOW
        assert "too short" in reasoning

    def test_calculate_confidence_empty_components(self):
        """Test confidence calculation for empty components."""
        validator = BrushSplitValidator()
        confidence, reasoning = validator.calculate_confidence(
            "Declaration B15", "   ", "Declaration B15"  # Whitespace-only handle
        )

        assert confidence == ConfidenceLevel.LOW
        assert "empty component" in reasoning

    def test_validate_split_new(self):
        """Test validating a new split."""
        validator = BrushSplitValidator()
        split = validator.validate_split("Declaration B15", None, "Declaration B15")

        assert split.original == "Declaration B15"
        assert split.handle is None
        assert split.knot == "Declaration B15"
        assert split.validated is True
        assert split.corrected is False
        assert split.validated_at is not None

    def test_validate_split_correction(self):
        """Test validating a corrected split."""
        # Add existing split
        validator = BrushSplitValidator()
        existing = BrushSplit(
            original="Declaration B15 w/ Chisel & Hound Zebra",
            handle="Declaration B15",
            knot="Chisel & Hound Zebra",
            validated=True,
            corrected=False,
            validated_at="2025-01-27T14:30:00Z",
            occurrences=[],
        )
        validator.validated_splits[existing.original] = existing

        # Validate with correction
        split = validator.validate_split(
            "Declaration B15 w/ Chisel & Hound Zebra", "Chisel & Hound Zebra", "Declaration B15"
        )

        assert split.corrected is True
        assert split.system_handle == "Declaration B15"
        assert split.system_knot == "Chisel & Hound Zebra"

    def test_save_and_load_yaml(self):
        """Test saving and loading YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_path = Path(f.name)

        try:
            validator = BrushSplitValidator()
            validator.yaml_path = yaml_path

            # Create test splits
            splits = [
                BrushSplit(
                    original="Declaration B15",
                    handle=None,
                    knot="Declaration B15",
                    validated=True,
                    corrected=False,
                    validated_at="2025-01-27T14:30:00Z",
                    occurrences=[],
                ),
                BrushSplit(
                    original="Declaration B15 w/ Chisel & Hound Zebra",
                    handle="Chisel & Hound Zebra",
                    knot="Declaration B15",
                    validated=True,
                    corrected=True,
                    validated_at="2025-01-27T14:30:00Z",
                    system_handle="Declaration B15",
                    system_knot="Chisel & Hound Zebra",
                    system_confidence=ConfidenceLevel.HIGH,
                    system_reasoning="Delimiter split: w/ detected",
                    occurrences=[],
                ),
            ]

            # Save splits
            success = validator.save_validated_splits(splits)
            assert success is True

            # Load splits
            validator.load_validated_splits()
            assert len(validator.validated_splits) == 2

            # Check first split
            split1 = validator.validated_splits["Declaration B15"]
            assert split1.handle is None
            assert split1.corrected is False

            # Check second split
            split2 = validator.validated_splits["Declaration B15 w/ Chisel & Hound Zebra"]
            assert split2.handle == "Chisel & Hound Zebra"
            assert split2.corrected is True
            assert split2.system_confidence == ConfidenceLevel.HIGH

        finally:
            yaml_path.unlink(missing_ok=True)
