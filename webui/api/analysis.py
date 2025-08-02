#!/usr/bin/env python3
"""Analysis endpoints for SOTD pipeline analyzer API."""

import logging
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the existing FilteredEntriesManager instead of duplicating logic
from sotd.utils.filtered_entries import FilteredEntriesManager

# Get logger for this module
logger = logging.getLogger(__name__)


try:
    from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer
    from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer

    logger.info("✅ MismatchAnalyzer imported successfully")
    logger.info("✅ UnmatchedAnalyzer imported successfully")
except ImportError as e:
    # Fallback for development
    logger.error(f"❌ Failed to import analyzers: {e}")
    UnmatchedAnalyzer = None
    MismatchAnalyzer = None

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


class UnmatchedAnalysisRequest(BaseModel):
    """Request model for unmatched analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap)")
    months: List[str] = Field(..., description="List of months to analyze (YYYY-MM format)")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of results to return")


class MismatchAnalysisRequest(BaseModel):
    """Request model for mismatch analysis."""

    field: str = Field(..., description="Field to analyze (razor, blade, brush, soap)")
    month: str = Field(..., description="Month to analyze (YYYY-MM format)")
    threshold: int = Field(default=3, ge=1, le=10, description="Levenshtein distance threshold")
    use_enriched_data: bool = Field(
        default=False, description="Use enriched data instead of matched data"
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
    partial_results: bool = False
    error: Optional[str] = None


class MismatchItem(BaseModel):
    """Model for individual mismatch item."""

    original: str
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
    # Split brush fields
    is_split_brush: Optional[bool] = None
    handle_component: Optional[str] = None
    knot_component: Optional[str] = None


class MismatchAnalysisResponse(BaseModel):
    """Response model for mismatch analysis."""

    field: str
    month: str
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
    correct_match: str
    expected_brand: str
    expected_model: str
    actual_brand: str
    actual_model: str
    severity: str
    suggested_action: str
    details: str


class CatalogValidationResponse(BaseModel):
    """Response model for catalog validation."""

    field: str
    total_entries: int
    issues: List[CatalogValidationIssue]
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


def get_filtered_entries_manager() -> FilteredEntriesManager:
    """Get FilteredEntriesManager instance for intentionally unmatched data."""
    filtered_file = project_root / "data" / "intentionally_unmatched.yaml"
    manager = FilteredEntriesManager(filtered_file)
    manager.load()
    return manager


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

            # Deduplicate and limit to 5 (same as command line tool)
            unique_comment_ids = list(set(comment_ids))[:5] if comment_ids else []
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
        from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches

        # Create a validator instance and clear its caches
        validator = ValidateCorrectMatches()
        validator.force_refresh()

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
        validate_months([request.month])

        logger.info(
            f"Starting mismatch analysis for field '{request.field}' for month {request.month}"
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
        analyzer = MismatchAnalyzer()

        # Create args object for the analyzer
        class Args:
            def __init__(self):
                self.month = request.month
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
        analyzer._load_correct_matches()
        logger.info(f"Loaded {len(analyzer._correct_matches)} correct matches")

        # Use the analyzer's logic directly - DRY principle
        mismatches = analyzer.identify_mismatches(data, request.field, args)

        # Convert analyzer results to API response format
        all_items = []
        total_matches = len(records)
        total_mismatches = 0

        # Process all mismatch categories from analyzer
        for mismatch_type, items in mismatches.items():
            logger.info(f"Processing category '{mismatch_type}' with {len(items)} items")
            for item in items:
                record = item["record"]
                field_data = record.get(request.field, {})

                original = field_data.get("original", "")
                normalized = field_data.get("normalized", original)
                pattern = field_data.get("pattern", "")
                match_type = field_data.get("match_type", "")
                record_id = record.get("id", "")

                # Handle intentionally unmatched items differently - they don't have matched data
                if mismatch_type == "intentionally_unmatched":
                    # For intentionally unmatched items, use empty matched dict and set match_type to "filtered"
                    matched = {}
                    enriched = {}
                    match_type = "filtered"
                else:
                    # When using enriched data, get original matched data from matched_data_map
                    if request.use_enriched_data and data.get("matched_data_map"):
                        # Get the original matched data from the matched_data_map
                        matched_data_map = data["matched_data_map"]
                        matched_record = matched_data_map.get(record_id, {})
                        matched_field_data = matched_record.get(request.field, {})
                        matched = matched_field_data.get("matched", {})
                        enriched = field_data.get("enriched", {})
                    else:
                        # Using matched data directly
                        matched = field_data.get("matched", {})
                        enriched = field_data.get("enriched", {})

                    # Skip records with missing data for other categories
                    if not normalized or not matched:
                        continue

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
                    # Split brush fields from analyzer results
                    is_split_brush=item.get("is_split_brush"),
                    handle_component=item.get("handle_component"),
                    knot_component=item.get("knot_component"),
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
            month=request.month,
            total_matches=total_matches,
            total_mismatches=total_mismatches,
            mismatch_items=all_items,
            processing_time=0.0,
            partial_results=False,
            error=None,
            matched_data_map=data.get("matched_data_map") if request.use_enriched_data else None,  # type: ignore
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

        # Load correct matches from file
        correct_matches_file = project_root / "data" / "correct_matches.yaml"
        if not correct_matches_file.exists():
            return CorrectMatchesResponse(field=field, total_entries=0, entries={})

        import yaml

        with correct_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        logger.info(f"Loaded data keys: {list(data.keys())}")

        # For brush field, include both brush and split_brush sections
        if field == "brush":
            field_data = data.get(field, {})
            split_brush_data = data.get("split_brush", {})
            # Combine both sections
            combined_data = {"brush": field_data, "split_brush": split_brush_data}
            logger.info(f"Field data for '{field}': {field_data}")
            logger.info(f"Split brush data: {split_brush_data}")
        else:
            field_data = data.get(field, {})
            split_brush_data = {}  # Initialize for non-brush fields
            combined_data = field_data
            logger.info(f"Field data for '{field}': {field_data}")

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
            # For brush field, count both brush and split_brush entries
            # Count brush section entries
            brush_entries = sum(
                len(strings) if isinstance(strings, list) else 0
                for brand_data in field_data.values()
                if isinstance(brand_data, dict)
                for strings in brand_data.values()
            )
            # Count split_brush section entries
            split_brush_entries = len(split_brush_data)
            total_entries = brush_entries + split_brush_entries
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
    """Mark matches as correct and save to correct_matches.yaml."""
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
        console = Console()
        correct_matches_file = project_root / "data" / "correct_matches.yaml"
        manager = CorrectMatchesManager(console, correct_matches_file)

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

                # Use the proper method to mark as correct
                match_key = manager.create_match_key(request.field, original, matched)
                manager.mark_match_as_correct(
                    match_key,
                    {
                        "original": original,
                        "matched": matched,
                        "field": request.field,
                    },
                )
                marked_count += 1

            except Exception as e:
                errors.append(f"Error marking match {match}: {e}")

        # Save to file
        if marked_count > 0:
            manager.save_correct_matches()

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
    """Remove matches from correct matches and save to correct_matches.yaml."""
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
        console = Console()
        correct_matches_file = project_root / "data" / "correct_matches.yaml"
        manager = CorrectMatchesManager(console, correct_matches_file)

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

                # Create match key and remove from correct matches
                match_key = manager.create_match_key(request.field, original, matched)

                # Check if the match exists in correct matches
                if manager.is_match_correct(match_key):
                    # Remove the match from correct matches
                    # We need to modify the manager to support removal
                    # For now, we'll clear the entire field and re-add everything except this match
                    # This is a temporary solution - ideally the manager would have a remove method
                    field_data = manager._correct_matches_data.get(request.field, {})

                    # Find and remove the specific entry
                    for brand, brand_data in field_data.items():
                        if isinstance(brand_data, dict):
                            for model, strings in brand_data.items():
                                if isinstance(strings, list):
                                    # Remove the specific original string
                                    if original in strings:
                                        strings.remove(original)
                                        removed_count += 1
                                        # If this was the last string for this model, clean up
                                        if not strings:
                                            del brand_data[model]
                                        # If this was the last model for this brand, clean up
                                        if not brand_data:
                                            del field_data[brand]
                                        break

                    # Update the manager's internal data
                    manager._correct_matches_data[request.field] = field_data

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
        correct_matches_file = project_root / "data" / "correct_matches.yaml"
        manager = CorrectMatchesManager(console, correct_matches_file)
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
        correct_matches_file = project_root / "data" / "correct_matches.yaml"
        manager = CorrectMatchesManager(console, correct_matches_file)
        manager.clear_correct_matches()

        return {"success": True, "message": "Cleared all correct matches"}

    except Exception as e:
        logger.error(f"Error clearing all correct matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing all correct matches: {str(e)}")


@router.post("/validate-catalog", response_model=CatalogValidationResponse)
async def validate_catalog_against_correct_matches(request: CatalogValidationRequest):
    """Validate correct_matches.yaml against current catalog patterns."""
    import time

    start_time = time.time()

    try:
        validate_field(request.field)

        # Import and use the validation logic directly
        try:
            from rich.console import Console

            from sotd.match.tools.managers.validate_correct_matches import ValidateCorrectMatches
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Could not import validation tools: {e}")

        # Create validator instance and run validation
        console = Console()
        validator = ValidateCorrectMatches(console)

        # Run the catalog validation
        issues = validator.validate_correct_matches_against_catalog(request.field)

        # Count total entries from correct_matches.yaml
        total_entries = 0
        try:
            import yaml

            correct_matches_file = project_root / "data" / "correct_matches.yaml"
            if correct_matches_file.exists():
                with open(correct_matches_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    field_data = data.get(request.field, {})
                    if isinstance(field_data, dict):
                        if request.field == "blade":
                            # Blade has format-aware structure: format -> brand -> model -> strings
                            for format, brands in field_data.items():
                                if isinstance(brands, dict):
                                    for brand, models in brands.items():
                                        if isinstance(models, dict):
                                            for model, strings in models.items():
                                                if isinstance(strings, list):
                                                    total_entries += len(strings)
                        else:
                            # Other fields have flat structure: brand -> model -> strings
                            for brand, models in field_data.items():
                                if isinstance(models, dict):
                                    for model, strings in models.items():
                                        if isinstance(strings, list):
                                            total_entries += len(strings)
        except Exception as e:
            logger.warning(f"Could not count total entries: {e}")

        processing_time = time.time() - start_time

        # Convert issues to proper format
        catalog_issues = []
        for issue in issues:
            catalog_issues.append(
                CatalogValidationIssue(
                    issue_type=issue.get("issue_type", ""),
                    field=issue.get("field", ""),
                    correct_match=issue.get("correct_match", ""),
                    expected_brand=issue.get("expected_brand", ""),
                    expected_model=issue.get("expected_model", ""),
                    actual_brand=issue.get("actual_brand", ""),
                    actual_model=issue.get("actual_model", ""),
                    severity=issue.get("severity", ""),
                    suggested_action=issue.get("suggested_action", ""),
                    details=issue.get("details", ""),
                )
            )

        return CatalogValidationResponse(
            field=request.field,
            total_entries=total_entries,
            issues=catalog_issues,
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"Error validating catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating catalog: {str(e)}")
