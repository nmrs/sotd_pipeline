#!/usr/bin/env python3
"""Analysis endpoints for SOTD pipeline analyzer API."""

import logging
import os
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Get logger for this module
logger = logging.getLogger(__name__)

# Import the existing FilteredEntriesManager instead of duplicating logic
from sotd.utils.filtered_entries import FilteredEntriesManager  # noqa: E402

try:
    from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer  # noqa: E402
    from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer  # noqa: E402

    logger.info("✅ MismatchAnalyzer imported successfully")
    logger.info("✅ UnmatchedAnalyzer imported successfully")
except ImportError as e:
    # Fallback for development
    logger.error(f"❌ Failed to import analyzers: {e}")
    UnmatchedAnalyzer = None
    MismatchAnalyzer = None

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class UnmatchedAnalysisRequest(BaseModel):
    """Request model for unmatched analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap, soap_brand)")
    months: List[str] = Field(..., description="List of months to analyze (YYYY-MM format)")
    limit: int = Field(default=50, ge=1, description="Maximum number of results to return")


class MismatchAnalysisRequest(BaseModel):
    """Request model for mismatch analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap)")
    months: List[str] = Field(..., description="List of months to analyze (YYYY-MM format)")
    threshold: int = Field(default=3, ge=0, le=10, description="Levenshtein distance threshold")
    use_enriched_data: bool = Field(
        default=False, description="Use enriched data instead of matched data"
    )
    display_mode: Optional[str] = Field(
        default="mismatches",
        description=(
            "Display mode: 'mismatches' (default), 'matches' (confirmed matches only), or 'all'"
        ),
    )


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


class ProductFieldData(BaseModel):
    """Model for product field data (matched and enriched)."""

    original: str
    matched: Optional[Dict[str, Any]] = None
    enriched: Optional[Dict[str, Any]] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None


class CommentProductData(BaseModel):
    """Model for all product data in a comment."""

    razor: Optional[ProductFieldData] = None
    blade: Optional[ProductFieldData] = None
    brush: Optional[ProductFieldData] = None
    soap: Optional[ProductFieldData] = None


class CommentDetail(BaseModel):
    """Model for comment details."""

    id: str
    author: str
    body: str
    created_utc: str
    thread_id: str
    thread_title: str
    url: str
    product_data: Optional[CommentProductData] = None
    data_source: Optional[str] = None  # "enriched" or "matched"


class UnmatchedItem(BaseModel):
    """Model for individual unmatched item."""

    item: str
    count: int
    examples: List[str]
    comment_ids: List[str]
    unmatched: Optional[dict] = None


class UnmatchedAnalysisResponse(BaseModel):
    """Response model for unmatched analysis."""

    field: str
    months: List[str]
    total_unmatched: int
    unmatched_items: List[UnmatchedItem]
    processing_time: float
    partial_results: bool = False
    error: Optional[str] = None


class MismatchItem(BaseModel):
    """Model for individual mismatch item."""

    original: str
    normalized: Optional[str] = None  # Add normalized field for search functionality
    matched: dict
    enriched: Optional[dict] = None
    pattern: Optional[str] = None
    match_type: str
    confidence: Optional[float] = None
    mismatch_type: Optional[str] = None
    reason: Optional[str] = None
    count: int
    examples: List[str]
    comment_ids: List[str]
    # Source file information for each comment ID
    comment_sources: Dict[str, str] = Field(default_factory=dict)  # comment_id -> source_file
    is_confirmed: Optional[bool] = None
    # Strategy field for brush matching
    matched_by_strategy: Optional[str] = None


class MismatchAnalysisResponse(BaseModel):
    """Response model for mismatch analysis."""

    field: str
    months: List[str]  # Changed from month: str to months: List[str]
    total_matches: int
    total_mismatches: int
    mismatch_items: List[MismatchItem]
    processing_time: float
    partial_results: bool = False
    error: Optional[str] = None
    matched_data_map: Optional[Dict[str, Dict[str, Any]]] = None


class MarkCorrectRequest(BaseModel):
    """Request model for marking matches as correct."""

    field: str = Field(..., description="Field type (razor, blade, brush, soap)")
    matches: List[Dict[str, Any]] = Field(
        ..., description="List of matches with original and matched data to mark as correct"
    )
    force: bool = Field(default=False, description="Force operation without confirmation")


class MarkCorrectResponse(BaseModel):
    """Response model for marking matches as correct."""

    success: bool
    message: str
    marked_count: int
    errors: List[str] = []


class RemoveCorrectRequest(BaseModel):
    """Request model for removing matches from correct matches."""

    field: str = Field(..., description="Field type (razor, blade, brush, soap)")
    matches: List[Dict[str, Any]] = Field(
        ..., description="List of matches to remove from correct matches"
    )
    force: bool = Field(default=False, description="Force operation without confirmation")


class RemoveCorrectResponse(BaseModel):
    """Response model for removing matches from correct matches."""

    success: bool
    message: str
    removed_count: int
    errors: List[str] = []


class CorrectMatchesResponse(BaseModel):
    """Response model for correct matches data."""

    field: str
    total_entries: int
    entries: Dict[str, Any]


class CatalogValidationRequest(BaseModel):
    """Request model for catalog validation."""

    field: str = Field(..., description="Field to validate (razor, blade, brush, soap)")


class CatalogValidationIssue(BaseModel):
    """Model for catalog validation issue."""

    issue_type: str
    field: str
    format: Optional[str] = None  # Format field for blade validation
    correct_match: str
    expected_brand: Optional[str]
    expected_model: Optional[str]
    actual_brand: Optional[str]
    actual_model: Optional[str]
    expected_section: Optional[str] = None  # Expected section for structural changes
    actual_section: Optional[str] = None  # Actual section for structural changes
    severity: str
    suggested_action: str
    details: str
    catalog_format: Optional[str] = None  # Catalog format for format mismatch issues
    matched_pattern: Optional[str] = None  # Pattern that caused the match for mismatched results
    # Brush-specific match details
    current_match_details: Optional[dict] = None  # Current brush match details
    expected_handle_match: Optional[dict] = None  # Expected handle match details
    expected_knot_match: Optional[dict] = None  # Expected knot match details
    line_numbers: Optional[Dict[str, List[int]]] = (
        None  # Line numbers by section/file for duplicate/conflict issues
    )


