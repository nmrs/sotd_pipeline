"""Core aggregation engine using pandas for efficient data processing."""

import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import psutil
from datetime import date


class PerformanceMonitor:
    """Monitor performance metrics during aggregation."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.start_time = None
        self.start_memory = None
        self.metrics = {}

    def start(self, operation: str):
        """Start timing an operation."""
        if self.debug:
            self.start_time = time.time()
            self.start_memory = self._get_memory_usage()
            print(f"[DEBUG] Starting {operation}")

    def end(self, operation: str, record_count: Optional[int] = None):
        """End timing an operation and record metrics."""
        if self.debug and self.start_time:
            elapsed = time.time() - self.start_time
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - self.start_memory if self.start_memory else 0

            self.metrics[operation] = {
                "elapsed_seconds": elapsed,
                "record_count": record_count,
                "records_per_second": (
                    record_count / elapsed if record_count and elapsed > 0 else 0
                ),
                "memory_start_mb": self.start_memory,
                "memory_end_mb": end_memory,
                "memory_delta_mb": memory_delta,
            }
            print(f"[DEBUG] {operation} completed in {elapsed:.3f}s")
            if record_count:
                rate = record_count / elapsed
                print(
                    f"[DEBUG] {operation} processed {record_count} records "
                    f"at {rate:.1f} records/sec"
                )
            print(f"[DEBUG] {operation} memory: {end_memory:.1f}MB (delta: {memory_delta:+.1f}MB)")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except (ImportError, AttributeError):
            # Fallback if psutil is not available
            return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return self.metrics


def optimize_dataframe_operations(df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    """
    Optimize DataFrame for better performance.

    Args:
        df: Input DataFrame
        debug: Enable debug logging

    Returns:
        Optimized DataFrame
    """
    if debug:
        print(f"[DEBUG] DataFrame optimization: {len(df)} rows, {len(df.columns)} columns")

    # Use more efficient dtypes where possible
    for col in df.columns:
        if df[col].dtype == "object":
            # Skip dictionary columns (they can't be converted to category)
            if bool(df[col].apply(lambda x: isinstance(x, dict)).any()):
                if debug:
                    print(f"[DEBUG] Skipping dictionary column '{col}'")
                continue

            # Convert object columns to category if they have limited unique values
            try:
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.5:  # Less than 50% unique values
                    df[col] = df[col].astype("category")
                    if debug:
                        print(
                            f"[DEBUG] Converted column '{col}' to category "
                            f"(unique ratio: {unique_ratio:.2f})"
                        )
            except (TypeError, ValueError) as e:
                if debug:
                    print(f"[DEBUG] Could not optimize column '{col}': {e}")
                continue

    # Optimize memory usage by downcasting numeric types
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            try:
                if df[col].dtype == "int64":
                    # Downcast integers
                    df[col] = pd.to_numeric(df[col], downcast="integer")
                elif df[col].dtype == "float64":
                    # Downcast floats
                    df[col] = pd.to_numeric(df[col], downcast="float")
                if debug:
                    print(f"[DEBUG] Downcasted column '{col}' to {df[col].dtype}")
            except (TypeError, ValueError) as e:
                if debug:
                    print(f"[DEBUG] Could not downcast column '{col}': {e}")
                continue

    return df


def optimized_groupby_agg(
    df: pd.DataFrame, group_col: str, agg_col: str, agg_funcs: list, debug: bool = False
) -> pd.DataFrame:
    """
    Perform optimized groupby aggregation with explicit observed=False to avoid
    deprecation warnings.

    Args:
        df: Input DataFrame
        group_col: Column to group by
        agg_col: Column to aggregate
        agg_funcs: List of aggregation functions
        debug: Enable debug logging

    Returns:
        Grouped DataFrame with flattened column names
    """
    if debug:
        print(f"[DEBUG] Grouping by '{group_col}' with aggregation on '{agg_col}'")

    # Perform groupby with explicit observed=False to avoid deprecation warning
    if len(agg_funcs) == 1:
        # Single aggregation function
        grouped = df.groupby(group_col, observed=False).agg({agg_col: agg_funcs[0]}).reset_index()
        # Flatten column names for single aggregation
        grouped.columns = [group_col, agg_col]
    else:
        # Multiple aggregation functions
        grouped = df.groupby(group_col, observed=False).agg({agg_col: agg_funcs}).reset_index()
        # Flatten column names
        grouped.columns = [group_col] + [f"{agg_col}_{func}" for func in agg_funcs]

    return grouped


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
            from sotd.utils.date_utils import parse_thread_date

            # Try to parse the date from thread title
            parsed_date = parse_thread_date(record["thread_title"], 2025)  # year hint
            if parsed_date:
                month_info = {"year": parsed_date.year, "month": parsed_date.month}
                break

    if not month_info:
        if debug:
            print("[DEBUG] Could not determine month from thread titles, using fallback")
        # Fallback: try to extract from metadata or use current month
        import datetime

        now = datetime.datetime.now()
        month_info = {"year": now.year, "month": now.month}

    # Calculate total days in the month
    import calendar

    year = month_info["year"]
    month = month_info["month"]
    total_days_in_month = calendar.monthrange(year, month)[1]

    if debug:
        print(f"[DEBUG] Processing month {year}-{month:02d} " f"with {total_days_in_month} days")

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
            from sotd.utils.date_utils import parse_thread_date

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


def aggregate_razor_manufacturers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate razor usage statistics by manufacturer (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for razor manufacturer aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor manufacturer aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group razor manufacturer data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor manufacturer grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_blade_manufacturers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate blade usage statistics by manufacturer (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        blade = record.get("blade", {})
        matched = blade.get("matched", {}) if isinstance(blade, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for blade manufacturer aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during blade manufacturer aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group blade manufacturer data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during blade manufacturer grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_soap_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate soap usage statistics by maker (manufacturer).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        soap = record.get("soap", {})
        matched = soap.get("matched", {}) if isinstance(soap, dict) else {}
        maker = matched.get("maker")
        if maker:
            data.append({"maker": maker, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for soap maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during soap maker aggregation: {e}")

    # Group by maker and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "maker", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group soap maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during soap maker grouping: {e}")

    grouped.columns = ["maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_knot_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by knot maker (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush knot maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot maker aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush knot maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot maker grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_handle_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by handle maker.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        handle_maker = matched.get("handle_maker")
        if handle_maker:
            data.append({"handle_maker": handle_maker, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush handle maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush handle maker aggregation: {e}")

    # Group by handle_maker and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "handle_maker", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush handle maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush handle maker grouping: {e}")

    grouped.columns = ["handle_maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_fibers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by fiber type.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    fiber_data = []
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

                    fiber = matched.get("fiber", None)
                    if fiber:
                        fiber_data.append(
                            {
                                "fiber": fiber,
                                "user": record.get("author", "Unknown"),
                            }
                        )

    if not fiber_data:
        if debug:
            print("[DEBUG] No valid brush fiber data found")
        return []

    try:
        df = pd.DataFrame(fiber_data)
        df = optimize_dataframe_operations(df, debug)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for brush fiber aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "fiber", "user", ["count", "nunique"], debug)
    except Exception as e:
        raise ValueError(f"Failed to group brush fiber data: {e}")

    grouped.columns = ["fiber", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} brush fibers ({invalid_records} invalid records)")

    return results  # type: ignore


def aggregate_brush_knot_sizes(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by knot size (mm).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        return []

    knot_size_data = []
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

                    knot_size = matched.get("knot_size_mm", None)
                    if knot_size:
                        knot_size_str = str(knot_size)
                        knot_size_data.append(
                            {
                                "knot_size_mm": knot_size_str,
                                "user": record.get("author", "Unknown"),
                            }
                        )

    if not knot_size_data:
        if debug:
            print("[DEBUG] No valid brush knot size data found")
        return []

    try:
        df = pd.DataFrame(knot_size_data)
        df = optimize_dataframe_operations(df, debug)
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for brush knot size aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "knot_size_mm", "user", ["count", "nunique"], debug)
    except Exception as e:
        raise ValueError(f"Failed to group brush knot size data: {e}")

    grouped.columns = ["knot_size_mm", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} brush knot sizes "
            f"({invalid_records} invalid records)"
        )

    return results  # type: ignore


def aggregate_blackbird_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Blackland Blackbird plate usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Blackbird plate aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_blackbird_plates")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for Blackbird plates")
        monitor.end("aggregate_blackbird_plates", 0)
        return []

    plate_data = []
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
                if isinstance(matched, dict) and matched.get("brand") == "Blackland":
                    model = matched.get("model", "")
                    if "Blackbird" in model:
                        # Check for enriched plate information
                        enriched = razor_info.get("enriched", {})
                        plate = enriched.get("plate") if isinstance(enriched, dict) else None

                        if plate:
                            plate_data.append(
                                {
                                    "plate": plate,
                                    "user": record.get("author", "Unknown"),
                                }
                            )

    if not plate_data:
        if debug:
            print("[DEBUG] No valid Blackbird plate data found")
        monitor.end("aggregate_blackbird_plates", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(plate_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for Blackbird plate aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Blackbird plate aggregation: {e}")

    # Group by plate and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group Blackbird plate data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Blackbird plate grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["plate", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} Blackbird plates "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_blackbird_plates", len(plate_data))
    return results  # type: ignore


def aggregate_christopher_bradley_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Karve Christopher Bradley plate usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Christopher Bradley plate aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_christopher_bradley_plates")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for Christopher Bradley plates")
        monitor.end("aggregate_christopher_bradley_plates", 0)
        return []

    plate_data = []
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
                if isinstance(matched, dict) and matched.get("brand") == "Karve":
                    model = matched.get("model", "")
                    if model == "Christopher Bradley":
                        # Check for enriched plate information
                        enriched = razor_info.get("enriched", {})
                        if isinstance(enriched, dict):
                            plate_level = enriched.get("plate_level")
                            plate_type = enriched.get("plate_type", "SB")  # Default to SB

                            if plate_level:
                                # Combine plate level and type for aggregation
                                plate_identifier = f"{plate_level} {plate_type}"
                                plate_data.append(
                                    {
                                        "plate": plate_identifier,
                                        "user": record.get("author", "Unknown"),
                                    }
                                )

    if not plate_data:
        if debug:
            print("[DEBUG] No valid Christopher Bradley plate data found")
        monitor.end("aggregate_christopher_bradley_plates", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(plate_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(
            f"Failed to create DataFrame for Christopher Bradley plate aggregation: {e}"
        )
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Christopher Bradley plate aggregation: {e}")

    # Group by plate and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group Christopher Bradley plate data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Christopher Bradley plate grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["plate", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} Christopher Bradley plates "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_christopher_bradley_plates", len(plate_data))
    return results  # type: ignore


def aggregate_game_changer_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate RazoRock Game Changer plate usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Game Changer plate aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_game_changer_plates")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for Game Changer plates")
        monitor.end("aggregate_game_changer_plates", 0)
        return []

    plate_data = []
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
                if isinstance(matched, dict) and matched.get("brand") == "RazoRock":
                    model = matched.get("model", "")
                    if "Game Changer" in model:
                        # Check for enriched gap and variant information
                        enriched = razor_info.get("enriched", {})
                        if isinstance(enriched, dict):
                            gap = enriched.get("gap")
                            variant = enriched.get("variant")

                            if gap or variant:
                                # Create plate identifier combining gap and variant
                                plate_parts = []
                                if gap:
                                    plate_parts.append(f"Gap {gap}")
                                if variant:
                                    plate_parts.append(variant)

                                plate_identifier = " ".join(plate_parts)
                                plate_data.append(
                                    {
                                        "plate": plate_identifier,
                                        "user": record.get("author", "Unknown"),
                                    }
                                )

    if not plate_data:
        if debug:
            print("[DEBUG] No valid Game Changer plate data found")
        monitor.end("aggregate_game_changer_plates", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(plate_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for Game Changer plate aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Game Changer plate aggregation: {e}")

    # Group by plate and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group Game Changer plate data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Game Changer plate grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["plate", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} Game Changer plates "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_game_changer_plates", len(plate_data))
    return results  # type: ignore


def aggregate_super_speed_tips(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Gillette Super Speed tip usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of Super Speed tip aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_super_speed_tips")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for Super Speed tips")
        monitor.end("aggregate_super_speed_tips", 0)
        return []

    tip_data = []
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
                if isinstance(matched, dict) and matched.get("brand") == "Gillette":
                    model = matched.get("model", "")
                    if model == "Super Speed":
                        # Check for enriched tip information
                        enriched = razor_info.get("enriched", {})
                        if isinstance(enriched, dict):
                            tip = enriched.get("super_speed_tip")

                            if tip:
                                tip_data.append(
                                    {
                                        "tip": tip,
                                        "user": record.get("author", "Unknown"),
                                    }
                                )

    if not tip_data:
        if debug:
            print("[DEBUG] No valid Super Speed tip data found")
        monitor.end("aggregate_super_speed_tips", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(tip_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for Super Speed tip aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Super Speed tip aggregation: {e}")

    # Group by tip and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "tip", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group Super Speed tip data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during Super Speed tip grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["tip", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} Super Speed tips "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_super_speed_tips", len(tip_data))
    return results  # type: ignore


def aggregate_straight_razor_specs(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate straight razor specification usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of straight razor specification aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_straight_razor_specs")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for straight razor specs")
        monitor.end("aggregate_straight_razor_specs", 0)
        return []

    spec_data = []
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
                if isinstance(matched, dict) and matched.get("format") == "Straight":
                    # Check for enriched specification information
                    enriched = razor_info.get("enriched", {})
                    if isinstance(enriched, dict):
                        grind = enriched.get("grind")
                        width = enriched.get("width")
                        point = enriched.get("point")

                        # Create specification identifier
                        specs = []
                        if grind:
                            specs.append(f"Grind: {grind}")
                        if width:
                            specs.append(f"Width: {width}")
                        if point:
                            specs.append(f"Point: {point}")

                        if specs:
                            spec_identifier = " | ".join(specs)
                            spec_data.append(
                                {
                                    "specs": spec_identifier,
                                    "user": record.get("author", "Unknown"),
                                }
                            )

    if not spec_data:
        if debug:
            print("[DEBUG] No valid straight razor specification data found")
        monitor.end("aggregate_straight_razor_specs", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(spec_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for straight razor spec aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during straight razor spec aggregation: {e}")

    # Group by specs and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "specs", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group straight razor spec data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during straight razor spec grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["specs", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} straight razor specifications "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_straight_razor_specs", len(spec_data))
    return results  # type: ignore


def aggregate_razor_blade_combinations(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate razor-blade combination usage statistics.

    Args:
        records: List of enriched comment records
        debug: Enable debug logging

    Returns:
        List of razor-blade combination aggregation results

    Raises:
        ValueError: If records list is invalid or contains invalid data
    """
    monitor = PerformanceMonitor(debug)
    monitor.start("aggregate_razor_blade_combinations")

    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")

    if not records:
        if debug:
            print("[DEBUG] No records to process for razor-blade combinations")
        monitor.end("aggregate_razor_blade_combinations", 0)
        return []

    combination_data = []
    invalid_records = 0

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            if debug:
                print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
            invalid_records += 1
            continue

        # Extract razor and blade information
        razor_name = None
        blade_name = None

        # Get razor name from matched data
        if "razor" in record:
            razor_info = record["razor"]
            if isinstance(razor_info, dict) and "matched" in razor_info:
                matched = razor_info["matched"]
                if isinstance(matched, dict):
                    brand = matched.get("brand", "")
                    model = matched.get("model", "")
                    if brand and model:
                        razor_name = f"{brand} {model}".strip()

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

        # Only include records where both razor and blade are matched
        if razor_name and blade_name:
            combination_data.append(
                {
                    "razor": razor_name,
                    "blade": blade_name,
                    "combination": f"{razor_name} + {blade_name}",
                    "user": record.get("author", "Unknown"),
                }
            )

    if not combination_data:
        if debug:
            print("[DEBUG] No valid razor-blade combination data found")
        monitor.end("aggregate_razor_blade_combinations", 0)
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(combination_data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for razor-blade combination aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during razor-blade combination aggregation: {e}")

    # Group by combination and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "combination", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group razor-blade combination data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during razor-blade combination grouping: {e}")

    # Rename columns to match expected output
    grouped.columns = ["combination", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending), then by unique_users (descending) as tie breaker
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} razor-blade combinations "
            f"({invalid_records} invalid records)"
        )

    monitor.end("aggregate_razor_blade_combinations", len(combination_data))
    return results  # type: ignore


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
