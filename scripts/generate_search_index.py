#!/usr/bin/env python3
"""
Generate search index from aggregated data files.

This script scans all monthly and annual aggregation files to create a lightweight
search index for fast autocomplete queries and date picker validation.

The search index includes:
- Unique products (razors, blades, brushes, soaps) with first_seen/last_seen
- Unique users with first_seen/last_seen
- Available months and years for date picker validation
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def parse_brand_model_from_name(name: str) -> Tuple[str, str]:
    """
    Parse brand and model from a composite name like "Brand Model".

    Args:
        name: Composite name string

    Returns:
        Tuple of (brand, model). If parsing fails, returns (name, "")
    """
    if not name:
        return ("", "")

    # Try to split on first space
    parts = name.split(" ", 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    else:
        # Single word - treat as brand only
        return (name, "")


def extract_products_from_category(
    category_data: List[Dict[str, Any]], product_type: str, month: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract product information from a category's aggregated data.

    Args:
        category_data: List of aggregated product records
        product_type: Type of product ("razor", "blade", "brush", "soap")
        month: Month string (YYYY-MM) for tracking first_seen/last_seen

    Returns:
        Dictionary mapping product keys to product info with first_seen/last_seen
    """
    products = {}

    for record in category_data:
        if product_type == "soap":
            # Soaps have brand and scent fields
            brand = record.get("brand", "")
            scent = record.get("scent", "")
            if not brand:
                continue

            # Create key from brand and scent
            key = f"{product_type}:{brand}:{scent}".lower()

            if key not in products:
                products[key] = {
                    "type": product_type,
                    "brand": brand,
                    "scent": scent,
                    "first_seen": month,
                    "last_seen": month,
                }
            else:
                # Update last_seen if this month is later
                if month > products[key]["last_seen"]:
                    products[key]["last_seen"] = month
                if month < products[key]["first_seen"]:
                    products[key]["first_seen"] = month

        else:
            # Razors, blades, brushes - try to get brand/model from fields or parse from name
            brand = record.get("brand", "")
            model = record.get("model", "")

            # If brand/model not in record, parse from name
            if not brand:
                name = record.get("name", "")
                if name:
                    brand, model = parse_brand_model_from_name(name)
                else:
                    continue

            if not brand:
                continue

            # Create key from brand and model
            key = f"{product_type}:{brand}:{model}".lower()

            if key not in products:
                products[key] = {
                    "type": product_type,
                    "brand": brand,
                    "model": model,
                    "first_seen": month,
                    "last_seen": month,
                }
            else:
                # Update last_seen if this month is later
                if month > products[key]["last_seen"]:
                    products[key]["last_seen"] = month
                if month < products[key]["first_seen"]:
                    products[key]["first_seen"] = month

    return products


