#!/usr/bin/env python3
"""Product Usage API endpoints for the SOTD Pipeline WebUI."""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add the project root to the path to import from sotd
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sotd.aggregate.aggregators.users.user_aggregator import (  # noqa: E402
    _extract_date_from_thread_title,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/product-usage", tags=["product-usage"])


class Product(BaseModel):
    """Product information."""

    key: str
    brand: str
    model: str
    usage_count: int
    unique_users: int


class UserProductUsage(BaseModel):
    """User product usage information."""

    username: str
    usage_count: int
    usage_dates: List[str]
    comment_ids: List[str]


class ProductUsageAnalysis(BaseModel):
    """Product usage analysis result."""

    product: Dict[str, str]
    total_usage: int
    unique_users: int
    users: List[UserProductUsage]
    usage_by_date: Dict[str, List[str]]
    comments_by_date: Dict[str, List[str]]


def _generate_product_key(product_type: str, matched: Dict[str, Any]) -> str:
    """Generate product key based on product type."""
    if product_type == "razor":
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        return f"{brand}|{model}"
    elif product_type == "blade":
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        return f"{brand}|{model}"
    elif product_type == "brush":
        brand = matched.get("brand", "") or ""
        model = matched.get("model", "") or ""
        handle = matched.get("handle", {})
        knot = matched.get("knot", {})
        handle_brand = handle.get("brand", "") if handle else ""
        knot_brand = knot.get("brand", "") if knot else ""
        knot_model = knot.get("model", "") if knot else ""
        return f"{brand}|{model}|{handle_brand}|{knot_brand}|{knot_model}"
    elif product_type == "soap":
        brand = matched.get("brand", "")
        scent = matched.get("scent", "")
        return f"{brand}|{scent}"
    else:
        return ""


def _extract_product_info(product_type: str, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract product information from product data."""
    if not product_data:
        return None

    matched = product_data.get("matched", {})
    if not matched:
        return None

    if product_type == "razor":
        brand = matched.get("brand")
        model = matched.get("model")
        if brand and model:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand,
                "model": model,
            }
    elif product_type == "blade":
        brand = matched.get("brand")
        model = matched.get("model")
        if brand and model:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand,
                "model": model,
            }
    elif product_type == "brush":
        brand = matched.get("brand")
        model = matched.get("model")
        # Brushes can have brand/model at top level or in handle/knot
        if brand or model:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand or "",
                "model": model or "",
            }
    elif product_type == "soap":
        brand = matched.get("brand")
        scent = matched.get("scent")
        if brand and scent:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand,
                "model": scent,  # Use scent as model for consistency
            }

    return None


@router.get("/products/{month}/{product_type}", response_model=List[Product])
async def get_products_for_month(
    month: str,
    product_type: str,
    search: Optional[str] = Query(None, description="Search filter for products"),
) -> List[Product]:
    """Get list of available products for a month and product type."""
    try:
        # Validate product type
        if product_type not in ["razor", "blade", "brush", "soap"]:
            raise HTTPException(status_code=400, detail=f"Invalid product type: {product_type}")

        # Load enriched data
        try:
            project_root = Path(__file__).parent.parent.parent
            enriched_file = project_root / "data" / "enriched" / f"{month}.json"

            if not enriched_file.exists():
                return []

            with enriched_file.open("r", encoding="utf-8") as f:
                enriched_data = json.load(f)

        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            return []

        # Extract products from records
        products_dict: Dict[str, Dict[str, Any]] = {}
        records = enriched_data.get("data", [])

        for record in records:
            product_field = record.get(product_type)
            if not product_field:
                continue

            product_info = _extract_product_info(product_type, product_field)
            if not product_info:
                continue

            product_key = product_info["key"]
            if product_key not in products_dict:
                products_dict[product_key] = {
                    "key": product_key,
                    "brand": product_info["brand"],
                    "model": product_info["model"],
                    "usage_count": 0,
                    "unique_users": set(),
                }

            products_dict[product_key]["usage_count"] += 1
            author = record.get("author")
            if author:
                products_dict[product_key]["unique_users"].add(author)

        # Convert to list and format
        products = []
        for product_data in products_dict.values():
            products.append(
                {
                    "key": product_data["key"],
                    "brand": product_data["brand"],
                    "model": product_data["model"],
                    "usage_count": product_data["usage_count"],
                    "unique_users": len(product_data["unique_users"]),
                }
            )

        # Sort by usage count (descending)
        products.sort(key=lambda x: x["usage_count"], reverse=True)

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            products = [
                p
                for p in products
                if search_lower in p["brand"].lower() or search_lower in p["model"].lower()
            ]

        # Limit to top 100 for performance
        return products[:100]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting products for month {month} and type {product_type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analysis/{month}/{product_type}/{brand}/{model}", response_model=ProductUsageAnalysis)
async def get_product_usage_analysis(
    month: str, product_type: str, brand: str, model: str
) -> ProductUsageAnalysis:
    """Get product usage analysis for a specific product."""
    try:
        # Decode URL-encoded brand and model
        brand = unquote(brand)
        model = unquote(model)

        # Validate product type
        if product_type not in ["razor", "blade", "brush", "soap"]:
            raise HTTPException(status_code=400, detail=f"Invalid product type: {product_type}")

        # Load enriched data
        try:
            project_root = Path(__file__).parent.parent.parent
            enriched_file = project_root / "data" / "enriched" / f"{month}.json"

            if not enriched_file.exists():
                raise HTTPException(status_code=404, detail=f"No data available for {month}")

            with enriched_file.open("r", encoding="utf-8") as f:
                enriched_data = json.load(f)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error loading enriched data for {month}: {e}")
            raise HTTPException(status_code=500, detail="Error loading enriched data")

        # Filter records by product match
        matching_records = []
        records = enriched_data.get("data", [])

        for record in records:
            product_field = record.get(product_type)
            if not product_field:
                continue

            matched = product_field.get("matched", {})
            if not matched:
                continue

            # Match based on product type
            if product_type == "razor":
                if matched.get("brand") == brand and matched.get("model") == model:
                    matching_records.append(record)
            elif product_type == "blade":
                if matched.get("brand") == brand and matched.get("model") == model:
                    matching_records.append(record)
            elif product_type == "brush":
                # For brushes, match on brand/model (handle/knot info is for display)
                if matched.get("brand") == brand and matched.get("model") == model:
                    matching_records.append(record)
            elif product_type == "soap":
                # For soap, brand is maker and model is scent
                if matched.get("brand") == brand and matched.get("scent") == model:
                    matching_records.append(record)

        if not matching_records:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_type} '{brand} {model}' not found in month {month}",
            )

        # Group by user and extract dates
        users_dict: Dict[str, Dict[str, Any]] = {}
        comments_by_date: Dict[str, List[str]] = {}
        total_usage = len(matching_records)

        for record in matching_records:
            author = record.get("author", "")
            comment_id = record.get("id", "")
            thread_title = record.get("thread_title", "")

            if not author:
                continue

            # Initialize user if not exists
            if author not in users_dict:
                users_dict[author] = {
                    "username": author,
                    "usage_count": 0,
                    "usage_dates": [],
                    "comment_ids": [],
                }

            users_dict[author]["usage_count"] += 1
            if comment_id:
                users_dict[author]["comment_ids"].append(comment_id)

            # Extract date from thread title
            if thread_title and comment_id:
                try:
                    posted_date = _extract_date_from_thread_title(thread_title)
                    date_str = posted_date.strftime("%Y-%m-%d")

                    if date_str not in comments_by_date:
                        comments_by_date[date_str] = []

                    comments_by_date[date_str].append(comment_id)

                    # Add date to user if not already present
                    if date_str not in users_dict[author]["usage_dates"]:
                        users_dict[author]["usage_dates"].append(date_str)

                except Exception as e:
                    logger.warning(f"Could not extract date from thread title: {thread_title} - {e}")
                    continue

        # Convert users dict to list and sort by usage count
        users_list = list(users_dict.values())
        users_list.sort(key=lambda x: x["usage_count"], reverse=True)

        # Sort usage dates for each user
        for user in users_list:
            user["usage_dates"].sort()

        # Build usage_by_date (same as comments_by_date for consistency)
        usage_by_date = comments_by_date.copy()

        # Build response
        analysis = {
            "product": {
                "type": product_type,
                "brand": brand,
                "model": model,
            },
            "total_usage": total_usage,
            "unique_users": len(users_list),
            "users": users_list,
            "usage_by_date": usage_by_date,
            "comments_by_date": comments_by_date,
        }

        return ProductUsageAnalysis(**analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error analyzing product {product_type} '{brand} {model}' for month {month}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "product-usage"}

