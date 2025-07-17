#!/usr/bin/env python3
"""Analysis endpoints for SOTD pipeline analyzer API."""

import logging
import sys
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for importing SOTD modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


class UnmatchedAnalysisRequest(BaseModel):
    """Request model for unmatched analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap)")
    months: List[str] = Field(..., description="List of months to analyze (YYYY-MM format)")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of results to return")


class UnmatchedAnalysisResult(BaseModel):
    """Result model for unmatched analysis."""

    original_text: str
    use_count: int
    source_files: List[str]
    source_lines: List[str]


class UnmatchedAnalysisResponse(BaseModel):
    """Response model for unmatched analysis."""

    field: str
    months: List[str]
    total_unmatched: int
    results: List[UnmatchedAnalysisResult]


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
        analyzer = UnmatchedAnalyzer()

        # Prepare analysis results
        all_unmatched = {}

        # Process each month
        for month in request.months:
            logger.info(f"Processing month: {month}")

            # Create args object for the analyzer
            class Args:
                def __init__(self):
                    self.month = month
                    self.field = request.field
                    self.limit = request.limit
                    self.out_dir = Path("data")
                    self.debug = False

            args = Args()

            try:
                # Load data for this month
                records = analyzer.load_matched_data(args)

                # Process unmatched records
                for record in records:
                    analyzer._process_field_unmatched(record, request.field, all_unmatched)

            except Exception as e:
                logger.warning(f"Error processing month {month}: {e}")
                # Continue with other months
                continue

        # Convert results to response format
        results = []
        for original_text, file_infos in list(all_unmatched.items())[: request.limit]:
            source_files = list(set(info["file"] for info in file_infos if info["file"]))
            source_lines = list(
                set(info["line"] for info in file_infos if info["line"] != "unknown")
            )

            results.append(
                UnmatchedAnalysisResult(
                    original_text=original_text,
                    use_count=len(file_infos),
                    source_files=source_files,
                    source_lines=source_lines,
                )
            )

        logger.info(f"Analysis complete. Found {len(results)} unmatched items")

        return UnmatchedAnalysisResponse(
            field=request.field,
            months=request.months,
            total_unmatched=len(all_unmatched),
            results=results,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in unmatched analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error performing unmatched analysis: {str(e)}"
        )
