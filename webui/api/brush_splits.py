"""
Brush Split Validator API endpoints and data structures.

This module provides the backend API for the Brush Split Validator tool,
including data loading, validation, and YAML file management.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Create router for brush split endpoints
router = APIRouter(prefix="/api/brush-splits", tags=["brush-splits"])


def normalize_brush_string(brush_string: str) -> Optional[str]:
    """Normalize a brush string for consistent processing.

    Args:
        brush_string: The raw brush string from matched data

    Returns:
        Normalized brush string or None if invalid
    """
    if not brush_string or not brush_string.strip():
        return None

    # Basic normalization
    normalized = brush_string.strip()

    # Remove common prefixes/suffixes that don't add value
    normalized = re.sub(r"^(brush|b):\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)  # Normalize whitespace

    return normalized if normalized else None


class ConfidenceLevel(Enum):
    """Confidence levels for brush string splits."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationStatus(Enum):
    """Validation status for brush splits."""

    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    CORRECTED = "corrected"


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
    knot: str
    validated: bool = False
    corrected: bool = False
    validated_at: Optional[str] = None  # ISO timestamp
    system_handle: Optional[str] = None
    system_knot: Optional[str] = None
    system_confidence: Optional[ConfidenceLevel] = None
    system_reasoning: Optional[str] = None
    occurrences: List[BrushSplitOccurrence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "original": self.original,
            "handle": self.handle,
            "knot": self.knot,
            "validated": self.validated,
            "corrected": self.corrected,
            "validated_at": self.validated_at,
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
            validated=data.get("validated", False),
            corrected=data.get("corrected", False),
            validated_at=data.get("validated_at"),
            system_handle=data.get("system_handle"),
            system_knot=data.get("system_knot"),
            system_confidence=system_confidence,
            system_reasoning=data.get("system_reasoning"),
            occurrences=[
                BrushSplitOccurrence.from_dict(occ) for occ in data.get("occurrences", [])
            ],
        )


@dataclass
class BrushSplitStatistics:
    """Statistics for brush split validation progress."""

    total: int = 0
    validated: int = 0
    corrected: int = 0
    validation_percentage: float = 0.0
    correction_percentage: float = 0.0
    split_types: Dict[str, int] = field(
        default_factory=lambda: {"delimiter": 0, "fiber_hint": 0, "brand_context": 0, "no_split": 0}
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total": self.total,
            "validated": self.validated,
            "corrected": self.corrected,
            "validation_percentage": self.validation_percentage,
            "correction_percentage": self.correction_percentage,
            "split_types": self.split_types,
        }

    def calculate_percentages(self):
        """Calculate validation and correction percentages."""
        if self.total > 0:
            self.validation_percentage = (self.validated / self.total) * 100
        if self.validated > 0:
            self.correction_percentage = (self.corrected / self.validated) * 100


# Pydantic models for API request/response validation
class BrushSplitOccurrenceModel(BaseModel):
    """Pydantic model for brush split occurrence."""

    file: str = Field(..., description="File containing the occurrence")
    comment_ids: List[str] = Field(default_factory=list, description="List of comment IDs")


class BrushSplitModel(BaseModel):
    """Pydantic model for brush split data."""

    original: str = Field(..., description="Original brush string")
    handle: Optional[str] = Field(None, description="Handle component")
    knot: str = Field(..., description="Knot component")
    validated: bool = Field(False, description="Whether this split has been validated")
    corrected: bool = Field(False, description="Whether this split was corrected")
    validated_at: Optional[str] = Field(None, description="ISO timestamp of validation")
    system_handle: Optional[str] = Field(None, description="System-generated handle")
    system_knot: Optional[str] = Field(None, description="System-generated knot")
    system_confidence: Optional[str] = Field(None, description="System confidence level")
    system_reasoning: Optional[str] = Field(None, description="System reasoning")
    occurrences: List[BrushSplitOccurrenceModel] = Field(
        default_factory=list, description="List of occurrences"
    )


class SaveSplitsRequest(BaseModel):
    """Request model for saving brush splits."""

    brush_splits: List[BrushSplitModel] = Field(..., description="List of brush splits to save")


class SaveSplitsResponse(BaseModel):
    """Response model for saving brush splits."""

    success: bool = Field(..., description="Whether the save operation was successful")
    message: str = Field(..., description="Human-readable message")
    saved_count: int = Field(..., description="Number of splits saved")


class LoadResponse(BaseModel):
    """Response model for loading brush splits."""

    brush_splits: List[BrushSplitModel] = Field(..., description="List of brush splits")
    statistics: Dict[str, Any] = Field(..., description="Validation statistics")


class YAMLResponse(BaseModel):
    """Response model for YAML loading."""

    brush_splits: List[BrushSplitModel] = Field(..., description="List of validated splits")
    file_info: Dict[str, Any] = Field(..., description="File information")


