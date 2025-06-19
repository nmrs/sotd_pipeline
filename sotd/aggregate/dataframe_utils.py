"""DataFrame utility functions for aggregation operations."""

import pandas as pd


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
