#!/usr/bin/env python3
"""Product usage aggregation for detailed product usage analysis with user breakdowns and comment IDs."""

from typing import Any, Dict, List

from ..users.user_aggregator import _extract_date_from_thread_title


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


def _extract_product_info(
    product_type: str, product_data: Dict[str, Any]
) -> Dict[str, Any] | None:
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
        brand = matched.get("brand") or ""
        model = matched.get("model") or ""
        if brand or model:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand,
                "model": model,
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


def aggregate_product_usage(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Aggregate detailed product usage analysis from enriched records.

    Returns a dictionary organized by product type (razors, blades, brushes, soaps),
    then by product key, with detailed analysis including:
    - product info (type, brand, model)
    - total_usage, unique_users
    - users list with usage counts, dates, and comment IDs
    - comments_by_date mapping
    - comment_urls: mapping of comment_id -> url

    Args:
        records: List of enriched comment records

    Returns:
        Dictionary with structure: {product_type: {product_key: analysis_data}}
    """
    if not records:
        return {"razors": {}, "blades": {}, "brushes": {}, "soaps": {}}

    # Organize by product type
    product_analyses: Dict[str, Dict[str, Dict[str, Any]]] = {
        "razors": {},
        "blades": {},
        "brushes": {},
        "soaps": {},
    }

    for record in records:
        author = record.get("author", "").strip()
        comment_id = record.get("id", "")
        thread_title = record.get("thread_title", "")

        if not author or not comment_id or not thread_title:
            continue

        # Extract date from thread title
        try:
            posted_date = _extract_date_from_thread_title(thread_title)
            date_str = posted_date.strftime("%Y-%m-%d")
        except (ValueError, KeyError):
            continue

        # Process each product type
        for product_type in ["razor", "blade", "brush", "soap"]:
            product_field = record.get(product_type)
            if not product_field:
                continue

            product_info = _extract_product_info(product_type, product_field)
            if not product_info:
                continue

            product_key = product_info["key"]
            # Map product type to plural key
            plural_map = {"razor": "razors", "blade": "blades", "brush": "brushes", "soap": "soaps"}
            products_dict = product_analyses[plural_map[product_type]]

            # Initialize product analysis if not exists
            if product_key not in products_dict:
                products_dict[product_key] = {
                    "product": {
                        "type": product_type,
                        "brand": product_info["brand"],
                        "model": product_info["model"],
                    },
                    "total_usage": 0,
                    "unique_users": set(),
                    "users": {},  # username -> user data
                    "comments_by_date": {},
                    "comment_urls": {},
                }

            product_analysis = products_dict[product_key]
            product_analysis["total_usage"] += 1
            product_analysis["unique_users"].add(author)

            # Extract URL from record if available
            comment_url = record.get("url", "")
            if comment_url and comment_id:
                product_analysis["comment_urls"][comment_id] = comment_url

            # Add to comments_by_date
            if date_str not in product_analysis["comments_by_date"]:
                product_analysis["comments_by_date"][date_str] = []
            product_analysis["comments_by_date"][date_str].append(comment_id)

            # Add to user data
            if author not in product_analysis["users"]:
                product_analysis["users"][author] = {
                    "username": author,
                    "usage_count": 0,
                    "usage_dates": [],
                    "comment_ids": [],
                }

            user_data = product_analysis["users"][author]
            user_data["usage_count"] += 1
            user_data["comment_ids"].append(comment_id)
            if date_str not in user_data["usage_dates"]:
                user_data["usage_dates"].append(date_str)

    # Finalize product analyses
    for product_type in ["razors", "blades", "brushes", "soaps"]:
        for product_key, analysis in product_analyses[product_type].items():
            # Convert unique_users set to count
            analysis["unique_users"] = len(analysis["unique_users"])

            # Convert users dict to list and sort by usage_count
            users_list = list(analysis["users"].values())
            for user_data in users_list:
                user_data["usage_dates"].sort()
            users_list.sort(key=lambda x: x["usage_count"], reverse=True)
            analysis["users"] = users_list

            # Add usage_by_date (same as comments_by_date for consistency)
            analysis["usage_by_date"] = analysis["comments_by_date"].copy()

    return product_analyses
