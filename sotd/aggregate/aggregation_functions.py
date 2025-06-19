"""Core aggregation functions for data processing."""

from typing import Any, Dict, List

import pandas as pd

from sotd.aggregate.dataframe_utils import optimize_dataframe_operations
from sotd.aggregate.performance_monitor import PerformanceMonitor


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
    monitor = PerformanceMonitor(debug)
    monitor.start("filter_matched_records")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to filter")
        monitor.end("filter_matched_records", 0)
        return []

    matched_records = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        # Check if any product has a non-empty 'matched' field
        has_match = False
        for product_field in ["razor", "blade", "soap", "brush"]:
            if product_field in record:
                product_data = record[product_field]
                if (
                    isinstance(product_data, dict)
                    and "matched" in product_data
                    and isinstance(product_data["matched"], dict)
                    and len(product_data["matched"]) > 0
                ):
                    has_match = True
                    break
        if has_match:
            matched_records.append(record)

    if debug:
        print(
            f"[DEBUG] Filtered {len(records)} records to {len(matched_records)} matched records "
            f"({invalid_records} invalid records)"
        )

    monitor.end("filter_matched_records", len(matched_records))
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
    monitor = PerformanceMonitor(debug)
    monitor.start("calculate_basic_metrics")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("calculate_basic_metrics", 0)
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
        monitor.end("calculate_basic_metrics", 0)
        return {
            "total_shaves": 0,
            "unique_shavers": 0,
            "avg_shaves_per_user": 0.0,
        }

    # Convert to pandas DataFrame for efficient calculations
    try:
        df = pd.DataFrame(valid_records)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame from records: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during basic metrics calculation: {e}")

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

    monitor.end("calculate_basic_metrics", len(valid_records))
    return metrics
