#!/usr/bin/env python3
"""Format compatibility analysis endpoints for SOTD pipeline analyzer API."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for format compatibility endpoints
router = APIRouter(prefix="/api/format-compatibility", tags=["format-compatibility"])

# Data directory path (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENRICHED_DATA_DIR = PROJECT_ROOT / "data" / "enriched"


class FormatCompatibilityResult(BaseModel):
    """Model for format compatibility analysis result."""

    razor_original: str
    razor_matched: Dict[str, Any]
    razor_enriched: Optional[Dict[str, Any]] = None
    blade_original: str
    blade_matched: Dict[str, Any]
    severity: str  # "error" or "warning"
    issue_type: str
    comment_ids: List[str]
    count: int


class FormatCompatibilityResponse(BaseModel):
    """Response model for format compatibility analysis."""

    months: List[str]
    severity_filter: str
    total_issues: int
    errors: int
    warnings: int
    results: List[FormatCompatibilityResult]
    processing_time: float


def _get_razor_format(razor_data: Dict[str, Any]) -> Optional[str]:
    """Extract razor format from matched or enriched data."""
    if not razor_data:
        return None

    # Prefer enriched format, fall back to matched format
    enriched = razor_data.get("enriched", {})
    if enriched and enriched.get("format"):
        return enriched.get("format", "").strip()

    matched = razor_data.get("matched", {})
    if matched:
        return matched.get("format", "").strip()

    return None


def _get_blade_format(blade_data: Dict[str, Any]) -> Optional[str]:
    """Extract blade format from matched data."""
    if not blade_data:
        return None

    matched = blade_data.get("matched", {})
    if matched:
        return matched.get("format", "").strip()

    return None


def _check_compatibility(
    razor_format: Optional[str], blade_format: Optional[str]
) -> Tuple[bool, Optional[str], str]:
    """
    Check if razor and blade formats are compatible.

    Returns:
        (is_compatible, severity, issue_type)
        - is_compatible: True if compatible, False if incompatible
        - severity: "error" for incompatible, "warning" for missing blade format
        - issue_type: Description of the issue
    """
    if not razor_format:
        # No razor format - can't determine compatibility
        return True, None, ""

    razor_format_lower = razor_format.lower()

    # Shavette can use any blade format (enrichment handles this)
    if razor_format_lower == "shavette" or razor_format_lower.startswith("shavette ("):
        return True, None, ""

    # Cartridge/Disposable and Straight razors shouldn't have blades
    if razor_format == "Cartridge/Disposable":
        if blade_format:
            return False, "warning", "Cartridge/Disposable razor should not have blade format"
        return True, None, ""

    if razor_format == "Straight":
        if blade_format:
            return False, "warning", "Straight razor should not have blade format"
        return True, None, ""

    # Missing blade format is a warning
    if not blade_format:
        return False, "warning", f"Razor format '{razor_format}' but blade format is missing"

    # DE razor compatibility
    if razor_format == "DE":
        if blade_format == "DE" or blade_format == "Half DE":
            return True, None, ""
        return False, "error", f"DE razor incompatible with {blade_format} blade"

    # Half DE razor compatibility
    if razor_format == "Half DE":
        if blade_format == "DE":
            return True, None, ""
        return False, "error", f"Half DE razor incompatible with {blade_format} blade"

    # AC razor compatibility
    if razor_format == "AC":
        if blade_format == "AC":
            return True, None, ""
        return False, "error", f"AC razor incompatible with {blade_format} blade"

    # GEM razor compatibility
    if razor_format == "GEM":
        if blade_format == "GEM":
            return True, None, ""
        return False, "error", f"GEM razor incompatible with {blade_format} blade"

    # Injector razor compatibility
    if razor_format == "Injector":
        if blade_format == "Injector":
            return True, None, ""
        return False, "error", f"Injector razor incompatible with {blade_format} blade"

    # Hair Shaper razor compatibility
    if razor_format == "Hair Shaper":
        if blade_format == "Hair Shaper":
            return True, None, ""
        return False, "error", f"Hair Shaper razor incompatible with {blade_format} blade"

    # Unknown razor format - can't determine compatibility
    # Don't flag as error, just return compatible
    return True, None, ""


@router.get("", response_model=FormatCompatibilityResponse)
async def analyze_format_compatibility(
    months: str = Query(..., description="Comma-separated list of months (YYYY-MM format)"),
    severity: str = Query("all", description="Filter by severity: 'error', 'warning', or 'all'"),
) -> FormatCompatibilityResponse:
    """
    Analyze format compatibility between razors and blades in enriched data.

    Identifies incompatible combinations (e.g., DE razor with AC blade) and
    missing blade format warnings.
    """
    import time

    start_time = time.time()

    # Parse months
    month_list = [m.strip() for m in months.split(",") if m.strip()]

    if not month_list:
        raise HTTPException(status_code=400, detail="At least one month is required")

    # Validate severity filter
    if severity not in ["error", "warning", "all"]:
        raise HTTPException(
            status_code=400, detail="severity must be 'error', 'warning', or 'all'"
        )

    # Load enriched data for all months
    all_records = []
    failed_months = []

    for month in month_list:
        enriched_file = ENRICHED_DATA_DIR / f"{month}.json"

        if not enriched_file.exists():
            logger.warning(f"Enriched data file not found: {enriched_file}")
            failed_months.append(month)
            continue

        try:
            with enriched_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "data" not in data:
                logger.error(f"Invalid data structure in {month}.json")
                failed_months.append(month)
                continue

            records = data.get("data", [])
            logger.info(f"Loaded {len(records)} records from {month}.json")
            all_records.extend(records)

        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            failed_months.append(month)
            continue

    if failed_months:
        logger.warning(f"Failed to load data for months: {failed_months}")

    if not all_records:
        raise HTTPException(
            status_code=404, detail=f"No enriched data found for months: {', '.join(month_list)}"
        )

    # Analyze compatibility
    # Use tuple keys for grouping, convert to string for dictionary key
    incompatibilities: Dict[Tuple[str, ...], FormatCompatibilityResult] = {}

    for record in all_records:
        razor_data = record.get("razor")
        blade_data = record.get("blade")
        comment_id = record.get("id", "")

        if not razor_data:
            continue

        razor_format = _get_razor_format(razor_data)
        blade_format = _get_blade_format(blade_data)

        is_compatible, issue_severity, issue_type = _check_compatibility(razor_format, blade_format)

        if not is_compatible and issue_severity:
            # Create a key for grouping identical incompatibilities
            razor_matched = razor_data.get("matched", {})
            blade_matched = blade_data.get("matched", {}) if blade_data else {}

            # Create tuple key for grouping identical incompatibilities
            key: Tuple[str, ...] = (
                str(razor_data.get("original", "")),
                str(razor_matched.get("brand", "")),
                str(razor_matched.get("model", "")),
                str(razor_format or ""),
                str(blade_data.get("original", "") if blade_data else ""),
                str(blade_matched.get("brand", "")),
                str(blade_matched.get("model", "")),
                str(blade_format or ""),
                str(issue_severity),
                str(issue_type),
            )

            if key not in incompatibilities:
                incompatibilities[key] = FormatCompatibilityResult(
                    razor_original=razor_data.get("original", ""),
                    razor_matched=razor_matched,
                    razor_enriched=razor_data.get("enriched"),
                    blade_original=blade_data.get("original", "") if blade_data else "",
                    blade_matched=blade_matched,
                    severity=issue_severity,
                    issue_type=issue_type,
                    comment_ids=[],
                    count=0,
                )

            incompatibilities[key].comment_ids.append(comment_id)
            incompatibilities[key].count += 1

    # Convert to list and filter by severity
    results = list(incompatibilities.values())

    if severity != "all":
        results = [r for r in results if r.severity == severity]

    # Sort by severity (errors first), then by count (descending)
    results.sort(key=lambda x: (x.severity != "error", -x.count))

    # Calculate statistics
    errors = sum(1 for r in results if r.severity == "error")
    warnings = sum(1 for r in results if r.severity == "warning")

    processing_time = time.time() - start_time

    logger.info(
        f"Format compatibility analysis completed: {len(results)} issues "
        f"({errors} errors, {warnings} warnings) in {processing_time:.2f}s"
    )

    return FormatCompatibilityResponse(
        months=month_list,
        severity_filter=severity,
        total_issues=len(results),
        errors=errors,
        warnings=warnings,
        results=results,
        processing_time=processing_time,
    )

