"""Core aggregation engine using pandas for efficient data processing."""

from typing import Any, Dict, List

import pandas as pd


def filter_matched_records(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Filter enriched records to only include those with successfully matched products.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of records with at least one successfully matched product

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to filter")
        return []

    matched_records = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        # Check if any product has a successful match
        has_match = False

        for product_field in ["razor", "blade", "soap", "brush"]:
            if product_field in record:
                product_data = record[product_field]
                if isinstance(product_data, dict) and "matched" in product_data:
                    matched_data = product_data["matched"]
                    if isinstance(matched_data, dict):
                        # Validate match_type if present
                        if "match_type" in matched_data:
                            match_type = matched_data["match_type"]
                            valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                            if (
                                not isinstance(match_type, str)
                                or match_type not in valid_match_types
                            ):
                                if debug:
                                    print(
                                        f"[DEBUG] Record {i}: {product_field}.match_type invalid: "
                                        f"{match_type}"
                                    )
                                invalid_records += 1
                                break

                        # Check if this product has a successful match
                        # Different products have different success indicators
                        if product_field == "razor" and matched_data.get("brand"):
                            has_match = True
                        elif product_field == "blade" and matched_data.get("brand"):
                            has_match = True
                        elif product_field == "soap" and matched_data.get("maker"):
                            has_match = True
                        elif product_field == "brush" and matched_data.get("brand"):
                            has_match = True

        if has_match:
            matched_records.append(record)

    if debug:
        print(
            f"[DEBUG] Filtered {len(records)} records to {len(matched_records)} matched records "
            f"({invalid_records} invalid records)"
        )

    return matched_records


def calculate_basic_metrics(records: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Any]:
    """
    Calculate basic metrics for the dataset.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        Dictionary with basic metrics

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return {
            "total_shaves": 0,
            "unique_shavers": 0,
            "avg_shaves_per_user": 0.0,
        }

    # Validate records before processing
    valid_records = []
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            continue

        if "author" not in record:
            if debug:
                print(f"[DEBUG] Record {i}: Missing 'author' field")
            continue

        if not isinstance(record["author"], str):
            if debug:
                print(
                    f"[DEBUG] Record {i}: 'author' should be string, got {type(record['author'])}"
                )
            continue

        valid_records.append(record)

    if not valid_records:
        if debug:
            print("[DEBUG] No valid records for basic metrics calculation")
        return {
            "total_shaves": 0,
            "unique_shavers": 0,
            "avg_shaves_per_user": 0.0,
        }

    # Convert to pandas DataFrame for efficient calculations
    try:
        df = pd.DataFrame(valid_records)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame from records: {e}")

    total_shaves = len(valid_records)
    unique_shavers = df["author"].nunique()
    avg_shaves_per_user = total_shaves / unique_shavers if unique_shavers > 0 else 0.0

    metrics = {
        "total_shaves": total_shaves,
        "unique_shavers": unique_shavers,
        "avg_shaves_per_user": round(avg_shaves_per_user, 2),
    }

    if debug:
        print(f"[DEBUG] Basic metrics: {metrics}")

    return metrics


def aggregate_razors(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate razor usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of razor aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    razor_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        if "razor" in record:
            razor_info = record["razor"]
            if isinstance(razor_info, dict) and "matched" in razor_info:
                matched = razor_info["matched"]
                if isinstance(matched, dict) and matched.get("brand"):
                    # Validate match_type if present
                    if "match_type" in matched:
                        match_type = matched["match_type"]
                        valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                        if not isinstance(match_type, str) or match_type not in valid_match_types:
                            if debug:
                                print(f"[DEBUG] Record {i}: razor.match_type invalid: {match_type}")
                            invalid_records += 1
                            continue

                    # Extract razor name from matched data
                    brand = matched.get("brand", "")
                    model = matched.get("model", "")
                    format_type = matched.get("format", "")

                    # Create a descriptive razor name
                    razor_name_parts = []
                    if brand:
                        razor_name_parts.append(brand)
                    if model:
                        razor_name_parts.append(model)
                    if format_type:
                        razor_name_parts.append(format_type)

                    razor_name = " ".join(razor_name_parts) if razor_name_parts else "Unknown Razor"

                    razor_data.append(
                        {
                            "razor_name": razor_name,
                            "brand": brand,
                            "model": model,
                            "format": format_type,
                            "user": record.get("author", "Unknown"),
                        }
                    )

    if not razor_data:
        if debug:
            print("[DEBUG] No valid razor data found")
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(razor_data)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for razor aggregation: {e}")

    # Group by razor name and calculate metrics
    try:
        grouped = df.groupby("razor_name").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group razor data: {e}")

    # Flatten column names
    grouped.columns = ["razor_name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} razors ({invalid_records} invalid records)")

    return results  # type: ignore


def aggregate_blades(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate blade usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of blade aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    blade_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        if "blade" in record:
            blade_info = record["blade"]
            if isinstance(blade_info, dict) and "matched" in blade_info:
                matched = blade_info["matched"]
                if isinstance(matched, dict) and matched.get("brand"):
                    # Validate match_type if present
                    if "match_type" in matched:
                        match_type = matched["match_type"]
                        valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                        if not isinstance(match_type, str) or match_type not in valid_match_types:
                            if debug:
                                print(f"[DEBUG] Record {i}: blade.match_type invalid: {match_type}")
                            invalid_records += 1
                            continue

                    blade_name = matched.get("brand", "Unknown Blade")
                    blade_data.append(
                        {
                            "blade_name": blade_name,
                            "user": record.get("author", "Unknown"),
                        }
                    )

    if not blade_data:
        if debug:
            print("[DEBUG] No valid blade data found")
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(blade_data)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for blade aggregation: {e}")

    # Group by blade name and calculate metrics
    try:
        grouped = df.groupby("blade_name").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group blade data: {e}")

    # Flatten column names
    grouped.columns = ["blade_name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} blades ({invalid_records} invalid records)")

    return results  # type: ignore


def aggregate_soaps(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate soap usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of soap aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    soap_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        if "soap" in record:
            soap_info = record["soap"]
            if isinstance(soap_info, dict) and "matched" in soap_info:
                matched = soap_info["matched"]
                if isinstance(matched, dict) and matched.get("maker"):
                    # Validate match_type if present
                    if "match_type" in matched:
                        match_type = matched["match_type"]
                        valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                        if not isinstance(match_type, str) or match_type not in valid_match_types:
                            if debug:
                                print(f"[DEBUG] Record {i}: soap.match_type invalid: {match_type}")
                            invalid_records += 1
                            continue

                    maker = matched.get("maker", "")
                    scent = matched.get("scent", "")

                    # Create soap name (maker + scent)
                    soap_name_parts = []
                    if maker:
                        soap_name_parts.append(maker)
                    if scent:
                        soap_name_parts.append(scent)

                    soap_name = " ".join(soap_name_parts) if soap_name_parts else "Unknown Soap"

                    soap_data.append(
                        {
                            "soap_name": soap_name,
                            "maker": maker,
                            "scent": scent,
                            "user": record.get("author", "Unknown"),
                        }
                    )

    if not soap_data:
        if debug:
            print("[DEBUG] No valid soap data found")
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(soap_data)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for soap aggregation: {e}")

    # Group by soap name and calculate metrics
    try:
        grouped = df.groupby("soap_name").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group soap data: {e}")

    # Flatten column names
    grouped.columns = ["soap_name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} soaps ({invalid_records} invalid records)")

    return results  # type: ignore


def aggregate_brushes(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of brush aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    brush_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        if "brush" in record:
            brush_info = record["brush"]
            if isinstance(brush_info, dict) and "matched" in brush_info:
                matched = brush_info["matched"]
                if isinstance(matched, dict) and matched.get("brand"):
                    # Validate match_type if present
                    if "match_type" in matched:
                        match_type = matched["match_type"]
                        valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
                        if not isinstance(match_type, str) or match_type not in valid_match_types:
                            if debug:
                                print(f"[DEBUG] Record {i}: brush.match_type invalid: {match_type}")
                            invalid_records += 1
                            continue

                    brand = matched.get("brand", "")
                    handle_maker = matched.get("handle_maker", "")
                    fiber = matched.get("fiber", "")
                    knot_size = matched.get("knot_size_mm", "")

                    # Create brush name
                    brush_name_parts = []
                    if handle_maker:
                        brush_name_parts.append(handle_maker)
                    if brand:
                        brush_name_parts.append(brand)
                    if fiber:
                        brush_name_parts.append(fiber)
                    if knot_size:
                        brush_name_parts.append(f"{knot_size}mm")

                    brush_name = " ".join(brush_name_parts) if brush_name_parts else "Unknown Brush"

                    brush_data.append(
                        {
                            "brush_name": brush_name,
                            "brand": brand,
                            "handle_maker": handle_maker,
                            "fiber": fiber,
                            "knot_size_mm": knot_size,
                            "user": record.get("author", "Unknown"),
                        }
                    )

    if not brush_data:
        if debug:
            print("[DEBUG] No valid brush data found")
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(brush_data)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for brush aggregation: {e}")

    # Group by brush name and calculate metrics
    try:
        grouped = df.groupby("brush_name").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group brush data: {e}")

    # Flatten column names
    grouped.columns = ["brush_name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} brushes ({invalid_records} invalid records)")

    return results  # type: ignore


def aggregate_users(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate user statistics (top shavers).

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of user aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    # Validate records before processing
    valid_records = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        if "author" not in record:
            if debug:
                print(f"[DEBUG] Record {i}: Missing 'author' field")
            invalid_records += 1
            continue

        if not isinstance(record["author"], str):
            if debug:
                print(
                    f"[DEBUG] Record {i}: 'author' should be string, "
                    f"got {type(record['author'])}"
                )
            invalid_records += 1
            continue

        if "id" not in record:
            if debug:
                print(f"[DEBUG] Record {i}: Missing 'id' field")
            invalid_records += 1
            continue

        valid_records.append(record)

    if not valid_records:
        if debug:
            print("[DEBUG] No valid records for user aggregation")
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(valid_records)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for user aggregation: {e}")

    # Group by user and calculate metrics
    try:
        grouped = df.groupby("author").agg({"id": "count"}).reset_index()  # Count shaves per user
    except Exception as e:
        raise ValueError(f"Failed to group user data: {e}")

    grouped.columns = ["user", "shaves"]

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} users ({invalid_records} invalid records)")

    return results  # type: ignore