def extract_users_from_data(data: Dict[str, Any], month: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract user information from aggregated data.

    Args:
        data: Aggregated data dictionary
        month: Month string (YYYY-MM) for tracking first_seen/last_seen

    Returns:
        Dictionary mapping usernames to user info with first_seen/last_seen
    """
    users = {}

    # Check for users section in data
    users_data = data.get("data", {}).get("users", [])
    if not users_data:
        return users

    for record in users_data:
        username = record.get("user") or record.get("username") or record.get("name")
        if not username:
            continue

        username_lower = username.lower()

        if username_lower not in users:
            users[username_lower] = {
                "username": username,  # Preserve original case
                "first_seen": month,
                "last_seen": month,
            }
        else:
            # Update last_seen if this month is later
            if month > users[username_lower]["last_seen"]:
                users[username_lower]["last_seen"] = month
            if month < users[username_lower]["first_seen"]:
                users[username_lower]["first_seen"] = month

    return users


def merge_products(existing: Dict[str, Dict], new: Dict[str, Dict]) -> None:
    """
    Merge new products into existing products dict, updating first_seen/last_seen.

    Args:
        existing: Existing products dictionary to update
        new: New products dictionary to merge in
    """
    for key, product in new.items():
        if key not in existing:
            existing[key] = product
        else:
            # Update first_seen if new month is earlier
            if product["first_seen"] < existing[key]["first_seen"]:
                existing[key]["first_seen"] = product["first_seen"]
            # Update last_seen if new month is later
            if product["last_seen"] > existing[key]["last_seen"]:
                existing[key]["last_seen"] = product["last_seen"]


def merge_users(existing: Dict[str, Dict], new: Dict[str, Dict]) -> None:
    """
    Merge new users into existing users dict, updating first_seen/last_seen.

    Args:
        existing: Existing users dictionary to update
        new: New users dictionary to merge in
    """
    for key, user in new.items():
        if key not in existing:
            existing[key] = user
        else:
            # Update first_seen if new month is earlier
            if user["first_seen"] < existing[key]["first_seen"]:
                existing[key]["first_seen"] = user["first_seen"]
            # Update last_seen if new month is later
            if user["last_seen"] > existing[key]["last_seen"]:
                existing[key]["last_seen"] = user["last_seen"]


def process_monthly_file(
    file_path: Path, data_dir: Path
) -> Tuple[Dict[str, Dict], Dict[str, Dict], str]:
    """
    Process a monthly aggregation file.

    Args:
        file_path: Path to monthly aggregation file
        data_dir: Base data directory

    Returns:
        Tuple of (products_dict, users_dict, month_string)
    """
    month = file_path.stem  # e.g., "2025-12"
    all_products = {}
    all_users = {}

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract products from each category
        data_section = data.get("data", {})

        # Razors
        if "razors" in data_section:
            razors = extract_products_from_category(data_section["razors"], "razor", month)
            merge_products(all_products, razors)

        # Blades
        if "blades" in data_section:
            blades = extract_products_from_category(data_section["blades"], "blade", month)
            merge_products(all_products, blades)

        # Brushes
        if "brushes" in data_section:
            brushes = extract_products_from_category(data_section["brushes"], "brush", month)
            merge_products(all_products, brushes)

        # Soaps
        if "soaps" in data_section:
            soaps = extract_products_from_category(data_section["soaps"], "soap", month)
            merge_products(all_products, soaps)

        # Extract users
        users = extract_users_from_data(data, month)
        merge_users(all_users, users)

        logger.debug(f"Processed {month}: {len(all_products)} products, {len(all_users)} users")

    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning(f"Error processing {file_path}: {e}")
        # Continue processing other files

    return (all_products, all_users, month)


def process_annual_file(
    file_path: Path, data_dir: Path
) -> Tuple[Dict[str, Dict], Dict[str, Dict], Set[str]]:
    """
    Process an annual aggregation file.

    Args:
        file_path: Path to annual aggregation file
        data_dir: Base data directory

    Returns:
        Tuple of (products_dict, users_dict, months_set)
    """
    year = file_path.stem  # e.g., "2025"
    all_products = {}
    all_users = {}
    months_in_year = set()

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Get included months from metadata
        metadata = data.get("metadata", {})
        included_months = metadata.get("included_months", [])
        months_in_year.update(included_months)

        # Extract products from each category
        # Razors
        if "razors" in data:
            razors = extract_products_from_category(data["razors"], "razor", f"{year}-01")
            all_products.update(razors)

        # Blades
        if "blades" in data:
            blades = extract_products_from_category(data["blades"], "blade", f"{year}-01")
            all_products.update(blades)

        # Brushes
        if "brushes" in data:
            brushes = extract_products_from_category(data["brushes"], "brush", f"{year}-01")
            all_products.update(brushes)

        # Soaps
        if "soaps" in data:
            soaps = extract_products_from_category(data["soaps"], "soap", f"{year}-01")
            all_products.update(soaps)

        # Extract users from users section if present
        if "users" in data:
            users_data = data["users"]
            for record in users_data:
                username = record.get("user") or record.get("username") or record.get("name")
                if not username:
                    continue

                username_lower = username.lower()
                # For annual, use first month of year as first_seen
                first_month = f"{year}-01"
                if username_lower not in all_users:
                    all_users[username_lower] = {
                        "username": username,
                        "first_seen": first_month,
                        "last_seen": f"{year}-12",
                    }
                else:
                    # Update if needed
                    if f"{year}-01" < all_users[username_lower]["first_seen"]:
                        all_users[username_lower]["first_seen"] = first_month
                    if f"{year}-12" > all_users[username_lower]["last_seen"]:
                        all_users[username_lower]["last_seen"] = f"{year}-12"

        logger.debug(
            f"Processed annual {year}: {len(all_products)} products, {len(all_users)} users"
        )

    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning(f"Error processing {file_path}: {e}")
        # Continue processing other files

    return (all_products, all_users, months_in_year)


def generate_search_index(data_dir: Path, output_path: Path) -> bool:
    """
    Generate search index from all aggregated files.

    Args:
        data_dir: Base data directory (contains aggregated/ subdirectory)
        output_path: Path to write search index JSON file

    Returns:
        True if successful, False otherwise
    """
    aggregated_dir = data_dir / "aggregated"
    if not aggregated_dir.exists():
        logger.error(f"Aggregated directory not found: {aggregated_dir}")
        return False

    # Collect all products and users
    all_products = {}
    all_users = {}
    all_months = set()
    all_years = set()

    # Process monthly files
    monthly_dir = aggregated_dir
    monthly_files = sorted(monthly_dir.glob("*.json"))
    for file_path in monthly_files:
        # Skip annual directory
        if file_path.is_dir():
            continue

        # Validate filename format (YYYY-MM.json)
        if not re.match(r"^\d{4}-\d{2}\.json$", file_path.name):
            continue

        month = file_path.stem
        products, users, _ = process_monthly_file(file_path, data_dir)
        merge_products(all_products, products)
        merge_users(all_users, users)
        all_months.add(month)
        all_years.add(month[:4])  # Extract year

    # Process annual files
    annual_dir = aggregated_dir / "annual"
    if annual_dir.exists():
        annual_files = sorted(annual_dir.glob("*.json"))
        for file_path in annual_files:
            # Validate filename format (YYYY.json)
            if not re.match(r"^\d{4}\.json$", file_path.name):
                continue

            year = file_path.stem
            products, users, months = process_annual_file(file_path, data_dir)
            merge_products(all_products, products)
            merge_users(all_users, users)
            all_months.update(months)
            all_years.add(year)

    # Convert products dict to list
    products_list = list(all_products.values())

    # Convert users dict to list
    users_list = list(all_users.values())

    # Sort months and years
    sorted_months = sorted(all_months)
    sorted_years = sorted(all_years)

    # Build search index structure
    search_index = {
        "products": products_list,
        "users": users_list,
        "available_months": sorted_months,
        "available_years": sorted_years,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    # Write search index
    try:
        from sotd.utils.file_io import save_json_data

        save_json_data(search_index, output_path, indent=2)
        logger.info(
            f"Generated search index: {len(products_list)} products, "
            f"{len(users_list)} users, {len(sorted_months)} months, {len(sorted_years)} years"
        )
        return True

    except Exception as e:
        logger.error(f"Error writing search index: {e}")
        return False


def main() -> int:
    """Main entry point for search index generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate search index from aggregated data")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Base data directory (default: data)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/search_index.json"),
        help="Output path for search index (default: data/search_index.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Generate search index
    success = generate_search_index(args.data_dir, args.output)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
