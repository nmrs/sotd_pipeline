#!/usr/bin/env python3
"""File system integration for SOTD pipeline data."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for file endpoints
router = APIRouter(prefix="/api/files", tags=["files"])


class MonthData(BaseModel):
    """Response model for month data."""

    month: str
    total_records: int
    data: List[Dict[str, Any]]


class AvailableMonths(BaseModel):
    """Response model for available months."""

    months: List[str]
    total_months: int


def get_data_directory() -> Path:
    """Get the data directory path."""
    # Support SOTD_DATA_DIR environment variable for containerized deployments
    sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
    if sotd_data_dir:
        data_dir = Path(sotd_data_dir) / "matched"
    else:
        # Fallback to relative path for development
        current_dir = Path(__file__).parent
        data_dir = current_dir.parent.parent / "data" / "matched"
    return data_dir


def validate_json_file(file_path: Path) -> bool:
    """Validate that a file contains valid JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False


@router.get("/available-months", response_model=AvailableMonths)
async def get_available_months() -> AvailableMonths:
    """Get list of available months from the matched data directory."""
    try:
        data_dir = get_data_directory()

        if not data_dir.exists():
            logger.warning(f"Data directory does not exist: {data_dir}")
            return AvailableMonths(months=[], total_months=0)

        # Find all JSON files in the directory
        json_files = list(data_dir.glob("*.json"))

        # Extract month names from filenames (YYYY-MM.json format)
        months = []
        for file_path in json_files:
            if file_path.stem:
                # Skip validation for performance - just check if file exists and has content
                if file_path.stat().st_size > 0:
                    months.append(file_path.stem)

        # Sort months chronologically
        months.sort()

        logger.info(f"Found {len(months)} available months: {months}")
        return AvailableMonths(months=months, total_months=len(months))

    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading available months: {str(e)}")


@router.get("/{month}", response_model=MonthData)
async def get_month_data(month: str) -> MonthData:
    """Get data for a specific month."""
    try:
        data_dir = get_data_directory()
        file_path = data_dir / f"{month}.json"

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Month data not found: {month}. "
                f"Available months can be retrieved from /api/files/available-months",
            )

        # Validate JSON structure
        if not validate_json_file(file_path):
            raise HTTPException(status_code=500, detail=f"Invalid JSON in month file: {month}")

        # Read and parse the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract records from the data structure
        records = data.get("data", [])
        if not isinstance(records, list):
            raise HTTPException(
                status_code=500, detail=f"Invalid data structure in month file: {month}"
            )

        logger.info(f"Successfully loaded {len(records)} records for month {month}")
        return MonthData(month=month, total_records=len(records), data=records)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error reading month data for {month}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading month data: {str(e)}")


@router.get("/{month}/summary")
async def get_month_summary(month: str) -> Dict[str, Any]:
    """Get a summary of data for a specific month."""
    try:
        data_dir = get_data_directory()
        file_path = data_dir / f"{month}.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Month data not found: {month}")

        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("data", [])

        # Calculate summary statistics
        summary = {
            "month": month,
            "total_records": len(records),
            "file_size_bytes": file_path.stat().st_size,
            "fields_present": {},
            "match_stats": {"total_matched": 0, "total_unmatched": 0, "match_types": {}},
        }

        # Analyze field presence and match statistics
        for record in records:
            for field in ["razor", "blade", "brush", "soap"]:
                field_data = record.get(field)
                if field_data:
                    summary["fields_present"][field] = summary["fields_present"].get(field, 0) + 1

                    # Analyze match statistics
                    if isinstance(field_data, dict):
                        matched = field_data.get("matched")
                        match_type = field_data.get("match_type")

                        if matched is not None:
                            summary["match_stats"]["total_matched"] += 1
                        else:
                            summary["match_stats"]["total_unmatched"] += 1

                        if match_type:
                            summary["match_stats"]["match_types"][match_type] = (
                                summary["match_stats"]["match_types"].get(match_type, 0) + 1
                            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for {month}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting month summary: {str(e)}")
