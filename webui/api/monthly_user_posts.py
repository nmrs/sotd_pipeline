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
    _extract_date_from_thread_title,
    aggregate_users,
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
    # Product usage data
    razors: List[Dict[str, Any]]
    blades: List[Dict[str, Any]]
    brushes: List[Dict[str, Any]]
    soaps: List[Dict[str, Any]]


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
        data_keys = list(enriched_data.keys()) if isinstance(enriched_data, dict) else "Not a dict"
        logger.debug(f"Enriched data keys: {data_keys}")

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

        # Extract product usage data
        razors = []
        blades = []
        brushes = []
        soaps = []

        for record in user_records:
            comment_id = record.get("id", "")

            # Extract razor data
            if "razor" in record and record["razor"]:
                razor = record["razor"]
                matched = razor.get("matched", {})
                if matched and matched.get("brand") and matched.get("model"):
                    razor_key = f"{matched['brand']}|{matched['model']}"
                    existing = next((r for r in razors if r["key"] == razor_key), None)
                    if existing:
                        existing["count"] += 1
                        existing["comment_ids"].append(comment_id)
                    else:
                        razors.append(
                            {
                                "key": razor_key,
                                "brand": matched["brand"],
                                "model": matched["model"],
                                "count": 1,
                                "comment_ids": [comment_id],
                            }
                        )

            # Extract blade data
            if "blade" in record and record["blade"]:
                blade = record["blade"]
                matched = blade.get("matched", {})
                if matched and matched.get("brand") and matched.get("model"):
                    blade_key = f"{matched['brand']}|{matched['model']}"
                    existing = next((b for b in blades if b["key"] == blade_key), None)
                    if existing:
                        existing["count"] += 1
                        existing["comment_ids"].append(comment_id)
                    else:
                        blades.append(
                            {
                                "key": blade_key,
                                "brand": matched["brand"],
                                "model": matched["model"],
                                "count": 1,
                                "comment_ids": [comment_id],
                            }
                        )

            # Extract brush data
            if "brush" in record and record["brush"]:
                brush = record["brush"]
                matched = brush.get("matched", {})
                
                # Extract brush information from various possible locations
                brush_brand = matched.get("brand")
                brush_model = matched.get("model")
                
                # Get handle and knot info for display purposes
                handle = matched.get("handle", {})
                knot = matched.get("knot", {})
                handle_brand = handle.get("brand", "") if handle else ""
                knot_brand = knot.get("brand", "") if knot else ""
                knot_model = knot.get("model", "") if knot else ""
                
                # Process all brushes, even those without top-level brand/model
                # Use actual top-level values, don't fill with fallbacks
                brush_key = (
                    f"{brush_brand or ''}|{brush_model or ''}|"
                    f"{handle_brand}|{knot_brand}|{knot_model}"
                )
                existing = next((b for b in brushes if b["key"] == brush_key), None)
                if existing:
                    existing["count"] += 1
                    existing["comment_ids"].append(comment_id)
                else:
                    brushes.append(
                        {
                            "key": brush_key,
                            "brand": brush_brand or "",
                            "model": brush_model or "",
                            "handle_brand": handle_brand,
                            "knot_brand": knot_brand,
                            "knot_model": knot_model,
                            "count": 1,
                            "comment_ids": [comment_id],
                        }
                    )

            # Extract soap data
            if "soap" in record and record["soap"]:
                soap = record["soap"]
                matched = soap.get("matched", {})
                if matched and matched.get("brand") and matched.get("scent"):
                    soap_key = f"{matched['brand']}|{matched['scent']}"
                    existing = next((s for s in soaps if s["key"] == soap_key), None)
                    if existing:
                        existing["count"] += 1
                        existing["comment_ids"].append(comment_id)
                    else:
                        soaps.append(
                            {
                                "key": soap_key,
                                "brand": matched["brand"],
                                "model": matched["scent"],
                                "count": 1,
                                "comment_ids": [comment_id],
                            }
                        )

        # Convert to our expected format
        analysis = {
            "user": user_analysis["user"],
            "posted_days": user_analysis["shaves"],
            "missed_days": user_analysis["missed_days"],
            "posted_dates": sorted(posted_dates),
            "comment_ids": comment_ids,
            "comments_by_date": comments_by_date,
            "razors": razors,
            "blades": blades,
            "brushes": brushes,
            "soaps": soaps,
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
