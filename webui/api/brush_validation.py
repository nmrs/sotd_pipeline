"""Brush validation API endpoints for the SOTD Pipeline WebUI."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from sotd.match.brush_validation_cli import BrushValidationCLI
from webui.api.files import get_available_months

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brush-validation", tags=["brush-validation"])


class ValidationActionRequest(BaseModel):
    """Request model for validation actions."""

    input_text: str
    month: str
    system_used: str
    action: str
    system_choice: Dict[str, Any]
    user_choice: Dict[str, Any]
    all_brush_strategies: List[Dict[str, Any]]

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate month format is YYYY-MM."""
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Month must be in YYYY-MM format")
        return v

    @field_validator("system_used")
    @classmethod
    def validate_system_used(cls, v: str) -> str:
        """Validate system_used is valid."""
        if v not in ["legacy", "scoring", "migrated"]:
            raise ValueError("system_used must be 'legacy', 'scoring', or 'migrated'")
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action is valid."""
        if v not in ["validate", "override"]:
            raise ValueError("action must be 'validate' or 'override'")
        return v


class BrushValidationResponse(BaseModel):
    """Response model for brush validation data."""

    entries: List[Dict[str, Any]]
    pagination: Optional[Dict[str, Any]] = None


class ValidationStatisticsResponse(BaseModel):
    """Response model for validation statistics."""

    total_entries: int
    validated_count: int
    overridden_count: int
    unvalidated_count: int
    validation_rate: float


class ValidationActionResponse(BaseModel):
    """Response model for validation actions."""

    success: bool
    message: str


class AvailableMonthsResponse(BaseModel):
    """Response model for available months."""

    months: List[str]


@router.get("/months", response_model=AvailableMonthsResponse)
async def get_validation_months() -> AvailableMonthsResponse:
    """Get available months for brush validation."""
    try:
        logger.info("Getting available months for brush validation")
        months = await get_available_months()
        return AvailableMonthsResponse(months=months)
    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{month}/{system}", response_model=BrushValidationResponse)
async def get_brush_validation_data(
    month: str,
    system: str,
    sort_by: str = Query(default="unvalidated", pattern="^(unvalidated|validated|ambiguity)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
) -> BrushValidationResponse:
    """
    Get brush validation data for a specific month and system.

    Args:
        month: Month in YYYY-MM format
        system: System type ('legacy' or 'scoring')
        sort_by: Sort criteria ('unvalidated', 'validated', or 'ambiguity')
        page: Page number (1-based)
        page_size: Number of entries per page
    """
    # Validate month format
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

    # Validate system
    if system not in ["legacy", "scoring"]:
        raise HTTPException(status_code=422, detail="System must be 'legacy' or 'scoring'")

    try:
        logger.info(f"Loading brush validation data for {month}/{system}")

        # Initialize CLI with default data path
        cli = BrushValidationCLI()

        # Load and sort data
        entries = cli.load_month_data(month, system)
        sorted_entries = cli.sort_entries(entries, month, sort_by)

        # Calculate pagination
        total = len(sorted_entries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = sorted_entries[start_idx:end_idx]

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        }

        logger.info(
            f"Loaded {len(paginated_entries)} entries (page {page} of {pagination['pages']})"
        )

        return BrushValidationResponse(entries=paginated_entries, pagination=pagination)

    except Exception as e:
        logger.error(f"Error loading brush validation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{month}", response_model=ValidationStatisticsResponse)
async def get_validation_statistics(month: str) -> ValidationStatisticsResponse:
    """
    Get validation statistics for a specific month.

    Args:
        month: Month in YYYY-MM format
    """
    # Validate month format
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

    try:
        logger.info(f"Getting validation statistics for {month}")

        # Initialize CLI
        cli = BrushValidationCLI()

        # Get statistics
        stats = cli.get_validation_statistics(month)

        return ValidationStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting validation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action", response_model=ValidationActionResponse)
async def record_validation_action(
    action_data: ValidationActionRequest,
) -> ValidationActionResponse:
    """
    Record a user validation or override action.

    Args:
        action_data: Validation action data
    """
    try:
        logger.info(f"Recording {action_data.action} action for {action_data.input_text}")

        # Initialize CLI
        cli = BrushValidationCLI()

        # Record the action
        if action_data.action == "validate":
            cli.user_actions_manager.record_validation(
                input_text=action_data.input_text,
                month=action_data.month,
                system_used=action_data.system_used,
                system_choice=action_data.system_choice,
                user_choice=action_data.user_choice,
                all_brush_strategies=action_data.all_brush_strategies,
            )
        elif action_data.action == "override":
            cli.user_actions_manager.record_override(
                input_text=action_data.input_text,
                month=action_data.month,
                system_used=action_data.system_used,
                system_choice=action_data.system_choice,
                user_choice=action_data.user_choice,
                all_brush_strategies=action_data.all_brush_strategies,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action_data.action}")

        return ValidationActionResponse(
            success=True, message=f"Successfully recorded {action_data.action} action"
        )

    except Exception as e:
        logger.error(f"Error recording validation action: {e}")
        raise HTTPException(status_code=500, detail=str(e))
