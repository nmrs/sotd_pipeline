#!/usr/bin/env python3
"""Analysis endpoints for SOTD pipeline analyzer API."""

import logging
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for importing SOTD modules
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

try:
    from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer

    logger.info("✅ UnmatchedAnalyzer imported successfully")
except ImportError as e:
    # Fallback for development
    logger.error(f"❌ Failed to import UnmatchedAnalyzer: {e}")
    UnmatchedAnalyzer = None

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


class UnmatchedAnalysisRequest(BaseModel):
    """Request model for unmatched analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap)")
    months: List[str] = Field(..., description="List of months to analyze (YYYY-MM format)")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of results to return")


class MatchPhaseRequest(BaseModel):
    """Request model for running match phase."""

    months: List[str] = Field(
        ..., description="List of months to run match phase on (YYYY-MM format)"
    )
    force: bool = Field(default=False, description="Force re-run even if data exists")


class MatchPhaseResponse(BaseModel):
    """Response model for match phase execution."""

    months: List[str]
    force: bool
    success: bool
    message: str
    error_details: str | None = None
    processing_time: float


class CommentDetail(BaseModel):
    """Model for comment details."""

    id: str
    author: str
    body: str
    created_utc: str
    thread_id: str
    thread_title: str
    url: str


class UnmatchedItem(BaseModel):
    """Model for individual unmatched item."""

    item: str
    count: int
    examples: List[str]
    comment_ids: List[str]
    # Optional fields for brush matching data
    match_type: Optional[str] = None
    matched: Optional[dict] = None
    unmatched: Optional[dict] = None


class UnmatchedAnalysisResponse(BaseModel):
    """Response model for unmatched analysis."""

    field: str
    months: List[str]
    total_unmatched: int
    unmatched_items: List[UnmatchedItem]
    processing_time: float


def validate_field(field: str) -> None:
    """Validate that the field is supported."""
    supported_fields = ["razor", "blade", "brush", "soap"]
    if field not in supported_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported field: {field}. Supported fields: {supported_fields}",
        )


def validate_months(months: List[str]) -> None:
    """Validate month format and availability."""
    if not months:
        raise HTTPException(status_code=400, detail="At least one month must be specified")

    for month in months:
        if not month or len(month) != 7 or month[4] != "-":
            raise HTTPException(
                status_code=400, detail=f"Invalid month format: {month}. Expected format: YYYY-MM"
            )


def find_comment_by_id(comment_id: str, months: List[str]) -> Optional[dict]:
    """Find a comment by its ID across the specified months."""
    import json

    for month in months:
        file_path = project_root / "data" / "matched" / f"{month}.json"
        if not file_path.exists():
            continue

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            for record in data.get("data", []):
                if record.get("id") == comment_id:
                    return record
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue

    return None


@router.get("/comment/{comment_id}", response_model=CommentDetail)
async def get_comment_detail(comment_id: str, months: str) -> CommentDetail:
    """Get detailed information for a specific comment."""
    try:
        # Parse months parameter (comma-separated list)
        month_list = [m.strip() for m in months.split(",") if m.strip()]

        if not month_list:
            raise HTTPException(status_code=400, detail="At least one month must be specified")

        # Find the comment
        comment = find_comment_by_id(comment_id, month_list)

        if not comment:
            raise HTTPException(
                status_code=404, detail=f"Comment {comment_id} not found in the specified months"
            )

        return CommentDetail(
            id=comment.get("id", ""),
            author=comment.get("author", ""),
            body=comment.get("body", ""),
            created_utc=comment.get("created_utc", ""),
            thread_id=comment.get("thread_id", ""),
            thread_title=comment.get("thread_title", ""),
            url=comment.get("url", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching comment: {str(e)}")


@router.post("/match-phase", response_model=MatchPhaseResponse)
async def run_match_phase(request: MatchPhaseRequest) -> MatchPhaseResponse:
    """Run the match phase for the specified months."""
    try:
        # Validate input parameters
        validate_months(request.months)

        logger.info(
            f"Starting match phase for {len(request.months)} months (force={request.force})"
        )

        # Clear caches if force is enabled to pick up catalog changes
        if request.force:
            try:
                from sotd.match.base_matcher import clear_catalog_cache
                from sotd.match.loaders import clear_yaml_cache

                clear_yaml_cache()
                clear_catalog_cache()
                logger.info("Cleared all caches due to force flag")
            except ImportError:
                logger.warning("Could not import cache clearing functions")

        # Run match phase for each month
        success_count = 0
        failed_months = []
        error_details = []
        all_output = []

        for month in request.months:
            logger.info(f"Processing match phase for month: {month}")

            try:
                # Build command
                cmd = [sys.executable, "run.py", "match", "--month", month]

                if request.force:
                    cmd.append("--force")

                # Run the command
                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                # Capture output for this month
                month_output = f"=== Match Phase for {month} ===\n"
                if result.stdout:
                    month_output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    month_output += f"STDERR:\n{result.stderr}\n"
                month_output += f"Return Code: {result.returncode}\n"
                all_output.append(month_output)

                if result.returncode == 0:
                    logger.info(f"✅ Match phase completed for {month}")
                    success_count += 1
                else:
                    error_msg = f"❌ Match phase failed for {month}:\n{result.stderr}"
                    logger.error(error_msg)
                    failed_months.append(month)
                    error_details.append(error_msg)

            except subprocess.TimeoutExpired:
                error_msg = f"⏰ Match phase timed out for {month}"
                logger.error(error_msg)
                failed_months.append(month)
                error_details.append(error_msg)
                all_output.append(
                    f"=== Match Phase for {month} ===\nTIMEOUT: Command exceeded 5 minute limit\n"
                )
            except Exception as e:
                error_msg = f"❌ Match phase error for {month}: {e}"
                logger.error(error_msg)
                failed_months.append(month)
                error_details.append(error_msg)
                all_output.append(f"=== Match Phase for {month} ===\nERROR: {str(e)}\n")

        # Prepare response
        if failed_months:
            message = (
                f"Completed {success_count}/{len(request.months)} months. "
                f"Failed: {', '.join(failed_months)}"
            )
            success = False
        else:
            message = f"Successfully completed match phase for all {len(request.months)} months"
            success = True

        logger.info(f"Match phase summary: {message}")

        # Combine all output for display
        full_output = "\n".join(all_output)

        return MatchPhaseResponse(
            months=request.months,
            force=request.force,
            success=success,
            message=message,
            error_details=full_output if not success else full_output,  # Always include output
            processing_time=0.0,  # TODO: Add actual timing
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in match phase execution: {e}")
        raise HTTPException(status_code=500, detail=f"Error running match phase: {str(e)}")


@router.post("/unmatched", response_model=UnmatchedAnalysisResponse)
async def analyze_unmatched(request: UnmatchedAnalysisRequest) -> UnmatchedAnalysisResponse:
    """Analyze unmatched field values for the specified months."""
    try:
        # Validate input parameters
        validate_field(request.field)
        validate_months(request.months)

        logger.info(
            f"Starting unmatched analysis for field '{request.field}' "
            f"across {len(request.months)} months"
        )

        # Create analyzer instance
        if UnmatchedAnalyzer is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    "UnmatchedAnalyzer not available. "
                    "Please ensure the SOTD pipeline is properly installed."
                ),
            )
        analyzer = UnmatchedAnalyzer()

        # Process each month individually to handle non-sequential months correctly
        all_results = []

        for month in request.months:
            # Create args object for each month
            class Args:
                def __init__(self):
                    self.month = month  # Single month
                    self.year = None
                    self.range = None
                    self.start = None
                    self.end = None
                    self.field = request.field
                    self.limit = request.limit
                    self.out_dir = project_root / "data"
                    self.debug = False

            args = Args()

            try:
                # Process this month
                result = analyzer.analyze_unmatched(args)
                all_results.append(result)
                logger.info(f"Processed {month}: {result['total_unmatched']} unmatched items")
            except Exception as e:
                logger.warning(f"Error processing month {month}: {e}")
                continue

        # Combine results from all months
        if request.field == "brush":
            # For brush field, preserve detailed structure
            combined_unmatched = {}
            for result in all_results:
                for item in result["unmatched_items"]:
                    key = item["item"]
                    if key not in combined_unmatched:
                        combined_unmatched[key] = {
                            "examples": [],
                            "comment_ids": [],
                            "match_type": item.get("match_type"),
                            "matched": item.get("matched"),
                            "unmatched": item.get("unmatched"),
                        }
                    # Safely extend lists
                    examples = item.get("examples", [])
                    comment_ids = item.get("comment_ids", [])
                    if examples:
                        combined_unmatched[key]["examples"].extend(examples)
                    if comment_ids:
                        combined_unmatched[key]["comment_ids"].extend(comment_ids)
        else:
            # For other fields, use simple structure
            combined_unmatched = defaultdict(lambda: {"examples": [], "comment_ids": []})
            for result in all_results:
                for item in result["unmatched_items"]:
                    combined_unmatched[item["item"]]["examples"].extend(item.get("examples", []))
                    combined_unmatched[item["item"]]["comment_ids"].extend(
                        item.get("comment_ids", [])
                    )

        # Convert to response format
        unmatched_items = []
        # Sort alphabetically by value, then by count descending
        sorted_items = sorted(
            combined_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1]["examples"]))
        )[: request.limit]

        for original_text, data in sorted_items:
            # Deduplicate examples and comment_ids and limit to 5
            examples = data.get("examples", [])
            comment_ids = data.get("comment_ids", [])
            unique_examples = list(set(examples))[:5] if examples else []
            unique_comment_ids = list(set(comment_ids))[:5] if comment_ids else []

            if request.field == "brush":
                # For brush field, include detailed structure
                unmatched_items.append(
                    UnmatchedItem(
                        item=original_text,
                        count=len(examples) if examples else 0,
                        examples=unique_examples,
                        comment_ids=unique_comment_ids,
                        match_type=data.get("match_type"),
                        matched=data.get("matched"),
                        unmatched=data.get("unmatched"),
                    )
                )
            else:
                # For other fields, use simple structure
                unmatched_items.append(
                    UnmatchedItem(
                        item=original_text,
                        count=len(examples) if examples else 0,
                        examples=unique_examples,
                        comment_ids=unique_comment_ids,
                    )
                )

        total_unmatched = len(combined_unmatched)
        logger.info(f"Analysis complete. Found {total_unmatched} unmatched items across all months")

        return UnmatchedAnalysisResponse(
            field=request.field,
            months=request.months,
            total_unmatched=total_unmatched,
            unmatched_items=unmatched_items,
            processing_time=0.0,  # TODO: Add actual timing
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in unmatched analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error performing unmatched analysis: {str(e)}"
        )
