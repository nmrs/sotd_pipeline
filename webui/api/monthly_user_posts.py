#!/usr/bin/env python3
"""Monthly User Posts API endpoints for the SOTD Pipeline WebUI."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add the project root to the path to import from sotd
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sotd.aggregate.aggregators.users.user_aggregator import (  # noqa: E402
    aggregate_users,
    _extract_date_from_thread_title,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monthly-user-posts", tags=["monthly-user-posts"])


class UserPostingAnalysis(BaseModel):
    """User posting analysis result."""

    user: str
    posted_days: int
    missed_days: int
    posted_dates: List[str]
    comment_ids: List[str]
    comments_by_date: Dict[str, List[str]]


class MonthData(BaseModel):
    """Month data availability."""

    month: str
    has_data: bool
    user_count: int


@router.get("/months", response_model=List[MonthData])
async def get_available_months() -> List[MonthData]:
    """Get list of available months with data."""
    try:
        # Get project root directory (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        enriched_dir = project_root / "data" / "enriched"

        if not enriched_dir.exists():
            return []

        months = []
        for file_path in enriched_dir.glob("*.json"):
            month = file_path.stem
            if month and len(month) == 7 and month[4] == "-":  # YYYY-MM format
                # Check if file has data
                try:
                    import json

                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        user_count = len(
                            set(
                                record.get("author")
                                for record in data.get("data", [])
                                if record.get("author")
                            )
                        )

                    months.append(MonthData(month=month, has_data=True, user_count=user_count))
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    months.append(MonthData(month=month, has_data=False, user_count=0))

        # Sort by month (newest first)
        months.sort(key=lambda x: x.month, reverse=True)
        return months

    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/users/{month}", response_model=List[Dict[str, Any]])
async def get_users_for_month(
    month: str, search: Optional[str] = Query(None, description="Search filter for usernames")
) -> List[Dict[str, Any]]:
    """Get list of users who posted in a specific month."""
    try:
        # Load enriched data
        try:
            # Get project root directory (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            enriched_file = project_root / "data" / "enriched" / f"{month}.json"

            if not enriched_file.exists():
                return []

            with enriched_file.open("r", encoding="utf-8") as f:
                enriched_data = json.load(f)

        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            return []

        # Use existing user aggregation logic
        user_aggregations = aggregate_users(enriched_data["data"])

        # Convert to our expected format
        users = [
            {"username": user["user"], "post_count": user["shaves"]} for user in user_aggregations
        ]

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            users = [user for user in users if search_lower in user["username"].lower()]

        # Return more users for better coverage (limit to top 50 instead of 20)
        return users[:50]

    except Exception as e:
        logger.error(f"Error getting users for month {month}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/{month}/{username}", response_model=UserPostingAnalysis)
async def get_user_posting_analysis(month: str, username: str) -> UserPostingAnalysis:
    """Get posting analysis for a specific user in a specific month."""
    try:
        # Load enriched data
        try:
            # Get project root directory (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            enriched_file = project_root / "data" / "enriched" / f"{month}.json"

            if not enriched_file.exists():
                raise HTTPException(status_code=404, detail=f"No data available for {month}")

            with enriched_file.open("r", encoding="utf-8") as f:
                enriched_data = json.load(f)

        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            raise HTTPException(status_code=500, detail="Error loading enriched data")

        # Debug logging
        logger.debug(f"Enriched data type: {type(enriched_data)}")
        logger.debug(
            f"Enriched data keys: {list(enriched_data.keys()) if isinstance(enriched_data, dict) else 'Not a dict'}"
        )

        # Use existing user aggregation logic
        user_aggregations = aggregate_users(enriched_data["data"])

        # Find the specific user
        user_analysis = None
        for user in user_aggregations:
            if user["user"] == username:
                user_analysis = user
                break

        if not user_analysis:
            raise HTTPException(
                status_code=404, detail=f"User {username} not found in month {month}"
            )

        # Calculate posted dates and comment IDs for the specific user
        user_records = [
            record for record in enriched_data.get("data", []) if record.get("author") == username
        ]

        # Extract posted dates and comment IDs
        posted_dates = []
        comment_ids = []
        comments_by_date = {}

        for record in user_records:
            thread_title = record.get("thread_title", "")
            comment_id = record.get("id", "")

            if thread_title and comment_id:
                try:
                    posted_date = _extract_date_from_thread_title(thread_title)
                    date_str = posted_date.strftime("%Y-%m-%d")

                    if date_str not in comments_by_date:
                        comments_by_date[date_str] = []
                        posted_dates.append(date_str)

                    comments_by_date[date_str].append(comment_id)
                    comment_ids.append(comment_id)

                except Exception as e:
                    logger.warning(
                        f"Could not extract date from thread title: {thread_title} - {e}"
                    )
                    continue

        # Convert to our expected format
        analysis = {
            "user": user_analysis["user"],
            "posted_days": user_analysis["shaves"],
            "missed_days": user_analysis["missed_days"],
            "posted_dates": sorted(posted_dates),
            "comment_ids": comment_ids,
            "comments_by_date": comments_by_date,
        }

        return UserPostingAnalysis(**analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing user {username} for month {month}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "monthly-user-posts"}