class StatisticsResponse(BaseModel):
    """Response model for statistics."""

    total: int = Field(..., description="Total number of splits")
    validated: int = Field(..., description="Number of validated splits")
    corrected: int = Field(..., description="Number of corrected splits")
    validation_percentage: float = Field(..., description="Validation percentage")
    correction_percentage: float = Field(..., description="Correction percentage")
    split_types: Dict[str, int] = Field(..., description="Breakdown by split type")


class BrushSplitValidator:
    """Core validator for brush string splits."""

    def __init__(self):
        self.validated_splits: Dict[str, BrushSplit] = {}
        self.yaml_path = Path("data/brush_splits.yaml")

    def load_validated_splits(self) -> None:
        """Load validated splits from YAML file with enhanced error handling."""
        if not self.yaml_path.exists():
            print(f"YAML file not found: {self.yaml_path}")
            return

        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                print("YAML file is empty or invalid")
                return

            if "brush_splits" not in data:
                print("YAML file missing 'brush_splits' key")
                return

            loaded_count = 0
            for split_data in data["brush_splits"]:
                try:
                    split = BrushSplit.from_dict(split_data)
                    self.validated_splits[split.original] = split
                    loaded_count += 1
                except Exception as e:
                    print(f"Error loading split {split_data.get('original', 'unknown')}: {e}")
                    continue

            print(f"Loaded {loaded_count} validated splits from {self.yaml_path}")
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
        except Exception as e:
            print(f"Error loading validated splits: {e}")

    def save_validated_splits(self, splits: List[BrushSplit]) -> bool:
        """Save validated splits to YAML file with atomic operations."""
        try:
            # Ensure directory exists
            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to YAML format
            yaml_data = {"brush_splits": [split.to_dict() for split in splits]}

            # Create temporary file for atomic write
            temp_path = self.yaml_path.with_suffix(".tmp")

            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, indent=2)

            # Atomic move to final location
            temp_path.replace(self.yaml_path)

            print(f"Saved {len(splits)} validated splits to {self.yaml_path}")
            return True
        except Exception as e:
            print(f"Error saving validated splits: {e}")
            # Clean up temp file if it exists
            temp_path = self.yaml_path.with_suffix(".tmp")
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            return False

    def calculate_confidence(
        self, original: str, handle: Optional[str], knot: str
    ) -> tuple[ConfidenceLevel, str]:
        """Calculate confidence level and reasoning for a brush split."""
        if not handle:  # Single component brush
            return ConfidenceLevel.HIGH, "Single component brush"

        # Check for empty components
        if not handle.strip() or not knot.strip():
            return ConfidenceLevel.LOW, "Warning: empty component detected"

        # Check for very short components
        if len(handle) < 3 or len(knot) < 3:
            return ConfidenceLevel.LOW, "Warning: component too short (<3 chars)"

        # Check for delimiter splits (most reliable)
        if " w/ " in original or " with " in original:
            return ConfidenceLevel.HIGH, "Delimiter split detected (w/ or with)"

        # Check for other delimiters
        if " / " in original or "/" in original or " - " in original:
            return ConfidenceLevel.HIGH, "Delimiter split detected (/, -, or -)"

        # Check for fiber indicators in components
        fiber_indicators = ["badger", "boar", "synthetic", "silvertip", "syn"]
        handle_has_fiber = any(indicator in handle.lower() for indicator in fiber_indicators)
        knot_has_fiber = any(indicator in knot.lower() for indicator in fiber_indicators)

        if handle_has_fiber and not knot_has_fiber:
            return ConfidenceLevel.HIGH, "Fiber-hint split: handle contains fiber indicator"
        elif knot_has_fiber and not handle_has_fiber:
            return ConfidenceLevel.HIGH, "Fiber-hint split: knot contains fiber indicator"
        elif handle_has_fiber and knot_has_fiber:
            return (
                ConfidenceLevel.MEDIUM,
                "Fiber-hint split: both components contain fiber indicators",
            )

        # Check for brand patterns (common brand names)
        brand_indicators = [
            "omega",
            "semogue",
            "zenith",
            "simpson",
            "declaration",
            "dg",
            "chisel",
            "c&h",
        ]
        handle_has_brand = any(brand in handle.lower() for brand in brand_indicators)
        knot_has_brand = any(brand in knot.lower() for brand in brand_indicators)

        if handle_has_brand and not knot_has_brand:
            return ConfidenceLevel.HIGH, "Brand-context split: handle contains brand indicator"
        elif knot_has_brand and not handle_has_brand:
            return ConfidenceLevel.HIGH, "Brand-context split: knot contains brand indicator"
        elif handle_has_brand and knot_has_brand:
            return (
                ConfidenceLevel.MEDIUM,
                "Brand-context split: both components contain brand indicators",
            )

        # Analyze component quality for unknown splits
        handle_quality = len(handle) >= 5 and not handle.isdigit()
        knot_quality = len(knot) >= 5 and not knot.isdigit()

        if handle_quality and knot_quality:
            return ConfidenceLevel.MEDIUM, "Unknown split type with good component quality"
        else:
            return ConfidenceLevel.LOW, "Unknown split type with poor component quality"

    def validate_split(
        self, original: str, handle: Optional[str], knot: str, validated_at: Optional[str] = None
    ) -> BrushSplit:
        """Create a validated brush split."""
        if validated_at is None:
            validated_at = datetime.utcnow().isoformat() + "Z"

        # Calculate system confidence and reasoning
        system_confidence, system_reasoning = self.calculate_confidence(original, handle, knot)

        # Check if this is a correction
        existing = self.validated_splits.get(original)
        corrected = False
        system_handle = None
        system_knot = None

        if existing:
            corrected = existing.handle != handle or existing.knot != knot
            if corrected:
                system_handle = existing.handle
                system_knot = existing.knot

        return BrushSplit(
            original=original,
            handle=handle,
            knot=knot,
            validated=True,
            corrected=corrected,
            validated_at=validated_at,
            system_handle=system_handle,
            system_knot=system_knot,
            system_confidence=system_confidence if corrected else None,
            system_reasoning=system_reasoning if corrected else None,
            occurrences=existing.occurrences if existing else [],
        )

    def merge_occurrences(self, original: str, new_occurrences: List[BrushSplitOccurrence]) -> None:
        """Merge new occurrences with existing validated entries."""
        if original not in self.validated_splits:
            return

        existing_split = self.validated_splits[original]

        # Create a set of existing file/comment_id combinations for efficient lookup
        existing_combinations = set()
        for occ in existing_split.occurrences:
            for comment_id in occ.comment_ids:
                existing_combinations.add((occ.file, comment_id))

        # Add new occurrences that don't already exist
        for new_occ in new_occurrences:
            for comment_id in new_occ.comment_ids:
                if (new_occ.file, comment_id) not in existing_combinations:
                    # Find existing occurrence for this file or create new one
                    existing_file_occ = None
                    for occ in existing_split.occurrences:
                        if occ.file == new_occ.file:
                            existing_file_occ = occ
                            break

                    if existing_file_occ:
                        existing_file_occ.comment_ids.append(comment_id)
                    else:
                        existing_split.occurrences.append(
                            BrushSplitOccurrence(file=new_occ.file, comment_ids=[comment_id])
                        )
                    existing_combinations.add((new_occ.file, comment_id))

    def get_all_validated_splits(self) -> List[BrushSplit]:
        """Get all validated splits as a list."""
        return list(self.validated_splits.values())


