#!/usr/bin/env python3
"""Analysis endpoints for SOTD pipeline analyzer API."""

import logging
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to Python path for importing SOTD modules
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
    pattern: Optional[str] = None
    match_type: str
    confidence: Optional[float] = None
    mismatch_type: Optional[str] = None
    reason: Optional[str] = None
    count: int
    examples: List[str]
    comment_ids: List[str]


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


class MarkCorrectRequest(BaseModel):
    """Request model for marking matches as correct."""

    field: str = Field(..., description="Field type (razor, blade, brush, soap)")
    matches: List[Dict[str, Any]] = Field(..., description="List of matches to mark as correct")
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
                self.show_correct = False
                self.test_correct_matches = None

        args = Args()

        # Load data using the analyzer's method
        try:
            records = analyzer.load_matched_data(args)
            data = {"data": records}
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

        # Identify mismatches
        mismatches = analyzer.identify_mismatches(data, request.field, args)

        # Always process all records for consistent frontend filtering
        all_items = []
        total_matches = len(records)
        total_mismatches = 0

        # Create lookup for mismatches to mark them appropriately
        mismatch_lookup = {}
        for mismatch_type, items in mismatches.items():
            for item in items:
                record_id = item["record"].get("id", "")
                if record_id:
                    mismatch_lookup[record_id] = (mismatch_type, item["reason"])

        # Process all records
        skipped_count = 0
        for record in records:
            try:
                field_data = record.get(request.field, {})
                if not isinstance(field_data, dict):
                    skipped_count += 1
                    continue

                original = field_data.get("original", "")
                normalized = field_data.get("normalized", original)
                matched = field_data.get("matched", {})
                pattern = field_data.get("pattern") or ""
                match_type = field_data.get("match_type", "")
                record_id = record.get("id", "")

                # Include all records, even those with missing data
                # For records with missing normalized or matched data, create placeholder items
                if not normalized:
                    normalized = str(original) if original else "No original text"
                if not matched:
                    matched = {"error": "No matched data"}

                # Determine if this is a mismatch
                mismatch_type = None
                reason = ""

                # Check if this record was flagged by the analyzer
                if record_id in mismatch_lookup:
                    mismatch_type, reason = mismatch_lookup[record_id]
                    total_mismatches += 1

                # Additional checks for problematic data
                if not mismatch_type:
                    # Check for missing or invalid match data
                    if not matched or matched.get("error"):
                        mismatch_type = "invalid_match_data"
                        reason = "Missing or invalid match data"
                        total_mismatches += 1
                    # Check for empty or invalid original text
                    elif not original or original.strip() == "":
                        mismatch_type = "empty_original"
                        reason = "Empty or missing original text"
                        total_mismatches += 1
                    # Check for "No Match" status
                    elif match_type == "No Match":
                        mismatch_type = "no_match_found"
                        reason = "No match was found for this item"
                        total_mismatches += 1

                # Override Levenshtein distance matches if they were successful
                if mismatch_type == "levenshtein_distance" and matched and not matched.get("error"):
                    # Successful fuzzy matches should be considered good matches
                    mismatch_type = "good_match"
                    reason = "Successfully matched with fuzzy matching"
                    total_mismatches -= 1  # Reduce count since this is now a good match

                # Create item for all matches
                all_item = MismatchItem(
                    original=normalized,
                    matched=matched,
                    pattern=pattern,
                    match_type=match_type or "No Match",
                    confidence=field_data.get("confidence"),
                    mismatch_type=mismatch_type or "good_match",
                    reason=reason,
                    count=1,
                    examples=(
                        [str(record.get("_source_file", ""))] if record.get("_source_file") else []
                    ),
                    comment_ids=[str(record_id)] if record_id else [],
                )

                all_items.append(all_item)
            except Exception as e:
                logger.warning(f"Error processing record {record.get('id', 'unknown')}: {e}")
                skipped_count += 1
                continue

        # Group identical items together
        grouped_items = {}
        for item in all_items:
            # Create a key for grouping based on the main identifying fields
            # Use JSON string for consistent dictionary comparison
            import json

            matched_json = json.dumps(item.matched, sort_keys=True)
            group_key = (
                item.original,
                matched_json,
                item.pattern or "",
                item.match_type,
                item.mismatch_type or "",
                item.reason or "",
            )

            if group_key in grouped_items:
                # Merge with existing item
                existing = grouped_items[group_key]
                existing.count += item.count
                existing.examples.extend(item.examples)
                existing.comment_ids.extend(item.comment_ids)
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
            f"skipped_invalid_field_data={skipped_count}, returned={len(all_items)}, "
            f"total_matches={total_matches}, total_mismatches={total_mismatches}"
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

        field_data = data.get(field, {})
        total_entries = sum(
            len(strings) if isinstance(strings, list) else 0
            for brand_data in field_data.values()
            if isinstance(brand_data, dict)
            for strings in brand_data.values()
        )

        return CorrectMatchesResponse(field=field, total_entries=total_entries, entries=field_data)

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
            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
            from rich.console import Console
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

                # Create match key and mark as correct
                match_key = manager.create_match_key(request.field, original, matched)
                manager.mark_match_as_correct(
                    match_key, {"original": original, "matched": matched, "field": request.field}
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
            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
            from rich.console import Console
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
            status_code=500, 
            detail=f"Error removing matches from correct matches: {str(e)}"
        )


@router.delete("/correct-matches/{field}")
async def clear_correct_matches_by_field(field: str):
    """Clear correct matches for a specific field."""
    try:
        validate_field(field)

        # Import the correct matches manager
        try:
            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
            from rich.console import Console
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
            from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager
            from rich.console import Console
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