class CatalogValidationResponse(BaseModel):
    """Response model for catalog validation."""

    field: str
    total_entries: int
    issues: List[CatalogValidationIssue]
    processing_time: float


def validate_field(field: str) -> None:
    """Validate that the field is supported."""
    supported_fields = ["razor", "blade", "brush", "soap", "soap_brand", "knot", "handle"]
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


def get_filtered_entries_manager() -> FilteredEntriesManager:
    """Get FilteredEntriesManager instance for intentionally unmatched data."""
    filtered_file = project_root / "data" / "intentionally_unmatched.yaml"
    manager = FilteredEntriesManager(filtered_file)
    manager.load()
    return manager


def find_comment_by_id(comment_id: str, months: List[str]) -> tuple[Optional[dict], Optional[str]]:
    """Find a comment by its ID across the specified months.

    Returns:
        Tuple of (comment_record, data_source) where data_source is "enriched" or "matched"
    """
    import json

    # First, try enriched files (which contain both matched and enriched data)
    for month in months:
        enriched_path = project_root / "data" / "enriched" / f"{month}.json"
        if enriched_path.exists():
            try:
                with enriched_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                for record in data.get("data", []):
                    if record.get("id") == comment_id:
                        return record, "enriched"
            except Exception as e:
                logger.warning(f"Error reading {enriched_path}: {e}")
                continue

    # Fallback to matched files
    for month in months:
        matched_path = project_root / "data" / "matched" / f"{month}.json"
        if matched_path.exists():
            try:
                with matched_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                for record in data.get("data", []):
                    if record.get("id") == comment_id:
                        return record, "matched"
            except Exception as e:
                logger.warning(f"Error reading {matched_path}: {e}")
                continue

    return None, None


def extract_product_field_data(field_data: Optional[Dict[str, Any]]) -> Optional[ProductFieldData]:
    """Extract product field data from a comment record field."""
    if not field_data or not isinstance(field_data, dict):
        return None

    return ProductFieldData(
        original=field_data.get("original", ""),
        matched=field_data.get("matched"),
        enriched=field_data.get("enriched"),
        match_type=field_data.get("match_type"),
        pattern=field_data.get("pattern"),
    )


@router.get("/comment/{comment_id}", response_model=CommentDetail)
async def get_comment_detail(comment_id: str, months: str) -> CommentDetail:
    """Get detailed information for a specific comment."""
    try:
        # Parse months parameter (comma-separated list)
        month_list = [m.strip() for m in months.split(",") if m.strip()]

        if not month_list:
            raise HTTPException(status_code=400, detail="At least one month must be specified")

        # Find the comment
        comment, data_source = find_comment_by_id(comment_id, month_list)

        if not comment:
            raise HTTPException(
                status_code=404, detail=f"Comment {comment_id} not found in the specified months"
            )

        # Extract product data
        product_data = CommentProductData(
            razor=extract_product_field_data(comment.get("razor")),
            blade=extract_product_field_data(comment.get("blade")),
            brush=extract_product_field_data(comment.get("brush")),
            soap=extract_product_field_data(comment.get("soap")),
        )

        # Only include product_data if at least one field has data
        has_product_data = any(
            [
                product_data.razor,
                product_data.blade,
                product_data.brush,
                product_data.soap,
            ]
        )

        return CommentDetail(
            id=comment.get("id", ""),
            author=comment.get("author", ""),
            body=comment.get("body", ""),
            created_utc=comment.get("created_utc", ""),
            thread_id=comment.get("thread_id", ""),
            thread_title=comment.get("thread_title", ""),
            url=comment.get("url", ""),
            product_data=product_data if has_product_data else None,
            data_source=data_source,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching comment: {str(e)}")


@router.post("/match-phase", response_model=MatchPhaseResponse)
async def run_match_phase(request: MatchPhaseRequest) -> MatchPhaseResponse:
    """Run match phase on specified months."""
    logger.info(f"🎯 Starting match phase for months: {request.months}, force: {request.force}")
    start_time = time.time()
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

        processing_time = time.time() - start_time
        logger.info(f"✅ Match phase completed in {processing_time:.2f}s - {message}")
        return MatchPhaseResponse(
            months=request.months,
            force=request.force,
            success=success,
            message=message,
            error_details=full_output if not success else full_output,  # Always include output
            processing_time=processing_time,
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
                    self.delta_months = None  # Add this to match month_span function
                    self.field = request.field
                    self.limit = request.limit
                    self.out_dir = project_root / "data"
                    self.debug = False

            args = Args()

            try:
                # Use the same logic as command line tool - call analyze_unmatched directly
                result = analyzer.analyze_unmatched(args)
                all_results.append(result)
                logger.info(f"Processed {month}: {len(result)} unmatched items")
            except Exception as e:
                logger.warning(f"Error processing month {month}: {e}")
                continue

        # Combine results from all months using the same logic as command line tool
        combined_unmatched = defaultdict(list)

        for result in all_results:
            for item, file_infos in result.items():
                # For brush field, use case-insensitive grouping
                if request.field == "brush":
                    # Use lowercase as the key for case-insensitive grouping
                    key = item.lower()
                    combined_unmatched[key].extend(file_infos)
                else:
                    # For other fields, use the original item as key
                    combined_unmatched[item].extend(file_infos)

        # Convert to response format
        unmatched_items = []
        case_groups = {}  # Initialize for both brush and non-brush cases

        # For brush field, we need to handle case-insensitive grouping
        if request.field == "brush":
            # Use the first occurrence of each case-insensitive group as the display text
            for key, file_infos in combined_unmatched.items():
                # Find the first occurrence of this key in the original results
                first_occurrence = None
                for result in all_results:
                    for item, _ in result.items():
                        if item.lower() == key:
                            first_occurrence = item
                            break
                    if first_occurrence:
                        break

                # Use the first occurrence, or the key if not found
                display_text = first_occurrence or key
                case_groups[display_text] = file_infos

            # Sort by the display text (alphabetically), then by count descending
            sorted_items = sorted(case_groups.items(), key=lambda x: (x[0].lower(), -len(x[1])))[
                : request.limit
            ]
        else:
            # For other fields, use the original sorting logic
            sorted_items = sorted(
                combined_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1]))
            )[: request.limit]

        for original_text, file_infos in sorted_items:
            # Extract comment IDs and examples from file_infos (same as command line tool)
            comment_ids = [
                info.get("comment_id", "") for info in file_infos if info.get("comment_id")
            ]
            examples = [info.get("file", "") for info in file_infos]

            # Sort comment IDs by month (newest first) - return ALL comment IDs
            unique_comment_ids = []
            if comment_ids:
                # Get all comment IDs with their source files, prioritizing newer months
                comment_files = {}
                for info in file_infos:
                    comment_id = info.get("comment_id", "")
                    if comment_id:
                        # Get source file (month) for sorting
                        source_file = info.get("file", "")
                        # Only keep if we haven't seen this comment_id, or if this month is newer
                        if (
                            comment_id not in comment_files
                            or source_file > comment_files[comment_id]
                        ):
                            comment_files[comment_id] = source_file

                # Sort by filename (month) newest first - return ALL comment IDs
                sorted_comments = sorted(comment_files.items(), key=lambda x: x[1], reverse=True)
                unique_comment_ids = [comment_id for comment_id, _ in sorted_comments]

            unique_examples = list(set(examples))[:5] if examples else []

            # Extract unmatched components data for brush field
            unmatched_components = None
            if request.field == "brush" and file_infos:
                # Check if any file_info has unmatched_components
                for file_info in file_infos:
                    if isinstance(file_info, dict) and "unmatched_components" in file_info:
                        unmatched_components = file_info["unmatched_components"]
                        break

            unmatched_items.append(
                UnmatchedItem(
                    item=original_text,
                    count=len(file_infos),
                    examples=unique_examples,
                    comment_ids=unique_comment_ids,
                    unmatched=unmatched_components,
                )
            )

        # Use the correct total count based on field type
        if request.field == "brush":
            total_unmatched = len(case_groups)
        else:
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


