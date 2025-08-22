#!/usr/bin/env python3
"""Monthly User Posts API endpoints for the SOTD Pipeline WebUI."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add the project root to the path to import from sotd
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sotd.aggregate.aggregators.users.user_posting_analyzer import UserPostingAnalyzer  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monthly-user-posts", tags=["monthly-user-posts"])


class UserPostingAnalysis(BaseModel):
    """User posting analysis result."""

    user: str
    posted_days: int
    missed_days: int
    posted_dates: List[str]
    comment_ids: List[str]


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
        analyzer = UserPostingAnalyzer()
        enriched_data = analyzer.load_enriched_data(month)

        if not enriched_data:
            return []

        # Get unique users with post counts
        user_counts = {}
        for record in enriched_data:
            author = record.get("author")
            if author:
                user_counts[author] = user_counts.get(author, 0) + 1

        # Convert to list and sort by post count (descending)
        users = [
            {"username": username, "post_count": count} for username, count in user_counts.items()
        ]
        users.sort(key=lambda x: x["post_count"], reverse=True)

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
        analyzer = UserPostingAnalyzer()
        enriched_data = analyzer.load_enriched_data(month)

        if not enriched_data:
            raise HTTPException(status_code=404, detail=f"No data available for {month}")

        # Analyze user posting
        analysis = analyzer.analyze_user_posting(username, enriched_data, month)

        # Convert dates to strings for JSON serialization
        analysis["posted_dates"] = [d.isoformat() for d in analysis["posted_dates"]]

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
