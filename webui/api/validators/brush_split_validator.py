"""Brush Split Validator that inherits from BaseValidator."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re

from webui.api.validators.base_validator import BaseValidator, ValidationResult


class ConfidenceLevel(Enum):
    """Confidence levels for brush string splits."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class BrushSplitOccurrence:
    """Represents an occurrence of a brush string in a specific file."""

    file: str
    comment_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"file": self.file, "comment_ids": self.comment_ids}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrushSplitOccurrence":
        """Create from dictionary."""
        return cls(file=data["file"], comment_ids=data.get("comment_ids", []))


@dataclass
class BrushSplit:
    """Represents a validated brush string split."""

    original: str
    handle: Optional[str]
    knot: Optional[str]  # Can be None when should_not_split is True
    match_type: Optional[str] = None
    validated: bool = False
    corrected: bool = False
    validated_at: Optional[str] = None  # ISO timestamp
    system_handle: Optional[str] = None
    system_knot: Optional[str] = None
    system_confidence: Optional[ConfidenceLevel] = None
    system_reasoning: Optional[str] = None
    occurrences: List[BrushSplitOccurrence] = field(default_factory=list)
    should_not_split: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "original": self.original,
            "handle": self.handle,
            "knot": self.knot,
            "match_type": self.match_type,
            "validated": self.validated,
            "corrected": self.corrected,
            "validated_at": self.validated_at,
            "should_not_split": self.should_not_split,
            "occurrences": [occ.to_dict() for occ in self.occurrences],
        }

        # Only include system fields if corrected
        if self.corrected:
            result.update(
                {
                    "system_handle": self.system_handle,
                    "system_knot": self.system_knot,
                    "system_confidence": (
                        self.system_confidence.value if self.system_confidence else None
                    ),
                    "system_reasoning": self.system_reasoning,
                }
            )

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrushSplit":
        """Create from dictionary."""
        # Handle system confidence enum
        system_confidence = None
        if data.get("system_confidence"):
            try:
                system_confidence = ConfidenceLevel(data["system_confidence"])
            except ValueError:
                system_confidence = None

        return cls(
            original=data["original"],
            handle=data["handle"],
            knot=data["knot"],
            match_type=data.get("match_type"),
            validated=data.get("validated", False),
            corrected=data.get("corrected", False),
            validated_at=data.get("validated_at"),
            system_handle=data.get("system_handle"),
            system_knot=data.get("system_knot"),
            system_confidence=system_confidence,
            system_reasoning=data.get("system_reasoning"),
            should_not_split=data.get("should_not_split", False),
            occurrences=[
                BrushSplitOccurrence.from_dict(occ) for occ in data.get("occurrences", [])
            ],
        )