# Global validator instance
validator = BrushSplitValidator()


@router.get("/load", response_model=LoadResponse, summary="Load brush splits from selected months")
async def load_brush_splits(months: List[str] = Query(..., description="Months to load data from")):
    """Load brush strings from selected months.

    Args:
        months: List of months in YYYY-MM format to load data from

    Returns:
        LoadResponse containing brush splits and statistics

    Raises:
        HTTPException: If no months specified or data loading fails
    """
    try:
        if not months:
            raise HTTPException(status_code=400, detail="No months specified")

        # Load validated splits first
        validator.load_validated_splits()

        # Load brush splits from matched data
        brush_splits: Dict[str, Dict] = {}  # original -> split_data

        for month in months:
            file_path = Path(f"data/matched/{month}.json")
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for record in data.get("data", []):
                    brush_data = record.get("brush")
                    if brush_data and brush_data.get("original"):
                        original = brush_data["original"]
                        normalized = normalize_brush_string(original)
                        if normalized:
                            # Extract split information from matched data
                            matched = brush_data.get("matched", {})
                            handle_text = matched.get("_original_handle_text")
                            knot_text = matched.get("_original_knot_text")

                            # If we have split information, use it
                            if handle_text and knot_text:
                                split_key = normalized
                                if split_key not in brush_splits:
                                    brush_splits[split_key] = {
                                        "original": normalized,
                                        "handle": handle_text,
                                        "knot": knot_text,
                                        "comment_ids": [],
                                    }
                                brush_splits[split_key]["comment_ids"].append(
                                    record.get("comment_id", "")
                                )
                            else:
                                # No split information, treat as single component
                                split_key = normalized
                                if split_key not in brush_splits:
                                    brush_splits[split_key] = {
                                        "original": normalized,
                                        "handle": None,
                                        "knot": normalized,
                                        "comment_ids": [],
                                    }
                                brush_splits[split_key]["comment_ids"].append(
                                    record.get("comment_id", "")
                                )
            except Exception as e:
                print(f"Error loading {month}: {e}")
                continue

        # Convert to BrushSplit objects
        splits = []
        for split_data in brush_splits.values():
            original = split_data["original"]
            handle = split_data["handle"]
            knot = split_data["knot"]
            comment_ids = split_data["comment_ids"]

            # Check if already validated
            if original in validator.validated_splits:
                split = validator.validated_splits[original]
                # Add new occurrences
                new_occurrence = BrushSplitOccurrence(
                    file=f"{months[0]}.json",  # Use first month as representative
                    comment_ids=comment_ids,
                )
                split.occurrences.append(new_occurrence)
                splits.append(split)
            else:
                # Create new unvalidated split with actual split data
                split = BrushSplit(
                    original=original,
                    handle=handle,
                    knot=knot,
                    validated=False,
                    corrected=False,
                    occurrences=[
                        BrushSplitOccurrence(file=f"{months[0]}.json", comment_ids=comment_ids)
                    ],
                )
                splits.append(split)

        # Calculate statistics with split type breakdown
        stats = BrushSplitStatistics()
        stats.total = len(splits)
        stats.validated = sum(1 for s in splits if s.validated)
        stats.corrected = sum(1 for s in splits if s.corrected)

        # Calculate split type breakdown
        for split in splits:
            if split.handle is None:
                stats.split_types["no_split"] += 1
            else:
                # Determine split type based on confidence calculation
                confidence, reasoning = validator.calculate_confidence(
                    split.original, split.handle, split.knot
                )
                if "delimiter" in reasoning.lower():
                    stats.split_types["delimiter"] += 1
                elif "fiber" in reasoning.lower():
                    stats.split_types["fiber_hint"] += 1
                elif "brand" in reasoning.lower():
                    stats.split_types["brand_context"] += 1
                else:
                    stats.split_types["no_split"] += 1

        stats.calculate_percentages()

        return {
            "brush_splits": [split.to_dict() for split in splits],
            "statistics": stats.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/yaml", response_model=YAMLResponse, summary="Load existing validated splits from YAML"
)
async def load_yaml():
    """Load existing validated splits from YAML file.

    Returns:
        YAMLResponse containing validated splits and file information

    Raises:
        HTTPException: If YAML loading fails
    """
    try:
        validator.load_validated_splits()

        # Get file information
        yaml_exists = validator.yaml_path.exists()
        yaml_size = validator.yaml_path.stat().st_size if yaml_exists else 0

        return {
            "brush_splits": [split.to_dict() for split in validator.validated_splits.values()],
            "file_info": {
                "exists": yaml_exists,
                "path": str(validator.yaml_path),
                "size_bytes": yaml_size,
                "loaded_count": len(validator.validated_splits),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", response_model=SaveSplitsResponse, summary="Save validated splits to YAML")
async def save_splits(data: SaveSplitsRequest):
    """Save validated splits to YAML file.

    Args:
        data: SaveSplitsRequest containing brush splits to save

    Returns:
        SaveSplitsResponse with save operation results

    Raises:
        HTTPException: If save operation fails
    """
    try:
        # Convert Pydantic models to BrushSplit objects
        splits = []
        for split_model in data.brush_splits:
            # Convert Pydantic model to dict, then to BrushSplit
            split_dict = split_model.model_dump()
            split = BrushSplit.from_dict(split_dict)
            splits.append(split)

        success = validator.save_validated_splits(splits)
        if success:
            return {
                "success": True,
                "message": f"Saved {len(splits)} brush splits",
                "saved_count": len(splits),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save splits")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=StatisticsResponse, summary="Get validation statistics")
async def get_statistics():
    """Get validation statistics for all validated splits.

    Returns:
        StatisticsResponse containing validation progress and split type breakdown

    Raises:
        HTTPException: If statistics calculation fails
    """
    try:
        validator.load_validated_splits()

        stats = BrushSplitStatistics()
        stats.total = len(validator.validated_splits)
        stats.validated = sum(1 for s in validator.validated_splits.values() if s.validated)
        stats.corrected = sum(1 for s in validator.validated_splits.values() if s.corrected)

        # Calculate split type breakdown for validated splits
        for split in validator.validated_splits.values():
            if split.handle is None:
                stats.split_types["no_split"] += 1
            else:
                # Determine split type based on confidence calculation
                confidence, reasoning = validator.calculate_confidence(
                    split.original, split.handle, split.knot
                )
                if "delimiter" in reasoning.lower():
                    stats.split_types["delimiter"] += 1
                elif "fiber" in reasoning.lower():
                    stats.split_types["fiber_hint"] += 1
                elif "brand" in reasoning.lower():
                    stats.split_types["brand_context"] += 1
                else:
                    stats.split_types["no_split"] += 1

        stats.calculate_percentages()

        return stats.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
