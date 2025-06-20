from typing import Any, Dict, List


def calculate_shaves(records: List[Dict[str, Any]]) -> int:
    """Calculate total number of shaves from records."""
    return len(records)


def calculate_unique_users(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique users from records."""
    authors = set()
    for record in records:
        author = record.get("author", "").strip()
        if author:
            authors.add(author)
    return len(authors)


def calculate_avg_shaves_per_user(records: List[Dict[str, Any]]) -> float:
    """Calculate average shaves per user."""
    total_shaves = calculate_shaves(records)
    unique_users = calculate_unique_users(records)
    if unique_users == 0:
        return 0.0
    return round(total_shaves / unique_users, 2)


def calculate_unique_soaps(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique soaps from records."""
    soaps = set()
    for record in records:
        soap = record.get("soap", {})
        matched = soap.get("matched", {})

        # Skip if no matched soap data
        if not matched or not matched.get("maker") or not matched.get("scent"):
            continue

        maker = matched.get("maker", "").strip()
        scent = matched.get("scent", "").strip()

        if maker and scent:
            soap_name = f"{maker} - {scent}"
            soaps.add(soap_name)

    return len(soaps)


def calculate_unique_brands(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique soap brands/makers from records."""
    brands = set()
    for record in records:
        soap = record.get("soap", {})
        matched = soap.get("matched", {})

        # Skip if no matched soap data or no maker
        if not matched or not matched.get("maker"):
            continue

        maker = matched.get("maker", "").strip()

        if maker:
            brands.add(maker)

    return len(brands)


def add_position_field(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add position field (1-based rank) to list of items."""
    for i, item in enumerate(items, 1):
        item["position"] = i
    return items


def calculate_metadata(records: List[Dict[str, Any]], month: str) -> Dict[str, Any]:
    """Generate metadata for aggregated data.

    Args:
        records: List of enriched comment records
        month: Month being processed (YYYY-MM format)

    Returns:
        Dictionary containing metadata with month, total_shaves, unique_shavers,
        avg_shaves_per_user, unique_soaps, and unique_brands
    """
    total_shaves = calculate_shaves(records)
    unique_shavers = calculate_unique_users(records)
    avg_shaves_per_user = calculate_avg_shaves_per_user(records)
    unique_soaps = calculate_unique_soaps(records)
    unique_brands = calculate_unique_brands(records)

    return {
        "month": month,
        "total_shaves": total_shaves,
        "unique_shavers": unique_shavers,
        "avg_shaves_per_user": avg_shaves_per_user,
        "unique_soaps": unique_soaps,
        "unique_brands": unique_brands,
    }
