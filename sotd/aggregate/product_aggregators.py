"""Product-specific aggregation functions."""

from typing import Any, Dict, List

import pandas as pd

from sotd.aggregate.dataframe_utils import optimize_dataframe_operations, optimized_groupby_agg
from sotd.aggregate.performance_monitor import PerformanceMonitor


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
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_razors")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("aggregate_razors", 0)
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
                            "name": razor_name,
                            "brand": brand,
                            "model": model,
                            "format": format_type,
                            "user": record.get("author", "Unknown"),
                        }
                    )

    if not razor_data:
        if debug:
            print("[DEBUG] No valid razor data found")
        monitor.end("aggregate_razors", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(razor_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for razor aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during razor aggregation: {e}")

    # Group by razor name and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "name", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group razor data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during razor grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} razors ({invalid_records} invalid records)")

    monitor.end("aggregate_razors", len(razor_data))
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
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_blades")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("aggregate_blades", 0)
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

                    # Extract blade name from matched data
                    brand = matched.get("brand", "")
                    model = matched.get("model", "")

                    # Create a descriptive blade name (brand + model)
                    blade_name_parts = []
                    if brand:
                        blade_name_parts.append(brand)
                    if model:
                        blade_name_parts.append(model)

                    blade_name = " ".join(blade_name_parts) if blade_name_parts else "Unknown Blade"

                    blade_data.append(
                        {
                            "name": blade_name,
                            "brand": brand,
                            "model": model,
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
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for blade aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during blade aggregation: {e}")

    # Group by blade name and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "name", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group blade data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during blade grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} blades ({invalid_records} invalid records)")

    monitor.end("aggregate_blades", len(blade_data))
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
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_soaps")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("aggregate_soaps", 0)
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
                            "name": soap_name,
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
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for soap aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during soap aggregation: {e}")

    # Group by soap name and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "name", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group soap data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during soap grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} soaps ({invalid_records} invalid records)")

    monitor.end("aggregate_soaps", len(soap_data))
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
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_brushes")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("aggregate_brushes", 0)
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
                    model = matched.get("model", "")

                    # Create brush name from brand and model only
                    if brand and model:
                        brush_name = f"{brand} {model}"
                    elif brand:
                        brush_name = brand
                    else:
                        brush_name = "Unknown Brush"

                    brush_data.append(
                        {
                            "name": brush_name,
                            "brand": brand,
                            "model": model,
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
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for brush aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during brush aggregation: {e}")

    # Group by brush name and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "name", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group brush data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during brush grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} brushes ({invalid_records} invalid records)")

    monitor.end("aggregate_brushes", len(brush_data))
    return results  # type: ignore
