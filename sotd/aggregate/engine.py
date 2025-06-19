"""Core aggregation engine using pandas for efficient data processing."""

import time
from typing import Any, Dict, List, Optional

import pandas as pd


class PerformanceMonitor:
    """Monitor performance metrics during aggregation."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.start_time = None
        self.metrics = {}

    def start(self, operation: str):
        """Start timing an operation."""
        if self.debug:
            self.start_time = time.time()
            print(f"[DEBUG] Starting {operation}")

    def end(self, operation: str, record_count: Optional[int] = None):
        """End timing an operation and record metrics."""
        if self.debug and self.start_time:
            elapsed = time.time() - self.start_time
            self.metrics[operation] = {
                "elapsed_seconds": elapsed,
                "record_count": record_count,
                "records_per_second": (
                    record_count / elapsed if record_count and elapsed > 0 else 0
                ),
            }
            print(f"[DEBUG] {operation} completed in {elapsed:.3f}s")
            if record_count:
                rate = record_count / elapsed
                print(
                    f"[DEBUG] {operation} processed {record_count} records "
                    f"at {rate:.1f} records/sec"
                )

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

    return df


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
        grouped = df.groupby("name").agg({"user": ["count", "nunique"]}).reset_index()
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group razor data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during razor grouping: {e}")

    # Flatten column names
    grouped.columns = ["name", "shaves", "unique_users"]

    # Calculate average shaves per user
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

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
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for blade aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during blade aggregation: {e}")

    # Group by blade name and calculate metrics
    try:
        grouped = df.groupby("name").agg({"user": ["count", "nunique"]}).reset_index()
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group blade data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during blade grouping: {e}")

    # Flatten column names
    grouped.columns = ["name", "shaves", "unique_users"]

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
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for soap aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during soap aggregation: {e}")

    # Group by soap name and calculate metrics
    try:
        grouped = df.groupby("name").agg({"user": ["count", "nunique"]}).reset_index()
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group soap data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during soap grouping: {e}")

    # Flatten column names
    grouped.columns = ["name", "shaves", "unique_users"]

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
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for brush aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during brush aggregation: {e}")

    # Group by brush name and calculate metrics
    try:
        grouped = df.groupby("name").agg({"user": ["count", "nunique"]}).reset_index()
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group brush data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during brush grouping: {e}")

    # Flatten column names
    grouped.columns = ["name", "shaves", "unique_users"]

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
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(valid_records)
    except (ValueError, TypeError, KeyError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to create DataFrame for user aggregation: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during user aggregation: {e}")

    # Group by user and calculate metrics
    try:
        grouped = df.groupby("author").agg({"id": "count"}).reset_index()
    except (KeyError, ValueError) as e:
        # These are data structure issues that should fail fast
        raise ValueError(f"Failed to group user data: {e}")
    except ImportError as e:
        # Pandas import issues - external dependency failure
        raise RuntimeError(f"Pandas import error during user grouping: {e}")

    grouped.columns = ["user", "shaves"]
    grouped["avg_shaves_per_user"] = 1.0  # Each user's avg is always 1.0 (all their own shaves)

    # Sort by shaves (descending)
    grouped = grouped.sort_values("shaves", ascending=False)

    # Convert back to list of dictionaries
    results = grouped.to_dict("records")

    if debug:
        print(f"[DEBUG] Aggregated {len(results)} users ({invalid_records} invalid records)")

    return results  # type: ignore


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
    import pandas as pd

    df = pd.DataFrame(data)
    grouped = df.groupby("brand").agg({"user": ["count", "nunique"]}).reset_index()
    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    import pandas as pd

    df = pd.DataFrame(data)
    grouped = df.groupby("brand").agg({"user": ["count", "nunique"]}).reset_index()
    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    import pandas as pd

    df = pd.DataFrame(data)
    grouped = df.groupby("maker").agg({"user": ["count", "nunique"]}).reset_index()
    grouped.columns = ["maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    import pandas as pd

    df = pd.DataFrame(data)
    grouped = df.groupby("brand").agg({"user": ["count", "nunique"]}).reset_index()
    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    import pandas as pd

    df = pd.DataFrame(data)
    grouped = df.groupby("handle_maker").agg({"user": ["count", "nunique"]}).reset_index()
    grouped.columns = ["handle_maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for brush fiber aggregation: {e}")

    try:
        grouped = df.groupby("fiber").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group brush fiber data: {e}")

    grouped.columns = ["fiber", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
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
    except Exception as e:
        raise ValueError(f"Failed to create DataFrame for brush knot size aggregation: {e}")

    try:
        grouped = df.groupby("knot_size_mm").agg({"user": ["count", "nunique"]}).reset_index()
    except Exception as e:
        raise ValueError(f"Failed to group brush knot size data: {e}")

    grouped.columns = ["knot_size_mm", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values("shaves", ascending=False)
    results = grouped.to_dict("records")

    if debug:
        print(
            f"[DEBUG] Aggregated {len(results)} brush knot sizes "
            f"({invalid_records} invalid records)"
        )

    return results  # type: ignore
