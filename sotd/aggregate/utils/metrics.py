from typing import Any, Dict, List


def calculate_shaves(records: List[Dict[str, Any]]) -> int:
    """Calculate total number of shaves from records."""
    return len(records)


def calculate_unique_users(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique users from records."""
    authors = set()
    for record in records:
        author = record.get("author", "")
        if author and author is not None:
            author = author.strip()
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


def calculate_median_shaves_per_user(records: List[Dict[str, Any]]) -> float:
    """Calculate median shaves per user."""
    if not records:
        return 0.0

    # Count shaves per user
    user_shaves = {}
    for record in records:
        author = record.get("author")
        if author and author.strip():  # Skip None, empty strings, and whitespace-only strings
            user_shaves[author.strip()] = user_shaves.get(author.strip(), 0) + 1

    if not user_shaves:
        return 0.0

    # Calculate median
    shave_counts = list(user_shaves.values())
    shave_counts.sort()
    n = len(shave_counts)

    if n % 2 == 0:
        # Even number of users, average of two middle values
        median = (shave_counts[n // 2 - 1] + shave_counts[n // 2]) / 2
    else:
        # Odd number of users, middle value
        median = shave_counts[n // 2]

    return round(median, 2)


def calculate_unique_soaps(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique soaps from records."""
    soaps = set()
    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
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
        soap = record.get("soap")
        if soap is None:
            continue
        matched = soap.get("matched", {})

        # Skip if no matched soap data or no maker
        if not matched or not matched.get("maker"):
            continue

        maker = matched.get("maker", "").strip()

        if maker:
            brands.add(maker)

    return len(brands)


def calculate_total_samples(records: List[Dict[str, Any]]) -> int:
    """Calculate total number of sample shaves from records."""
    total_samples = 0
    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
        enriched = soap.get("enriched", {})
        if enriched.get("sample_type"):
            total_samples += 1
    return total_samples


def calculate_sample_users(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique users who used samples."""
    sample_users = set()
    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
        enriched = soap.get("enriched", {})
        if enriched.get("sample_type"):
            author = record.get("author", "").strip()
            if author:
                sample_users.add(author)
    return len(sample_users)


def calculate_sample_brands(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique brands sampled."""
    sample_brands = set()
    for record in records:
        soap = record.get("soap")
        if soap is None:
            continue
        matched = soap.get("matched", {})
        if matched is None:
            continue
        brand = matched.get("maker") or ""
        if brand:
            brand = brand.strip()
        if brand:
            sample_brands.add(brand)
    return len(sample_brands)


def calculate_unique_razors(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique razors from records."""
    razors = set()
    for record in records:
        razor = record.get("razor")
        if razor is None:
            continue
        matched = razor.get("matched", {})

        # Skip if no matched razor data or no brand/model
        if not matched or not matched.get("brand") or not matched.get("model"):
            continue

        brand = matched.get("brand", "").strip()
        model = matched.get("model", "").strip()

        if brand and model:
            razor_name = f"{brand} {model}"
            razors.add(razor_name)

    return len(razors)


def calculate_unique_blades(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique blades from records."""
    blades = set()
    for record in records:
        blade = record.get("blade")
        if blade is None:
            continue
        matched = blade.get("matched", {})

        # Skip if no matched blade data or no brand/model
        if not matched or not matched.get("brand") or not matched.get("model"):
            continue

        brand = matched.get("brand", "").strip()
        model = matched.get("model", "").strip()

        if brand and model:
            blade_name = f"{brand} {model}"
            blades.add(blade_name)

    return len(blades)


def calculate_unique_brushes(records: List[Dict[str, Any]]) -> int:
    """Calculate number of unique brushes from records."""
    brushes = set()
    for record in records:
        brush = record.get("brush")
        if brush is None:
            continue
        matched = brush.get("matched", {})

        # Skip if no matched brush data or no brand/model
        if not matched or not matched.get("brand") or not matched.get("model"):
            continue

        brand = matched.get("brand", "").strip()
        model = matched.get("model", "").strip()

        if brand and model:
            brush_name = f"{brand} {model}"
            brushes.add(brush_name)

    return len(brushes)


def add_rank_field(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add rank field (1-based rank) to list of items."""
    for i, item in enumerate(items, 1):
        item["rank"] = i
    return items


def calculate_metadata(records: List[Dict[str, Any]], month: str) -> Dict[str, Any]:
    """Generate metadata for aggregated data.

    Args:
        records: List of enriched comment records
        month: Month being processed (YYYY-MM format)

    Returns:
        Dictionary containing metadata with month, total_shaves, unique_shavers,
        avg_shaves_per_user, median_shaves_per_user, unique_soaps, unique_brands,
        total_samples, sample_users, sample_brands, unique_razors, unique_blades,
        and unique_brushes
    """
    total_shaves = calculate_shaves(records)

    unique_shavers = calculate_unique_users(records)

    avg_shaves_per_user = calculate_avg_shaves_per_user(records)

    median_shaves_per_user = calculate_median_shaves_per_user(records)

    unique_soaps = calculate_unique_soaps(records)

    unique_brands = calculate_unique_brands(records)

    total_samples = calculate_total_samples(records)

    sample_users = calculate_sample_users(records)

    sample_brands = calculate_sample_brands(records)

    unique_razors = calculate_unique_razors(records)

    unique_blades = calculate_unique_blades(records)

    unique_brushes = calculate_unique_brushes(records)

    return {
        "month": month,
        "total_shaves": total_shaves,
        "unique_shavers": unique_shavers,
        "avg_shaves_per_user": avg_shaves_per_user,
        "median_shaves_per_user": median_shaves_per_user,
        "unique_soaps": unique_soaps,
        "unique_brands": unique_brands,
        "total_samples": total_samples,
        "sample_users": sample_users,
        "sample_brands": sample_brands,
        "unique_razors": unique_razors,
        "unique_blades": unique_blades,
        "unique_brushes": unique_brushes,
    }
