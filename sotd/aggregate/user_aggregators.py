"""User-related aggregation functions."""

import calendar
import datetime
from datetime import date
from typing import Any, Dict, List

import pandas as pd

from sotd.aggregate.dataframe_utils import optimize_dataframe_operations
from sotd.aggregate.performance_monitor import PerformanceMonitor
from sotd.utils.date_utils import parse_thread_date


def aggregate_users(records: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Aggregate user statistics (top shavers) with missed days calculation.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of user aggregation results with shaves and missed days

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_users")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        monitor.end("aggregate_users", 0)
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
                    f"[DEBUG] Record {i}: 'author' should be string, got {type(record['author'])}"
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
        monitor.end("aggregate_users", 0)
        return []

    # Extract month from first record's thread_title to determine total days
    month_info = None
    for record in valid_records:
        if "thread_title" in record and record["thread_title"]:
            # Try to parse the date from thread title
            parsed_date = parse_thread_date(record["thread_title"], 2025)  # year hint
            if parsed_date:
                month_info = {"year": parsed_date.year, "month": parsed_date.month}
                break

    if not month_info:
        if debug:
            print("[DEBUG] Could not determine month from thread titles, using fallback")
        # Fallback: try to extract from metadata or use current month
        now = datetime.datetime.now()
        month_info = {"year": now.year, "month": now.month}

    # Calculate total days in the month
    year = month_info["year"]
    month = month_info["month"]
    total_days_in_month = calendar.monthrange(year, month)[1]

    if debug:
        print(f"[DEBUG] Processing month {year}-{month:02d} with {total_days_in_month} days")

    # Process records to extract user, shaves, and unique days
    user_data = {}

    for record in valid_records:
        author = record["author"]
        thread_title = record.get("thread_title", "")

        # Initialize user data if not exists
        if author not in user_data:
            user_data[author] = {"shaves": 0, "unique_days": set(), "thread_titles": set()}

        # Count shaves
        user_data[author]["shaves"] += 1

        # Extract date from thread title
        if thread_title:
            parsed_date = parse_thread_date(thread_title, year)
            if parsed_date:
                user_data[author]["unique_days"].add(parsed_date.day)
            user_data[author]["thread_titles"].add(thread_title)

    # Convert to list and calculate missed days
    results = []
    for author, data in user_data.items():
        unique_days_count = len(data["unique_days"])
        missed_days = total_days_in_month - unique_days_count

        # Calculate which specific days were missed, as full YYYY-MM-DD strings
        all_days_in_month = set(range(1, total_days_in_month + 1))
        missed_days_set = all_days_in_month - data["unique_days"]
        missed_day_list = [date(year, month, d).isoformat() for d in sorted(missed_days_set)]

        results.append(
            {
                "user": author,  # No 'u/' prefix for compatibility
                "shaves": data["shaves"],
                "unique_days": unique_days_count,
                "missed_days": missed_days,
                "missed_day_list": missed_day_list,  # List of actual missed days as YYYY-MM-DD
                "avg_shaves_per_user": 1.0,  # Each user's avg is always 1.0 (all their own shaves)
            }
        )

    # Sort by shaves (descending), then by missed days (ascending)
    results.sort(key=lambda x: (-x["shaves"], x["missed_days"]))

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} users ({invalid_records} invalid records)")
        print(f"[DEBUG] Total days in month: {total_days_in_month}")

    monitor.end("aggregate_users", len(valid_records))
    return results


def aggregate_user_blade_usage(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate per-user blade usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of per-user blade usage aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_user_blade_usage")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for per-user blade usage")
        monitor.end("aggregate_user_blade_usage", 0)
        return []

    usage_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        # Extract blade information and use count
        blade_name = None
        use_count = None

        # Get blade name from matched data
        if "blade" in record:
            blade_info = record["blade"]
            if isinstance(blade_info, dict) and "matched" in blade_info:
                matched = blade_info["matched"]
                if isinstance(matched, dict):
                    brand = matched.get("brand", "")
                    model = matched.get("model", "")
                    if brand and model:
                        blade_name = f"{brand} {model}".strip()

        # Get use count from enriched data
        if "blade" in record:
            blade_info = record["blade"]
            if isinstance(blade_info, dict) and "enriched" in blade_info:
                enriched = blade_info["enriched"]
                if isinstance(enriched, dict):
                    use_count = enriched.get("use_count")

        # Only include records where blade is matched and use count is available
        if blade_name and use_count is not None:
            usage_data.append(
                {
                    "blade": blade_name,
                    "user": record.get("author", "Unknown"),
                    "use_count": use_count,
                }
            )

    if not usage_data:
        if debug:
            print("[DEBUG] No valid per-user blade usage data found")
        monitor.end("aggregate_user_blade_usage", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(usage_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for per-user blade usage aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during per-user blade usage aggregation: {e}")

    # Group by user and blade, calculate average use count
    try:
        grouped = (
            df.groupby(["user", "blade"], observed=False)
            .agg({"use_count": ["mean", "count", "max"]})
            .reset_index()
        )
        # Flatten column names
        grouped.columns = ["user", "blade", "avg_use_count", "shaves", "max_use_count"]
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group per-user blade usage data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during per-user blade usage grouping: {e}")

    # Round average use count to 2 decimal places
    grouped["avg_use_count"] = grouped["avg_use_count"].round(2)

    # Sort by average use count (descending), then by shaves (descending) as tie breaker
    grouped = grouped.sort_values(["avg_use_count", "shaves"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} per-user blade usage records "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_user_blade_usage", len(usage_data))
    return results  # type: ignore
