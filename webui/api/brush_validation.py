"""Brush validation API endpoints for the SOTD Pipeline WebUI."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

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
    system_used: Literal["legacy", "scoring"]
    action: Literal["validate", "override"]
    # For override actions, specify which strategy index to use
    strategy_index: Optional[int] = None

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
        if v != "scoring":
            raise ValueError("system_used must be 'scoring'")
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
    correct_entries: int
    user_processed: int
    overridden_count: int
    total_processed: int
    unprocessed_count: int
    processing_rate: float
    # Legacy fields for backward compatibility
    validated_count: int
    user_validations: int
    unvalidated_count: int
    validation_rate: float
    total_actions: int


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
        available_months = await get_available_months()
        return AvailableMonthsResponse(months=available_months.months)
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
    # New filter parameters for backend filtering
    strategy_count: Optional[int] = Query(
        default=None, 
        description="Filter by number of strategies (e.g., 1 for single strategy)"
    ),
    show_validated: Optional[bool] = Query(
        default=None, description="Include validated entries"
    ),
    show_single_strategy: Optional[bool] = Query(
        default=None, description="Show only single strategy entries"
    ),
    show_multiple_strategy: Optional[bool] = Query(
        default=None, description="Show only multiple strategy entries"
    ),
) -> BrushValidationResponse:
    """
    Get brush validation data for a specific month and system.

    Args:
        month: Month in YYYY-MM format
        system: System type ('scoring')
        sort_by: Sort criteria ('unvalidated', 'validated', or 'ambiguity')
        page: Page number (1-based)
        page_size: Number of entries per page
        strategy_count: Filter by specific number of strategies
        show_validated: Include validated entries
        show_single_strategy: Show only single strategy entries
        show_multiple_strategy: Show only multiple strategy entries
    """
    # Validate month format
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

    # Validate system
    if system != "scoring":
        raise HTTPException(status_code=422, detail="System must be 'scoring'")

    try:
        logger.info(f"Loading brush validation data for {month}/{system}")

        # Use counting service as single source of truth instead of CLI
        from pathlib import Path
        from sotd.match.brush_validation_counting_service import (
            BrushValidationCountingService,
        )

        # Initialize counting service with the same data path as the CLI
        project_root = Path(__file__).parent.parent.parent
        counting_service = BrushValidationCountingService(data_path=project_root / "data")

        logger.info("Counting service initialized successfully")

        # Get the total count from counting service (single source of truth)
        stats = counting_service.get_validation_statistics(month)
        total_entries = stats["total_entries"]

        logger.info(f"Total entries from counting service: {total_entries}")

        # Get the actual data from counting service instead of CLI
        # This ensures we have the same data that was counted
        matched_data = counting_service._load_matched_data(month)

        # Convert to the format expected by the frontend
        # IMPORTANT: Load ALL entries first (including validated ones) to match counting service logic
        entries = []
        records = matched_data.get("data", [])

        for record in records:
            if "brush" not in record:
                continue

            brush_entry = record["brush"]
            comment_id = record.get("id")
            comment_ids = [comment_id] if comment_id else []

            entry = {
                "input_text": brush_entry.get("normalized", ""),
                "normalized_text": brush_entry.get("normalized", ""),
                "system_used": "scoring",
                "matched": brush_entry.get("matched"),
                "all_strategies": brush_entry.get("all_strategies", []),
                "comment_ids": comment_ids,
            }
            entries.append(entry)

        logger.info(
            f"Loaded {len(entries)} total entries from counting service (including validated)"
        )

        # Apply backend filtering based on parameters
        filtered_entries = entries

        logger.info(
            f"Filtering parameters: strategy_count={strategy_count} (type: {type(strategy_count)}), show_validated={show_validated}"
        )
        logger.info(f"Initial entries count: {len(filtered_entries)}")

        # Filter by strategy count if specified
        if strategy_count is not None:
            logger.info(f"Strategy count filtering enabled with value: {strategy_count}")
            try:
                # Use the counting service to get the actual unique brush strings with this strategy count
                # This ensures we're counting the same way as the strategy distribution endpoint
                from sotd.match.brush_validation_counting_service import (
                    BrushValidationCountingService,
                )

                # Initialize counting service with the same data path as the CLI
                project_root = Path(__file__).parent.parent.parent
                counting_service = BrushValidationCountingService(data_path=project_root / "data")

                logger.info("Counting service initialized successfully")

                # Get the actual unique brush strings from the counting service
                if show_validated:
                    strategy_stats = (
                        counting_service.get_all_entries_strategy_distribution_statistics(month)
                    )
                else:
                    strategy_stats = counting_service.get_strategy_distribution_statistics(month)

                logger.info(f"Strategy stats retrieved: {strategy_stats}")

                # Get the count for this specific strategy count
                target_count = strategy_stats["all_strategies_lengths"].get(str(strategy_count), 0)
                logger.info(f"Target count for strategy_count={strategy_count}: {target_count}")

                if target_count > 0:
                    logger.info("Loading raw data for filtering...")
                    # Load the raw data directly to get the correct structure
                    import json
                    from pathlib import Path

                    project_root = Path(__file__).parent.parent.parent
                    matched_file = project_root / "data" / "matched" / f"{month}.json"

                    with open(matched_file, "r") as f:
                        raw_data = json.load(f)

                    logger.info(f"Raw data loaded, entries: {len(raw_data['data'])}")

                    # Get unique brush strings with this strategy count from raw data
                    unique_brush_strings = set()
                    logger.info(f"Looking for entries with strategy_count={strategy_count}")

                    for entry in raw_data["data"]:
                        if (
                            entry.get("brush")
                            and entry["brush"].get("all_strategies")
                            and len(entry["brush"]["all_strategies"]) == strategy_count
                        ):
                            # Apply validation filtering to raw data to match strategy distribution endpoint
                            if show_validated is not None and not show_validated:
                                # Exclude validated entries (same logic as strategy distribution endpoint)
                                matched = entry["brush"].get("matched", {})
                                strategy = matched.get("strategy") if matched else None
                                if strategy in ["correct_complete_brush", "correct_split_brush"]:
                                    continue  # Skip validated entries

                            normalized_text = entry["brush"].get("normalized", "")
                            if normalized_text:
                                unique_brush_strings.add(normalized_text.lower().strip())

                    logger.info(
                        f"Found {len(unique_brush_strings)} unique brush strings with strategy_count={strategy_count}"
                    )
                    logger.info(
                        f"Unique brush strings: {list(unique_brush_strings)[:5]}..."
                    )  # Show first 5

                    # Filter the CLI entries to only include those unique brush strings
                    # CLI entries have normalized_text, raw data has brush.normalized
                    # We need to deduplicate to get exactly target_count unique entries
                    filtered_entries_original = filtered_entries  # Store original for deduplication
                    filtered_entries = []
                    seen_brush_strings = set()

                    for entry in filtered_entries_original:
                        normalized_text = entry.get("normalized_text", "").lower().strip()
                        if (
                            normalized_text in unique_brush_strings
                            and normalized_text not in seen_brush_strings
                        ):
                            filtered_entries.append(entry)
                            seen_brush_strings.add(normalized_text)
                            if len(filtered_entries) >= target_count:
                                break  # Stop when we have exactly target_count entries

                    logger.info(
                        f"After deduplication, found {len(filtered_entries)} unique CLI entries"
                    )
                else:
                    logger.info(f"No entries found with strategy_count={strategy_count}")
                    # No entries with this strategy count
                    filtered_entries = []

            except Exception as e:
                logger.error(f"Error in strategy count filtering: {e}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                # Fall back to no filtering
                filtered_entries = entries

        # Filter by validation status if not already filtered by strategy count
        elif show_validated is not None:
            if not show_validated:
                # Exclude validated entries
                filtered_entries = [
                    entry
                    for entry in filtered_entries
                    if not (
                        entry.get("matched")
                        and entry.get("matched", {}).get("strategy")
                        in ["correct_complete_brush", "correct_split_brush"]
                    )
                ]

        # Sort the filtered entries
        # The counting service does not have a sort_entries method, so we rely on the CLI for sorting
        # This means we need to re-initialize the CLI to get the sorted data
        project_root = Path(__file__).parent.parent.parent
        cli = BrushValidationCLI(data_path=project_root / "data")
        sorted_entries = cli.sort_entries(filtered_entries, month, sort_by)

        # Deduplicate entries by normalized text to match statistics
        # The CLI loads individual comments, but we want unique brush strings
        unique_entries = []
        seen_normalized_texts = set()

        for entry in sorted_entries:
            normalized_text = entry.get("normalized_text", "").lower().strip()
            if normalized_text and normalized_text not in seen_normalized_texts:
                unique_entries.append(entry)
                seen_normalized_texts.add(normalized_text)

        logger.info(
            f"After deduplication: {len(unique_entries)} unique entries (was {len(sorted_entries)})"
        )

        # Calculate pagination using the counting service total (authoritative)
        # The counting service gives us the true total (1200), use that for pagination
        total = total_entries  # This comes from counting service (1200)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries = unique_entries[start_idx:end_idx]

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,  # Use counting service total (1200)
            "pages": (total + page_size - 1) // page_size,
        }

        logger.info(
            f"Pagination: page {page} of {pagination['pages']} "
            f"from total {total} (counting service authoritative)"
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

        # Use counting service as single source of truth instead of CLI
        from pathlib import Path
        from sotd.match.brush_validation_counting_service import (
            BrushValidationCountingService,
        )

        # Initialize counting service with the same data path as the CLI
        project_root = Path(__file__).parent.parent.parent
        counting_service = BrushValidationCountingService(data_path=project_root / "data")

        # Get statistics from counting service (includes both new and legacy fields)
        stats = counting_service.get_validation_statistics(month)

        return ValidationStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting validation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{month}/strategy-distribution")
async def get_strategy_distribution_statistics(month: str):
    """
    Get strategy distribution statistics for a specific month.

    This endpoint provides detailed counts of entries by strategy type
    to help debug filter count mismatches.

    Args:
        month: Month in YYYY-MM format
    """
    # Validate month format
    if not re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

    try:
        logger.info(f"Getting strategy distribution statistics for {month}")

        # Initialize CLI with correct data path (relative to project root)
        project_root = Path(__file__).parent.parent.parent
        cli = BrushValidationCLI(data_path=project_root / "data")

        # Get strategy distribution statistics
        stats = cli.get_strategy_distribution_statistics(month)

        return stats

    except Exception as e:
        logger.error(f"Error getting strategy distribution statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action", response_model=ValidationActionResponse)
async def record_validation_action(
    action_data: ValidationActionRequest,
) -> ValidationActionResponse:
    """
    Record a user validation or override action.

    Args:
        action_data: Validation action data with minimal information
    """
    try:
        logger.info(f"Recording {action_data.action} action for {action_data.input_text}")

        # Initialize CLI with correct data path (relative to project root)
        project_root = Path(__file__).parent.parent.parent
        cli = BrushValidationCLI(data_path=project_root / "data")

        # Get comment IDs for this input text from the matched data
        comment_ids = cli.get_comment_ids_for_input_text(
            action_data.input_text, action_data.month, action_data.system_used
        )

        # Load the brush data for this input text to determine field type and process dual-component brushes
        brush_data = cli.load_brush_data_for_input_text(
            action_data.input_text, action_data.month, action_data.system_used
        )

        if not brush_data:
            raise HTTPException(
                status_code=404,
                detail=f"Brush data not found for input text: {action_data.input_text}",
            )

        # Record the action - the backend handles all the business logic
        if action_data.action == "validate":
            cli.user_actions_manager.record_validation_with_data(
                input_text=action_data.input_text,
                month=action_data.month,
                system_used=action_data.system_used,
                brush_data=brush_data,
                comment_ids=comment_ids,
            )
        elif action_data.action == "override":
            if action_data.strategy_index is None:
                raise HTTPException(
                    status_code=400, detail="strategy_index is required for override actions"
                )

            cli.user_actions_manager.record_override_with_data(
                input_text=action_data.input_text,
                month=action_data.month,
                system_used=action_data.system_used,
                brush_data=brush_data,
                strategy_index=action_data.strategy_index,
                comment_ids=comment_ids,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action_data.action}")

        return ValidationActionResponse(
            success=True, message=f"Successfully recorded {action_data.action} action"
        )

    except Exception as e:
        logger.error(f"Error recording validation action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/undo", response_model=ValidationActionResponse)
async def undo_last_validation_action(month: str) -> ValidationActionResponse:
    """
    Undo the last validation action for a specific month.

    This removes the last validation/override action from both the learning file
    and correct_matches.yaml, effectively reverting the last user decision.

    Args:
        month: Month in YYYY-MM format
    """
    try:
        logger.info(f"Undoing last validation action for {month}")

        # Validate month format
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise HTTPException(status_code=400, detail="Month must be in YYYY-MM format")

        # Initialize CLI with correct data path (relative to project root)
        project_root = Path(__file__).parent.parent.parent
        cli = BrushValidationCLI(data_path=project_root / "data")

        # Attempt to undo the last action
        undone_action = cli.user_actions_manager.undo_last_action(month)

        if undone_action:
            return ValidationActionResponse(
                success=True,
                message=(
                    f"Successfully undone {undone_action.action} action "
                    f"for '{undone_action.input_text}'"
                ),
            )
        else:
            return ValidationActionResponse(
                success=False, message="No actions found to undo for this month"
            )

    except Exception as e:
        logger.error(f"Error undoing validation action: {e}")
        raise HTTPException(status_code=500, detail=str(e))