@router.get("/debug/version")
async def debug_version():
    """Debug endpoint to check if the server is using updated code."""
    return {"message": "Updated code loaded", "timestamp": "2025-01-27 16:30"}


@router.post("/clear-validator-cache")
async def clear_validator_cache():
    """Clear the validator cache to force a fresh validation."""
    try:
        # Clear validator cache - this endpoint is no longer needed with actual matching validation
        # but keeping for backward compatibility
        logger.info(
            "Validator cache clear requested - no longer needed with actual matching validation"
        )

        logger.info("✅ Validator cache cleared successfully")
        return {"success": True, "message": "Validator cache cleared successfully"}
    except Exception as e:
        logger.error(f"❌ Failed to clear validator cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear validator cache: {str(e)}")


@router.post("/mismatch", response_model=MismatchAnalysisResponse)
async def analyze_mismatch(request: MismatchAnalysisRequest) -> MismatchAnalysisResponse:
    """Analyze mismatches in matched data for the specified month."""
    try:
        # Validate input parameters
        validate_field(request.field)
        validate_months(request.months)

        logger.info(
            f"Starting mismatch analysis for field '{request.field}' for months {request.months}"
        )

        # Create analyzer instance
        if MismatchAnalyzer is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    "MismatchAnalyzer not available. "
                    "Please ensure the SOTD pipeline is properly installed."
                ),
            )
        # Create analyzer with console for proper error handling
        from rich.console import Console

        console = Console()
        analyzer = MismatchAnalyzer(console)

        # Create args object for the analyzer
        class Args:
            def __init__(self):
                # Handle multiple months using delta_months
                if len(request.months) == 1:
                    # Single month - use month field
                    self.month = request.months[0]
                    self.delta_months = None
                else:
                    # Multiple months - use delta_months with comma-separated list
                    self.month = None
                    self.delta_months = ",".join(request.months)

                self.year = None
                self.range = None
                self.start = None
                self.end = None
                self.field = request.field
                self.threshold = request.threshold
                self.out_dir = project_root / "data"
                self.debug = False
                self.force = False
                self.mark_correct = False
                self.dry_run = False
                self.no_confirm = False
                self.clear_correct = False
                self.clear_field = None
                self.show_correct = True
                self.test_correct_matches = None
                self.use_enriched_data = request.use_enriched_data

        args = Args()

        # Load data using the analyzer's method
        try:
            # Always load matched data for comparison
            matched_records = analyzer.load_matched_data(args)

            if request.use_enriched_data:
                logger.info("Using enriched data for mismatch analysis")
                enriched_records = analyzer.load_enriched_data(args)
                # Create a mapping of matched data by record ID for comparison
                matched_data_map = {}
                for record in matched_records:
                    record_id = record.get("id", "")
                    if record_id:
                        matched_data_map[record_id] = record

                # Use enriched data for analysis but keep matched data for comparison
                records = enriched_records
                data = {"data": records, "matched_data_map": matched_data_map}
            else:
                records = matched_records
                data = {"data": records}
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

        # Load correct matches first - this is required for identify_mismatches to work correctly
        # Fail fast per core rules - if loading fails, we want to know immediately
        try:
            analyzer._load_correct_matches()
            logger.info(f"Loaded {len(analyzer._correct_matches)} correct matches")
        except Exception as e:
            logger.error(f"Failed to load correct matches: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Failed to load correct matches: {str(e)}. "
                    f"This is required for mismatch analysis."
                ),
            )

        # Use the analyzer's logic directly - DRY principle
        mismatches = analyzer.identify_mismatches(data, request.field, args)

        # Convert analyzer results to API response format
        all_items = []
        total_matches = len(records)
        total_mismatches = 0

        # Process all mismatch categories from analyzer
        for mismatch_type, items in mismatches.items():
            logger.info(f"Processing category '{mismatch_type}' with {len(items)} items")

            # Skip certain categories based on display mode if specified
            if hasattr(request, "display_mode") and request.display_mode:
                if request.display_mode == "matches":
                    # For matches mode, only show confirmed matches
                    if mismatch_type not in ["exact_matches", "good_matches"]:
                        continue
                    # Only include items that are confirmed
                    items = [item for item in items if item.get("is_confirmed", False)]
                    if not items:
                        continue
                elif request.display_mode == "mismatches":
                    # For mismatches mode, exclude confirmed matches
                    if mismatch_type in ["exact_matches", "good_matches"]:
                        continue
                elif request.display_mode == "unconfirmed":
                    # For unconfirmed mode, only show unconfirmed items
                    if mismatch_type in ["exact_matches", "good_matches"]:
                        continue
                    items = [item for item in items if not item.get("is_confirmed", False)]
                    if not items:
                        continue
                elif request.display_mode == "regex":
                    # For regex mode, only show regex-related mismatches
                    if mismatch_type not in ["multiple_patterns"]:
                        continue
                elif request.display_mode == "intentionally_unmatched":
                    # For intentionally unmatched mode, only show those items
                    if mismatch_type != "intentionally_unmatched":
                        continue
                elif request.display_mode == "complete_brushes":
                    # For complete brushes mode, only show split brush items
                    # Filter out items that don't meet the threshold
                    items = [item for item in items if item.get("count", 0) >= request.threshold]
                    if not items:
                        continue
                # 'all' mode shows everything, so no filtering needed

            for item in items:
                record = item["record"]
                field_data = item.get("field_data", {})

                # If field_data is not available, try to get it from the record
                if not field_data:
                    field_data = record.get(request.field, {})

                original = field_data.get("original", "")
                normalized = field_data.get("normalized", original)
                pattern = field_data.get("pattern", "")
                match_type = field_data.get("match_type", "")
                record_id = record.get("id", "")

                # Handle intentionally unmatched items differently - they don't have matched data
                if mismatch_type == "intentionally_unmatched":
                    # For intentionally unmatched items, use empty matched dict and set
                    # match_type to "filtered"
                    matched = {}
                    enriched = {}
                    match_type = "filtered"
                else:
                    # When using enriched data, get original matched data from matched_data_map
                    if request.use_enriched_data and data.get("matched_data_map"):
                        # Get the original matched data from the matched_data_map
                        matched_data_map = data["matched_data_map"]
                        # Type guard: ensure matched_data_map is a dict
                        if isinstance(matched_data_map, dict):
                            matched_record = matched_data_map.get(record_id, {})
                            matched_field_data = matched_record.get(request.field, {})
                            matched = matched_field_data.get("matched", {})
                        else:
                            matched = {}
                        enriched = field_data.get("enriched", {})
                    else:
                        # Using matched data directly
                        matched = field_data.get("matched", {})
                        enriched = field_data.get("enriched", {})

                    # Skip records with missing data for other categories
                    if not normalized or not matched:
                        continue

                # Extract strategy field from matched data for brush field
                matched_by_strategy = None
                if request.field == "brush":
                    # First try to get from matched data
                    if matched:
                        matched_by_strategy = matched.get("_matched_by_strategy") or matched.get(
                            "strategy"
                        )
                        logger.debug(f"Strategy from matched data: {matched_by_strategy}")

                    # If no strategy in matched data, determine based on match characteristics
                    if not matched_by_strategy:
                        logger.debug(f"Determining strategy from match_type: {match_type}")
                        if match_type == "composite":
                            matched_by_strategy = "dual_component"
                        elif match_type == "split_brush":
                            matched_by_strategy = "automated_split"
                        elif match_type == "regex":
                            matched_by_strategy = "complete_brush"
                        elif match_type == "brand_default":
                            matched_by_strategy = "brand_fallback"
                        elif match_type == "knot_only":
                            matched_by_strategy = "knot_only"
                        elif match_type == "handle_only":
                            matched_by_strategy = "handle_only"
                        else:
                            matched_by_strategy = "unknown"
                        logger.debug(f"Determined strategy: {matched_by_strategy}")

                    logger.debug(f"Final strategy for {normalized}: {matched_by_strategy}")

                # Use analyzer's results directly
                is_confirmed = item.get("is_confirmed", False)
                reason = item.get("reason", "")

                # Create API response item
                source_file = record.get("_source_file", "")
                comment_sources = {}
                if record_id and source_file:
                    comment_sources[str(record_id)] = source_file

                api_item = MismatchItem(
                    original=normalized,
                    matched=matched,
                    enriched=enriched if enriched else None,
                    pattern=pattern,
                    match_type=match_type or "No Match",
                    confidence=field_data.get("confidence"),
                    mismatch_type=mismatch_type,
                    reason=reason,
                    count=1,
                    examples=([str(source_file)] if source_file else []),
                    comment_ids=[str(record_id)] if record_id else [],
                    comment_sources=comment_sources,
                    is_confirmed=is_confirmed,
                    matched_by_strategy=matched_by_strategy,
                    # Split brush fields from analyzer results
                )

                all_items.append(api_item)

                # Count mismatches (excluding good_matches and exact_matches)
                if mismatch_type not in ["good_matches", "exact_matches"]:
                    total_mismatches += 1

        # Group identical items together (case-insensitive)
        grouped_items = {}
        for item in all_items:
            group_key = item.original.lower()

            if group_key in grouped_items:
                # Merge with existing item
                existing = grouped_items[group_key]
                existing.count += item.count
                existing.examples.extend(item.examples)
                existing.comment_ids.extend(item.comment_ids)
                # Merge comment sources
                existing.comment_sources.update(item.comment_sources)
                # Keep the highest confidence if available
                if item.confidence is not None and (
                    existing.confidence is None or item.confidence > existing.confidence
                ):
                    existing.confidence = item.confidence
            else:
                # Create new grouped item
                grouped_items[group_key] = item

        # Convert back to list and sort
        all_items = list(grouped_items.values())
        all_items.sort(key=lambda x: (x.mismatch_type or "", x.original.lower()))

        logger.info(
            f"Mismatch analysis: total_records={len(records)}, "
            f"returned={len(all_items)}, "
            f"total_matches={total_matches}, "
            f"total_mismatches={total_mismatches}"
        )

        return MismatchAnalysisResponse(
            field=request.field,
            months=request.months,
            total_matches=total_matches,
            total_mismatches=total_mismatches,
            mismatch_items=all_items,
            processing_time=0.0,
            partial_results=False,
            error=None,
            matched_data_map=(data.get("matched_data_map") if request.use_enriched_data else None),  # type: ignore
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in mismatch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing mismatches: {str(e)}")


@router.get("/correct-matches/{field}", response_model=CorrectMatchesResponse)
async def get_correct_matches(field: str):
    """Get correct matches for a specific field."""
    try:
        validate_field(field)

        # Load correct matches from directory structure
        correct_matches_dir = project_root / "data" / "correct_matches"
        if not correct_matches_dir.exists():
            return CorrectMatchesResponse(field=field, total_entries=0, entries={})

        import yaml

        data = {}
        # Initialize field_data early to avoid unbound variable errors
        field_data: Dict[str, Any] = {}

        # For brush field, combine data from brush, handle, and knot sections
        if field == "brush":
            # Load brush, handle, and knot files
            for section in ["brush", "handle", "knot"]:
                section_file = correct_matches_dir / f"{section}.yaml"
                if section_file.exists():
                    try:
                        with section_file.open("r", encoding="utf-8") as f:
                            section_data = yaml.safe_load(f) or {}
                            if section_data:
                                data[section] = section_data
                    except Exception as e:
                        logger.warning(f"Error loading {section_file}: {e}")

            brush_data = data.get("brush", {})
            handle_data = data.get("handle", {})
            knot_data = data.get("knot", {})

            # Combine all sections for composite brush confirmation logic
            combined_data = {
                "brush": brush_data,
                "handle": handle_data,
                "knot": knot_data,
            }

            logger.info(
                f"Brush field data - brush: {brush_data}, handle: {handle_data}, knot: {knot_data}"
            )
        else:
            # Load field-specific file
            field_file = correct_matches_dir / f"{field}.yaml"
            if field_file.exists():
                try:
                    with field_file.open("r", encoding="utf-8") as f:
                        field_data = yaml.safe_load(f) or {}
                        if field_data:
                            data[field] = field_data
                except Exception as e:
                    logger.warning(f"Error loading {field_file}: {e}")

            field_data = data.get(field, {})
            combined_data = field_data
            logger.info(f"Field data for '{field}': {field_data}")

        # Check for malformed YAML with None keys and fail fast
        def check_for_none_keys(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k is None:
                        raise ValueError(
                            f"Malformed YAML: Found None key in "
                            f"correct_matches directory at path '{path}'. "
                            f"This indicates a corrupted YAML file that "
                            f"needs to be fixed."
                        )
                    check_for_none_keys(v, f"{path}.{k}" if path else str(k))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_none_keys(item, f"{path}[{i}]")

        check_for_none_keys(data)
        logger.info(f"Loaded data keys: {list(data.keys())}")

        # Calculate total entries based on field structure
        total_entries = 0
        if field == "blade":
            # Blade can have either format -> brand -> model -> strings structure
            # or brand -> model -> strings structure (flat)
            for first_level in field_data.values():
                if isinstance(first_level, dict):
                    # Check if this is format structure (has brands as values)
                    # or brand structure (has models as values)
                    sample_value = next(iter(first_level.values())) if first_level else None
                    if isinstance(sample_value, dict):
                        # Format structure: format -> brand -> model -> strings
                        for brand_data in first_level.values():
                            if isinstance(brand_data, dict):
                                for model_data in brand_data.values():
                                    if isinstance(model_data, list):
                                        total_entries += len(model_data)
                    else:
                        # Brand structure: brand -> model -> strings
                        for model_data in first_level.values():
                            if isinstance(model_data, list):
                                total_entries += len(model_data)
        elif field == "brush":
            # For brush field, count entries from all sections (brush, handle, knot)
            total_entries = 0

            # Count brush section entries
            brush_data = data.get(field, {})
            total_entries += sum(
                len(strings) if isinstance(strings, list) else 0
                for brand_data in brush_data.values()
                if isinstance(brand_data, dict)
                for strings in brand_data.values()
            )

            # Count handle section entries
            handle_data = data.get("handle", {})
            total_entries += sum(
                len(strings) if isinstance(strings, list) else 0
                for brand_data in handle_data.values()
                if isinstance(brand_data, dict)
                for strings in brand_data.values()
            )

            # Count knot section entries
            knot_data = data.get("knot", {})
            total_entries += sum(
                len(strings) if isinstance(strings, list) else 0
                for brand_data in knot_data.values()
                if isinstance(brand_data, dict)
                for strings in brand_data.values()
            )
        else:
            # Other fields have brand -> model -> strings structure
            total_entries = sum(
                len(strings) if isinstance(strings, list) else 0
                for brand_data in field_data.values()
                if isinstance(brand_data, dict)
                for strings in brand_data.values()
            )

        return CorrectMatchesResponse(
            field=field, total_entries=total_entries, entries=combined_data
        )

    except Exception as e:
        logger.error(f"Error loading correct matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading correct matches: {str(e)}")


@router.post("/mark-correct", response_model=MarkCorrectResponse)
async def mark_matches_as_correct(request: MarkCorrectRequest):
    """Mark matches as correct and save to correct_matches directory."""
    try:
        validate_field(request.field)

        if not request.matches:
            return MarkCorrectResponse(success=False, message="No matches provided", marked_count=0)

        # Import the correct matches manager
        try:
            from rich.console import Console

            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
        except ImportError as e:
            raise HTTPException(
                status_code=500, detail=f"Could not import CorrectMatchesManager: {e}"
            )

        # Create manager instance with correct file path
        # Use directory structure for field-specific files
        console = Console()
        correct_matches_path = project_root / "data" / "correct_matches"
        manager = CorrectMatchesManager(console, correct_matches_path)

        # Load existing correct matches
        manager.load_correct_matches()

        marked_count = 0
        errors = []

        for match in request.matches:
            try:
                original = match.get("original", "")
                matched = match.get("matched", {})

                if not original or not matched:
                    errors.append(f"Invalid match data: {match}")
                    continue

                # Debug logging
                logger.info(f"Processing match - original: {original}, matched: {matched}")
                logger.info(
                    f"DEBUG: Match data structure - field: {request.field}, original: {original}"
                )
                logger.info(
                    f"DEBUG: Matched data keys: {list(matched.keys()) if matched else 'None'}"
                )
                logger.info(f"DEBUG: Matched data content: {matched}")

                # For blade field, ensure format is preserved for correct section placement
                if request.field == "blade" and "format" in matched:
                    logger.info(f"Blade format detected: {matched['format']}")
                    # Ensure the format field is preserved in the match data
                    match_data_to_save = {
                        "original": original,
                        "matched": matched,
                        "field": request.field,
                    }
                else:
                    # For non-blade fields or blade fields without format, use standard structure
                    match_data_to_save = {
                        "original": original,
                        "matched": matched,
                        "field": request.field,
                    }

                # Use the proper method to mark as correct
                match_key = manager.create_match_key(request.field, original, matched)
                logger.info(f"DEBUG: Created match_key: {match_key}")
                logger.info(f"DEBUG: Match data to save: {match_data_to_save}")
                manager.mark_match_as_correct(match_key, match_data_to_save)
                logger.info("DEBUG: Marked match as correct, key stored in manager")
                marked_count += 1

            except Exception as e:
                errors.append(f"Error marking match {match}: {e}")

        # Save to file
        if marked_count > 0:
            logger.info(f"DEBUG: Saving {marked_count} matches to correct_matches directory")
            manager.save_correct_matches()
            logger.info("DEBUG: Saved correct matches to file")
            # Reload to verify it was saved
            manager.load_correct_matches()
            logger.info("DEBUG: Reloaded correct matches, verifying saved keys...")
            for match in request.matches:
                original = match.get("original", "")
                matched = match.get("matched", {})
                if original and matched:
                    verify_key = manager.create_match_key(request.field, original, matched)
                    is_found = verify_key in manager._correct_matches
                    logger.info(f"DEBUG: Verification - key: {verify_key}, found: {is_found}")
                    if not is_found:
                        logger.warning(f"DEBUG: WARNING - Key {verify_key} not found after save!")

        return MarkCorrectResponse(
            success=marked_count > 0,
            message=f"Marked {marked_count} matches as correct",
            marked_count=marked_count,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Error marking matches as correct: {e}")
        raise HTTPException(status_code=500, detail=f"Error marking matches as correct: {str(e)}")


@router.post("/remove-correct", response_model=RemoveCorrectResponse)
async def remove_matches_from_correct(request: RemoveCorrectRequest):
    """Remove matches from correct matches and save to correct_matches directory."""
    try:
        validate_field(request.field)

        if not request.matches:
            return RemoveCorrectResponse(
                success=False, message="No matches provided", removed_count=0
            )

        # Import the correct matches manager
        try:
            from rich.console import Console

            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
        except ImportError as e:
            raise HTTPException(
                status_code=500, detail=f"Could not import CorrectMatchesManager: {e}"
            )

        # Create manager instance with correct file path
        # Use directory structure for field-specific files
        console = Console()
        correct_matches_path = project_root / "data" / "correct_matches"
        manager = CorrectMatchesManager(console, correct_matches_path)

        # Load existing correct matches
        manager.load_correct_matches()

        removed_count = 0
        errors = []

        for match in request.matches:
            try:
                original = match.get("original", "")
                matched = match.get("matched", {})

                if not original or not matched:
                    errors.append(f"Invalid match data: {match}")
                    continue

                # Use the manager's remove_match method
                if manager.remove_match(request.field, original, matched):
                    removed_count += 1
                else:
                    errors.append(f"Match not found in correct matches: {original}")

            except Exception as e:
                errors.append(f"Error removing match {match}: {e}")

        # Save to file
        if removed_count > 0:
            manager.save_correct_matches()

        return RemoveCorrectResponse(
            success=removed_count > 0,
            message=f"Removed {removed_count} matches from correct matches",
            removed_count=removed_count,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Error removing matches from correct matches: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error removing matches from correct matches: {str(e)}"
        )


@router.delete("/correct-matches/{field}")
async def clear_correct_matches_by_field(field: str):
    """Clear correct matches for a specific field."""
    try:
        validate_field(field)

        # Import the correct matches manager
        try:
            from rich.console import Console

            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
        except ImportError as e:
            raise HTTPException(
                status_code=500, detail=f"Could not import CorrectMatchesManager: {e}"
            )

        # Create manager instance and clear field
        console = Console()
        correct_matches_path = project_root / "data" / "correct_matches"
        manager = CorrectMatchesManager(console, correct_matches_path)
        manager.load_correct_matches()
        manager.clear_correct_matches_by_field(field)

        return {"success": True, "message": f"Cleared correct matches for {field}"}

    except Exception as e:
        logger.error(f"Error clearing correct matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing correct matches: {str(e)}")


@router.delete("/correct-matches")
async def clear_all_correct_matches():
    """Clear all correct matches."""
    try:
        # Import the correct matches manager
        try:
            from rich.console import Console

            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
        except ImportError as e:
            raise HTTPException(
                status_code=500, detail=f"Could not import CorrectMatchesManager: {e}"
            )

        # Create manager instance and clear all
        console = Console()
        correct_matches_path = project_root / "data" / "correct_matches"
        manager = CorrectMatchesManager(console, correct_matches_path)
        manager.clear_correct_matches()

        return {"success": True, "message": "Cleared all correct matches"}

    except Exception as e:
        logger.error(f"Error clearing all correct matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing all correct matches: {str(e)}")


@router.post("/validate-catalog", response_model=CatalogValidationResponse)
async def validate_catalog_against_correct_matches(request: CatalogValidationRequest):
    """Validate catalog entries against correct_matches directory using
    actual matching validation."""
    logger.info(f"🔍 Starting actual matching validation for field: {request.field}")

    try:
        # Import the new ActualMatchingValidator
        from sotd.validate.actual_matching_validator import ActualMatchingValidator

        # Set up paths
        api_project_root = Path(__file__).parent.parent.parent
        correct_matches_path = api_project_root / "data" / "correct_matches"

        logger.info(f"Project root: {api_project_root}")
        logger.info(f"Correct matches path: {correct_matches_path}")
        logger.info(f"Path exists: {correct_matches_path.exists()}")

        # Change to project root directory to fix path resolution issues
        # This ensures matchers can find catalog files using relative paths
        original_cwd = Path.cwd()
        os.chdir(api_project_root)
        logger.info(f"Changed working directory from {original_cwd} to {Path.cwd()}")

        # Clear ALL caches to ensure fresh data on every validation
        from sotd.match.base_matcher import clear_catalog_cache
        from sotd.match.brush.matcher import clear_brush_catalog_cache
        from sotd.match.loaders import clear_yaml_cache

        clear_catalog_cache()
        clear_yaml_cache()
        clear_brush_catalog_cache()
        logger.info("Cleared all catalog caches for fresh data")

        # Create the actual matching validator
        validator = ActualMatchingValidator(data_path=api_project_root / "data")
        logger.info(f"Created ActualMatchingValidator: {type(validator)}")

        # Run validation
        logger.info(f"Running actual matching validation for field: {request.field}")
        start_time = time.time()
        validation_result = validator.validate(request.field)
        processing_time = time.time() - start_time

        logger.info(f"Validation completed in {processing_time:.2f}s")
        logger.info(f"Found {len(validation_result.issues)} issues")

        # Process issues for frontend consumption
        processed_issues = []
        for issue in validation_result.issues:
            # Map issue types from ActualMatchingValidator to frontend expected types
            if issue.issue_type == "no_match":
                mapped_issue_type = "no_match"
            elif issue.issue_type == "data_mismatch":
                mapped_issue_type = "data_mismatch"
            elif issue.issue_type == "structural_change":
                mapped_issue_type = "structural_change"
            elif issue.issue_type == "duplicate_string":
                mapped_issue_type = "duplicate_string"
            elif issue.issue_type == "cross_section_conflict":
                mapped_issue_type = "cross_section_conflict"
            else:
                # Keep other issue types as-is
                mapped_issue_type = issue.issue_type

            processed_issue = {
                "issue_type": mapped_issue_type,
                "field": request.field,
                "format": getattr(issue, "format", None),  # Format section for blades (AC, DE, etc.)
                "correct_match": issue.correct_match,
                "expected_brand": issue.expected_brand,
                "expected_model": issue.expected_model,
                "actual_brand": issue.actual_brand,
                "actual_model": issue.actual_model,
                "expected_section": issue.expected_section,
                "actual_section": issue.actual_section,
                "severity": issue.severity,
                "suggested_action": issue.suggested_action,
                "details": issue.details,
                "catalog_format": getattr(issue, "catalog_format", None),  # Actual format from matcher
                "matched_pattern": getattr(issue, "matched_pattern", None),  # Regex pattern that matched
                "line_numbers": getattr(
                    issue, "line_numbers", None
                ),  # Line numbers for duplicate/conflict issues
            }

            # For structural_change issues with brush data, add match details
            if issue.issue_type == "structural_change":
                # Add current brush match details (from correct_matches directory)
                if issue.expected_section == "brush":
                    processed_issue["current_match_details"] = {
                        "brand": issue.expected_brand,
                        "model": issue.expected_model,
                    }

                # Add expected handle/knot match details (from current matcher)
                if issue.actual_section == "handle_knot":
                    if hasattr(issue, "actual_handle_brand") and issue.actual_handle_brand:
                        processed_issue["expected_handle_match"] = {
                            "brand": issue.actual_handle_brand,
                            "model": issue.actual_handle_model,
                        }
                    if hasattr(issue, "actual_knot_brand") and issue.actual_knot_brand:
                        processed_issue["expected_knot_match"] = {
                            "brand": issue.actual_knot_brand,
                            "model": issue.actual_knot_model,
                        }
                        # Add fiber and knot size if available
                        actual_knot_fiber = getattr(issue, "actual_knot_fiber", None)
                        if actual_knot_fiber:
                            processed_issue["expected_knot_match"]["fiber"] = actual_knot_fiber
                        actual_knot_size_mm = getattr(issue, "actual_knot_size_mm", None)
                        if actual_knot_size_mm:
                            processed_issue["expected_knot_match"][
                                "knot_size_mm"
                            ] = actual_knot_size_mm

            processed_issues.append(processed_issue)

        logger.info(f"Returning {len(processed_issues)} processed issues")

        # Restore original working directory
        os.chdir(original_cwd)
        logger.info(f"Restored working directory to {Path.cwd()}")

        return {
            "field": request.field,
            "total_entries": validation_result.total_entries,
            "issues": processed_issues,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"Error validating catalog: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/remove-catalog-entries", response_model=RemoveCorrectResponse)
async def remove_catalog_validation_entries(request: RemoveCorrectRequest):
    """Remove entries from correct_matches directory based on catalog validation issues."""
    try:
        validate_field(request.field)

        if not request.matches:
            return RemoveCorrectResponse(
                success=False, message="No entries provided", removed_count=0
            )

        # Import required modules for direct YAML manipulation
        try:
            import yaml
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Could not import required modules: {e}")

        # Load and manipulate YAML from directory structure
        correct_matches_dir = project_root / "data" / "correct_matches"

        if not correct_matches_dir.exists():
            return RemoveCorrectResponse(
                success=False, message="Correct matches directory not found", removed_count=0
            )

        # Load YAML files from directory structure
        yaml_data = {}

        # Check if any entries are cross-section conflicts
        has_cross_section_conflict = any(
            entry.get("issue_type") == "cross_section_conflict" for entry in request.matches
        )

        # Determine which sections to load
        if has_cross_section_conflict:
            # For cross-section conflicts, load all brush-related sections
            sections_to_load = ["brush", "handle", "knot"]
        elif request.field == "brush":
            sections_to_load = ["brush", "handle", "knot"]
        else:
            sections_to_load = [request.field]

        for section in sections_to_load:
            section_file = correct_matches_dir / f"{section}.yaml"
            if section_file.exists():
                try:
                    with section_file.open("r", encoding="utf-8") as f:
                        section_data = yaml.safe_load(f) or {}
                        if section_data:
                            yaml_data[section] = section_data
                except Exception as e:
                    logger.warning(f"Error loading {section_file}: {e}")

        removed_count = 0
        errors = []

        for entry in request.matches:
            try:
                correct_match = entry.get("correct_match", "")
                actual_section = entry.get("actual_section", request.field)
                issue_type = entry.get("issue_type", "")
                expected_format = entry.get("format")  # Format section for blades (AC, DE, etc.)

                if not correct_match:
                    errors.append(f"Invalid entry data: {entry}")
                    continue

                # Remove from the hierarchical structure
                removed = False

                # Determine which sections to search based on field and issue type
                if issue_type == "cross_section_conflict":
                    # For cross-section conflicts, search in all brush-related sections
                    # regardless of the selected field
                    sections_to_search = ["brush", "knot", "handle"]
                elif request.field == "brush":
                    # For brush field, search across brush, knot, and handle sections
                    sections_to_search = ["brush", "knot", "handle"]
                else:
                    sections_to_search = [actual_section]

                for section in sections_to_search:
                    if section in yaml_data:
                        section_data = yaml_data[section]

                        # For blades, handle format-based structure
                        if request.field == "blade" and section_data:
                            # Check if structure is format-based (top-level keys are format names)
                            is_format_based = (
                                isinstance(section_data, dict)
                                and any(
                                    isinstance(v, dict)
                                    and any(
                                        isinstance(brand_data, dict)
                                        and any(isinstance(model_data, list) for model_data in brand_data.values())
                                        for brand_data in v.values()
                                    )
                                    for v in section_data.values()
                                )
                            )

                            if is_format_based:
                                # Iterate through format sections first, then brands, then models
                                # If expected_format is provided, only search in that format section
                                # Otherwise, search all format sections (for backward compatibility)
                                format_sections_to_search = (
                                    [expected_format] if expected_format else list(section_data.keys())
                                )
                                
                                for format_name in format_sections_to_search:
                                    if format_name not in section_data:
                                        continue
                                    format_data = section_data[format_name]
                                    if not isinstance(format_data, dict):
                                        continue
                                    for brand, brand_data in format_data.items():
                                        if isinstance(brand_data, dict):
                                            for model, patterns in brand_data.items():
                                                if isinstance(patterns, list):
                                                    # Look for the exact match (case-insensitive) and
                                                    # remove ALL occurrences
                                                    i = 0
                                                    while i < len(patterns):
                                                        pattern = patterns[i]
                                                        if (
                                                            isinstance(pattern, str)
                                                            and pattern.lower() == correct_match.lower()
                                                        ):
                                                            # Found the match, remove it
                                                            patterns.pop(i)
                                                            removed = True
                                                            removed_count += 1
                                                            # Don't increment i since we removed an element
                                                        else:
                                                            i += 1
                            else:
                                # Fallback to flat structure
                                for brand, brand_data in section_data.items():
                                    if isinstance(brand_data, dict):
                                        for model, patterns in brand_data.items():
                                            if isinstance(patterns, list):
                                                # Look for the exact match (case-insensitive) and
                                                # remove ALL occurrences
                                                i = 0
                                                while i < len(patterns):
                                                    pattern = patterns[i]
                                                    if (
                                                        isinstance(pattern, str)
                                                        and pattern.lower() == correct_match.lower()
                                                    ):
                                                        # Found the match, remove it
                                                        patterns.pop(i)
                                                        removed = True
                                                        removed_count += 1
                                                        # Don't increment i since we removed an element
                                                    else:
                                                        i += 1
                        else:
                            # For other fields (razor, soap, brush), use flat structure
                            # Search through all brands and models in the section
                            for brand, brand_data in section_data.items():
                                if isinstance(brand_data, dict):
                                    for model, patterns in brand_data.items():
                                        if isinstance(patterns, list):
                                            # Look for the exact match (case-insensitive) and
                                            # remove ALL occurrences
                                            i = 0
                                            while i < len(patterns):
                                                pattern = patterns[i]
                                                if (
                                                    isinstance(pattern, str)
                                                    and pattern.lower() == correct_match.lower()
                                                ):
                                                    # Found the match, remove it
                                                    patterns.pop(i)
                                                    removed = True
                                                    removed_count += 1
                                                    # Don't increment i since we removed an element
                                                else:
                                                    i += 1

                if not removed:
                    sections_str = ", ".join(sections_to_search)
                    if request.field == "blade":
                        errors.append(f"Entry not found in blade format sections: {correct_match}")
                    else:
                        errors.append(f"Entry not found in {sections_str} sections: {correct_match}")

            except Exception as e:
                errors.append(f"Error removing entry {entry}: {e}")

        # Save the updated YAML files to directory structure
        if removed_count > 0:
            try:
                for section, section_data in yaml_data.items():
                    if section_data:  # Only save if section has data
                        section_file = correct_matches_dir / f"{section}.yaml"
                        with section_file.open("w", encoding="utf-8") as f:
                            yaml.dump(
                                section_data,
                                f,
                                default_flow_style=False,
                                allow_unicode=True,
                                sort_keys=False,
                            )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error saving correct matches files: {e}"
                )

        return RemoveCorrectResponse(
            success=removed_count > 0,
            message=f"Removed {removed_count} entries from correct matches",
            removed_count=removed_count,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Error removing catalog validation entries: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error removing catalog validation entries: {str(e)}"
        )
