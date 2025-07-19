"""API endpoints for managing filtered entries."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for importing SOTD modules
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import SOTD modules after path setup
from sotd.utils.filtered_entries import load_filtered_entries, save_filtered_entries  # noqa: E402

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/filtered", tags=["filtered"])

# Path to filtered entries file
FILTERED_ENTRIES_PATH = Path("data/intentionally_unmatched.yaml")


class FilteredEntryRequest(BaseModel):
    """Request model for filtered entry operations."""

    category: str = Field(..., description="Product category (razor, brush, blade, soap)")
    entries: List[Dict[str, Any]] = Field(..., description="List of entries to process")


class FilteredEntryResponse(BaseModel):
    """Response model for filtered entry operations."""

    success: bool
    message: str
    data: Dict[str, Any] | None = None
    added_count: int = 0
    removed_count: int = 0
    errors: List[str] = []


class FilteredStatusRequest(BaseModel):
    """Request model for checking filtered status."""

    entries: List[Dict[str, str]] = Field(..., description="List of entries to check")


class FilteredStatusResponse(BaseModel):
    """Response model for filtered status check."""

    success: bool
    message: str
    data: Dict[str, bool]


@router.get("/", response_model=FilteredEntryResponse)
async def get_filtered_entries():
    """Get all filtered entries."""
    try:
        manager = load_filtered_entries(FILTERED_ENTRIES_PATH)
        data = manager.get_filtered_entries()

        return FilteredEntryResponse(
            success=True, message="Filtered entries retrieved successfully", data=data
        )
    except Exception as e:
        logger.error(f"Error retrieving filtered entries: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving filtered entries: {str(e)}")


@router.post("/", response_model=FilteredEntryResponse)
async def update_filtered_entries(request: FilteredEntryRequest):
    """Add or remove filtered entries."""
    try:
        category = request.category
        entries = request.entries

        if not category:
            raise HTTPException(status_code=400, detail="Category is required")

        if not entries:
            raise HTTPException(status_code=400, detail="Entries list is required")

        # Load current filtered entries
        manager = load_filtered_entries(FILTERED_ENTRIES_PATH)

        # Process each entry
        added_count = 0
        removed_count = 0
        errors = []

        for entry in entries:
            entry_name = entry.get("name")
            action = entry.get("action")
            comment_id = entry.get("comment_id")
            file_path = entry.get("file_path")
            source = entry.get("source", "user")

            if not entry_name:
                errors.append("Entry name is required")
                continue

            if action not in ["add", "remove"]:
                errors.append(f"Invalid action: {action}")
                continue

            if action == "add":
                if not comment_id or not file_path:
                    errors.append("comment_id and file_path are required for add action")
                    continue

                try:
                    manager.add_entry(category, entry_name, comment_id, file_path, source)
                    added_count += 1
                except Exception as e:
                    errors.append(f"Error adding entry {entry_name}: {str(e)}")

            elif action == "remove":
                if not comment_id or not file_path:
                    errors.append("comment_id and file_path are required for remove action")
                    continue

                try:
                    if manager.remove_entry(category, entry_name, comment_id, file_path):
                        removed_count += 1
                    else:
                        errors.append(f"Entry {entry_name} not found for removal")
                except Exception as e:
                    errors.append(f"Error removing entry {entry_name}: {str(e)}")

        # Save changes
        save_filtered_entries(manager)

        # Prepare response
        message_parts = []
        if added_count > 0:
            message_parts.append(f"Added {added_count} entries")
        if removed_count > 0:
            message_parts.append(f"Removed {removed_count} entries")

        message = "; ".join(message_parts) if message_parts else "No changes made"

        return FilteredEntryResponse(
            success=len(errors) == 0,
            message=message,
            added_count=added_count,
            removed_count=removed_count,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating filtered entries: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating filtered entries: {str(e)}")


@router.get("/{category}", response_model=FilteredEntryResponse)
async def get_filtered_entries_by_category(category: str):
    """Get filtered entries for a specific category."""
    try:
        manager = load_filtered_entries(FILTERED_ENTRIES_PATH)
        data = manager.get_filtered_entries(category)

        return FilteredEntryResponse(
            success=True,
            message=f"Filtered entries for {category} retrieved successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Error retrieving filtered entries for {category}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving filtered entries for {category}: {str(e)}"
        )


@router.post("/check", response_model=FilteredStatusResponse)
async def check_filtered_status(request: FilteredStatusRequest):
    """Check if specific entries are filtered."""
    try:
        entries = request.entries

        if not entries:
            raise HTTPException(status_code=400, detail="Entries list is required")

        manager = load_filtered_entries(FILTERED_ENTRIES_PATH)

        results = {}
        for entry in entries:
            category = entry.get("category")
            entry_name = entry.get("name")

            if not category or not entry_name:
                continue

            is_filtered = manager.is_filtered(category, entry_name)
            results[f"{category}:{entry_name}"] = is_filtered

        return FilteredStatusResponse(
            success=True, message="Filtered status checked successfully", data=results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking filtered status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking filtered status: {str(e)}")