class BrushSplitValidator(BaseValidator):
    """Validator for brush split data that inherits from BaseValidator."""

    def __init__(self, yaml_path: Optional[Path] = None):
        """Initialize the brush split validator."""
        if yaml_path is None:
            yaml_path = Path("data/brush_splits.yaml")
        super().__init__(yaml_path)

    def normalize_brush_string(self, brush_string: str) -> Optional[str]:
        """Normalize a brush string for consistent processing."""
        if not brush_string or not brush_string.strip():
            return None

        # Basic normalization
        normalized = brush_string.strip()

        # Remove common prefixes/suffixes that don't add value
        normalized = re.sub(r"^(brush|b):\s*", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\s+", " ", normalized)  # Normalize whitespace

        return normalized if normalized else None

    def load_brush_splits(self) -> ValidationResult:
        """Load brush splits from YAML file."""
        result = self.load_data()
        if not result.success:
            return result

        # Convert loaded data to BrushSplit objects
        brush_splits = []
        splits_data = self.data.get("splits", {})

        for brush_name, entries in splits_data.items():
            if isinstance(entries, list):
                for split_data in entries:
                    try:
                        brush_split = BrushSplit.from_dict(split_data)
                        brush_splits.append(brush_split)
                    except Exception as e:
                        return ValidationResult(
                            success=False, error_message=f"Error parsing brush split data: {e}"
                        )

        return ValidationResult(success=True, data={"brush_splits": brush_splits})

    def save_brush_splits(self, brush_splits: List[BrushSplit]) -> ValidationResult:
        """Save brush splits to YAML file."""
        # Organize splits by original brush name
        organized_splits = {}
        for split in brush_splits:
            key = split.original.lower()
            if key not in organized_splits:
                organized_splits[key] = []
            organized_splits[key].append(split.to_dict())

        # Create data structure
        data = {"splits": {}}
        for key in sorted(organized_splits.keys()):
            display_name = organized_splits[key][0]["original"]
            data["splits"][display_name] = organized_splits[key]

        return self.save_data(data)

    def get_brush_split_by_name(self, brush_name: str) -> Optional[BrushSplit]:
        """Get a brush split by original brush name."""
        if not self.is_loaded:
            return None

        splits_data = self.data.get("splits", {})
        for name, entries in splits_data.items():
            if name.lower() == brush_name.lower():
                if isinstance(entries, list) and len(entries) > 0:
                    return BrushSplit.from_dict(entries[0])
        return None

    def add_brush_split(self, brush_split: BrushSplit) -> ValidationResult:
        """Add a new brush split."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        # Check if brush split already exists
        existing = self.get_brush_split_by_name(brush_split.original)
        if existing:
            return ValidationResult(
                success=False,
                error_message=f"Brush split for '{brush_split.original}' already exists",
            )

        # Add to data structure
        splits_data = self.data.get("splits", {})
        splits_data[brush_split.original] = [brush_split.to_dict()]
        self.data["splits"] = splits_data

        return ValidationResult(success=True)

    def update_brush_split(self, brush_split: BrushSplit) -> ValidationResult:
        """Update an existing brush split."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        # Check if brush split exists
        existing = self.get_brush_split_by_name(brush_split.original)
        if not existing:
            return ValidationResult(
                success=False, error_message=f"Brush split for '{brush_split.original}' not found"
            )

        # Update in data structure
        splits_data = self.data.get("splits", {})
        splits_data[brush_split.original] = [brush_split.to_dict()]
        self.data["splits"] = splits_data

        return ValidationResult(success=True)

    def delete_brush_split(self, brush_name: str) -> ValidationResult:
        """Delete a brush split."""
        if not self.is_loaded:
            return ValidationResult(success=False, error_message="Data not loaded")

        splits_data = self.data.get("splits", {})
        if brush_name not in splits_data:
            return ValidationResult(
                success=False, error_message=f"Brush split for '{brush_name}' not found"
            )

        del splits_data[brush_name]
        self.data["splits"] = splits_data

        return ValidationResult(success=True)

    def validate_brush_split_data(self, brush_split: BrushSplit) -> ValidationResult:
        """Validate brush split data."""
        required_fields = ["original"]
        errors = []

        # Check required fields
        for field_name in required_fields:
            value = getattr(brush_split, field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required field '{field_name}'")

        # Validate that either handle/knot or should_not_split is set
        if not brush_split.should_not_split:
            if brush_split.handle is None and brush_split.knot is None:
                errors.append("Either handle/knot must be set or should_not_split must be true")

        # Validate that knot is null when should_not_split is true
        if brush_split.should_not_split and brush_split.knot is not None:
            errors.append("Knot must be null when should_not_split is true")

        return ValidationResult(success=len(errors) == 0, validation_errors=errors)

    def calculate_confidence(
        self, original: str, handle: Optional[str], knot: Optional[str]
    ) -> tuple[ConfidenceLevel, str]:
        """Calculate confidence level for a brush split."""
        if not handle and not knot:
            return ConfidenceLevel.LOW, "No split provided"

        if not handle or not knot:
            return ConfidenceLevel.MEDIUM, "Partial split provided"

        # Check for common patterns that indicate high confidence
        if "w/" in original.lower() or "with" in original.lower():
            return ConfidenceLevel.HIGH, "Contains explicit split indicator"

        # Only consider it high confidence if both components are substantial
        if len(handle) > 5 and len(knot) > 5:
            return ConfidenceLevel.HIGH, "Both components have substantial content"

        return ConfidenceLevel.MEDIUM, "Standard split quality"
