#!/usr/bin/env python3
"""User analysis aggregation for detailed user posting analysis with comment IDs and product usage."""

from calendar import monthrange
from datetime import date
from typing import Any, Dict, List

from ..users.user_aggregator import _extract_date_from_thread_title, _get_all_dates_in_month


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


def _extract_product_info(product_type: str, product_data: Dict[str, Any]) -> Dict[str, Any] | None:
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
        handle = matched.get("handle", {})
        knot = matched.get("knot", {})
        handle_brand = handle.get("brand", "") if handle else ""
        knot_brand = knot.get("brand", "") if knot else ""
        knot_model = knot.get("model", "") if knot else ""
        if brand or model:
            return {
                "key": _generate_product_key(product_type, matched),
                "brand": brand,
                "model": model,
                "handle_brand": handle_brand,
                "knot_brand": knot_brand,
                "knot_model": knot_model,
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


def aggregate_user_analysis(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate detailed user analysis from enriched records.

    Returns a dictionary keyed by username with detailed analysis including:
    - posted_days, missed_days, posted_dates
    - comment_ids, comments_by_date
    - comment_urls: mapping of comment_id -> url
    - product usage (razors, blades, brushes, soaps) with counts and comment IDs

    Args:
        records: List of enriched comment records

    Returns:
        Dictionary mapping username to user analysis data
    """
    if not records:
        return {}

    # Determine month from first record
    first_record = records[0]
    thread_title = first_record.get("thread_title", "")
    if not thread_title:
        return {}

    try:
        first_date = _extract_date_from_thread_title(thread_title)
        year, month = first_date.year, first_date.month
    except (ValueError, KeyError):
        return {}

    # Get all dates in the month
    all_dates = set(_get_all_dates_in_month(year, month))

    # Process records to build user analysis
    user_analyses: Dict[str, Dict[str, Any]] = {}

    for record in records:
        author = record.get("author", "").strip()
        comment_id = record.get("id", "")
        thread_title = record.get("thread_title", "")

        if not author or not thread_title or not comment_id:
            continue

        # Initialize user analysis if not exists
        if author not in user_analyses:
            user_analyses[author] = {
                "user": author,
                "posted_days": 0,
                "missed_days": 0,
                "posted_dates": [],
                "comment_ids": [],
                "comments_by_date": {},
                "comment_urls": {},
                "razors": {},
                "blades": {},
                "brushes": {},
                "soaps": {},
            }

        user_analysis = user_analyses[author]

        # Extract URL from record if available
        comment_url = record.get("url", "")
        if comment_url and comment_id:
            user_analysis["comment_urls"][comment_id] = comment_url

        # Extract date and add to comments_by_date
        try:
            posted_date = _extract_date_from_thread_title(thread_title)
            date_str = posted_date.strftime("%Y-%m-%d")

            if date_str not in user_analysis["comments_by_date"]:
                user_analysis["comments_by_date"][date_str] = []
                user_analysis["posted_dates"].append(date_str)

            user_analysis["comments_by_date"][date_str].append(comment_id)
            user_analysis["comment_ids"].append(comment_id)

        except (ValueError, KeyError):
            continue

        # Extract product usage
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
            products_dict = user_analysis[plural_map[product_type]]

            if product_key not in products_dict:
                products_dict[product_key] = {
                    "key": product_key,
                    "brand": product_info["brand"],
                    "model": product_info["model"],
                    "count": 0,
                    "comment_ids": [],
                }
                # Add brush-specific fields
                if product_type == "brush":
                    products_dict[product_key]["handle_brand"] = product_info.get(
                        "handle_brand", ""
                    )
                    products_dict[product_key]["knot_brand"] = product_info.get("knot_brand", "")
                    products_dict[product_key]["knot_model"] = product_info.get("knot_model", "")

            products_dict[product_key]["count"] += 1
            products_dict[product_key]["comment_ids"].append(comment_id)

    # Finalize user analyses
    for username, analysis in user_analyses.items():
        # Calculate posted_days and missed_days
        posted_dates_set = set(analysis["posted_dates"])
        analysis["posted_days"] = len(posted_dates_set)
        # Convert posted dates strings to date objects for comparison
        posted_dates_objects = {date.fromisoformat(d) for d in posted_dates_set}
        missed_dates_set = all_dates - posted_dates_objects
        analysis["missed_days"] = len(missed_dates_set)

        # Sort posted dates
        analysis["posted_dates"] = sorted(analysis["posted_dates"])

        # Convert product dictionaries to lists and sort by count
        for product_key in ["razors", "blades", "brushes", "soaps"]:
            products_list = list(analysis[product_key].values())
            products_list.sort(key=lambda x: x["count"], reverse=True)
            analysis[product_key] = products_list

    return user_analyses
