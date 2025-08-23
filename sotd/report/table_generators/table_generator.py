"""Universal table generator for report templates."""

from typing import Any, Dict, List, Optional

import pandas as pd


class TableGenerator:
    """Universal table generator that converts aggregated data to markdown tables.

    This generator takes aggregated data and converts it directly to markdown tables
    using pandas DataFrame and to_markdown() method. It supports basic parameter
    filtering for ranks and rows, and handles the mapping from template names
    to data keys.
    """

    def __init__(
        self,
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Dict[str, Any]]] = None,
        current_month: Optional[str] = None,
        debug: bool = False,
    ):
        """Initialize the table generator.

        Args:
            data: Dictionary containing aggregated data for each aggregator
            comparison_data: Optional dictionary of historical data for delta calculations
            current_month: Current month in YYYY-MM format for delta calculations
            debug: Enable debug output
        """
        self.data = data
        self.comparison_data = comparison_data or {}
        self.current_month = current_month
        self.debug = debug

        # No more hardcoded mappings - we'll convert kebab-case to snake_case dynamically

    def _preserve_acronyms(self, text: str) -> str:
        """Preserve acronyms while converting text to title case.

        Args:
            text: Text to format

        Returns:
            Formatted text with preserved acronyms
        """
        # Define common acronyms that should stay uppercase
        acronyms = {
            "de",
            "ac",
            "oc",
            "sb",
            "aa",
            "b",
            "c",
            "d",
            "f",  # Razor formats
            "mm",
            "ptfe",
            "gem",
            "weck",
            "valet",
            "rolls",  # Brand/model acronyms
            "lite",
            "standard",
            "vs",  # Special cases
        }

        # Convert to title case while preserving acronyms
        words = text.split()
        formatted_words = []

        for word in words:
            if word.lower() in acronyms:
                # Keep acronyms in uppercase
                formatted_words.append(word.upper())
            elif word.lower() == "per":
                # Keep "per" lowercase
                formatted_words.append(word.lower())
            else:
                # Convert to title case
                formatted_words.append(word.title())

        return " ".join(formatted_words)

    def _format_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format column names to Title Case with acronym preservation.

        Args:
            df: DataFrame to format

        Returns:
            DataFrame with formatted column names
        """
        formatted_df = df.copy()

        for col in formatted_df.columns:
            if col.startswith("Δ"):
                # Keep delta columns as-is
                continue

            # Convert to title case while preserving acronyms
            formatted_name = self._preserve_acronyms(col.title())
            formatted_df = formatted_df.rename(columns={col: formatted_name})

        return formatted_df

    def _format_usernames(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format usernames with "u/" prefix for Reddit display.

        Args:
            df: DataFrame to format

        Returns:
            DataFrame with formatted usernames
        """
        formatted_df = df.copy()

        # Check if this table has user-related columns
        user_columns = [col for col in formatted_df.columns if col.lower() in ["user", "author"]]

        for col in user_columns:
            if col in formatted_df.columns:
                # Add "u/" prefix to usernames that don't already have it
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"u/{x}" if x and not str(x).startswith("u/") else x
                )

        return formatted_df

    def _format_rank_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format rank column to show equal ranks as N=.

        Args:
            df: DataFrame with rank column

        Returns:
            DataFrame with formatted rank column
        """
        if "rank" not in df.columns:
            return df

        # Create a copy to avoid modifying the original
        df = df.copy()

        # Count occurrences of each rank
        rank_counts = df["rank"].value_counts().to_dict()

        # Format ranks: add = for equal ranks, space for single ranks
        def format_rank(rank):
            if rank_counts.get(rank, 1) > 1:
                return f"{rank}="
            return f"{rank} "  # Add space to force string formatting

        # Apply formatting to rank column
        df["rank"] = df["rank"].apply(format_rank)

        return df

    def _get_comparison_periods(self, current_month: str) -> List[str]:
        """Get comparison periods for delta calculations.

        Args:
            current_month: Current month in YYYY-MM format

        Returns:
            List of comparison periods: [previous_month, previous_year, five_years_ago]
        """
        from datetime import datetime

        # Parse current month
        current_date = datetime.strptime(current_month, "%Y-%m")

        # Previous month
        if current_date.month == 1:
            prev_month = current_date.replace(year=current_date.year - 1, month=12)
        else:
            prev_month = current_date.replace(month=current_date.month - 1)

        # Previous year (same month)
        prev_year = current_date.replace(year=current_date.year - 1)

        # Five years ago (same month)
        five_years_ago = current_date.replace(year=current_date.year - 5)

        # Format periods to match the keys used in comparison_data
        month_names = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }

        return [
            f"{month_names[prev_month.month]} {prev_month.year}",
            f"{month_names[current_date.month]} {prev_year.year}",
            f"{month_names[current_date.month]} {five_years_ago.year}",
        ]

    def _format_delta_column_names(self, current_month: str) -> Dict[str, str]:
        """Format delta column names based on current month.

        Args:
            current_month: Current month in YYYY-MM format

        Returns:
            Dictionary mapping internal names to display names
        """
        from datetime import datetime

        current_date = datetime.strptime(current_month, "%Y-%m")

        # Previous month
        if current_date.month == 1:
            prev_month = current_date.replace(year=current_date.year - 1, month=12)
        else:
            prev_month = current_date.replace(month=current_date.month - 1)

        # Previous year (same month)
        prev_year = current_date.replace(year=current_date.year - 1)

        # Five years ago (same month)
        five_years_ago = current_date.replace(year=current_date.year - 5)

        return {
            "Δ vs Previous Month": f"Δ vs {prev_month.strftime('%b %Y')}",
            "Δ vs Previous Year": f"Δ vs {prev_year.strftime('%b %Y')}",
            "Δ vs 5 Years Ago": f"Δ vs {five_years_ago.strftime('%b %Y')}",
        }

    def _calculate_deltas(
        self, df: pd.DataFrame, table_name: str, current_month: str
    ) -> pd.DataFrame:
        """Calculate delta columns for rank changes using vectorized operations.

        Args:
            df: DataFrame with current data
            table_name: Name of the table being processed
            current_month: Current month in YYYY-MM format

        Returns:
            DataFrame with delta columns added
        """
        if not self.comparison_data:
            # No comparison data available
            df = df.copy()
            df["Δ vs Previous Month"] = "n/a"
            df["Δ vs Previous Year"] = "n/a"
            df["Δ vs 5 Years Ago"] = "n/a"
            return df

        comparison_periods = self._get_comparison_periods(current_month)
        df = df.copy()

        # Initialize delta columns with proper names
        df["Δ vs Previous Month"] = "n/a"
        df["Δ vs Previous Year"] = "n/a"
        df["Δ vs 5 Years Ago"] = "n/a"

        # Get identifier columns for matching
        string_columns = self._get_string_columns(df.columns, table_name)
        if not string_columns:
            return df

        # Calculate deltas for each comparison period
        for i, period in enumerate(comparison_periods):
            if period not in self.comparison_data:
                continue

            # Get the data part of the (metadata, data) tuple
            period_data = self.comparison_data[period][1]
            if table_name not in period_data:
                continue

            # Get comparison data for this table
            comparison_df = pd.DataFrame(period_data[table_name])
            if comparison_df.empty:
                continue

            # Use vectorized operations for matching
            # Find the best matching column between current and comparison data
            matching_column = None
            for col in string_columns:
                if col in df.columns and col in comparison_df.columns:
                    matching_column = col
                    break

            if not matching_column:
                continue

            # Create a mapping from identifier to rank for fast lookup
            rank_mapping = comparison_df.set_index(matching_column)["rank"].to_dict()

            # Vectorized delta calculation
            def calculate_delta(identifier, current_rank):
                if identifier not in rank_mapping:
                    return "n/a"

                comparison_rank = rank_mapping[identifier]
                if current_rank == comparison_rank:
                    return "="
                elif current_rank < comparison_rank:
                    return f"↑{comparison_rank - current_rank}"
                else:
                    return f"↓{current_rank - comparison_rank}"

            # Apply vectorized function
            deltas = df.apply(
                lambda row: calculate_delta(row[matching_column], row["rank"]), axis=1
            )

            # Set delta values in appropriate column
            if i == 0:  # Previous month
                df["Δ vs Previous Month"] = deltas
            elif i == 1:  # Previous year
                df["Δ vs Previous Year"] = deltas
            elif i == 2:  # 5 years ago
                df["Δ vs 5 Years Ago"] = deltas

        return df

    def _get_string_columns(self, columns: list, table_name: str = None) -> list[str]:
        """Get columns suitable for user/entity matching using dynamic field discovery.

        Args:
            columns: List of available columns in the DataFrame
            table_name: Optional table name for aggregator-specific field discovery

        Returns:
            List of column names that are suitable for user/entity matching
        """

        # Try to discover field metadata from aggregator classes
        if table_name:
            aggregator_class = self._get_aggregator_class(table_name)
            if aggregator_class and hasattr(aggregator_class, "IDENTIFIER_FIELDS"):
                # Use aggregator's own field classification
                return [col for col in columns if col in aggregator_class.IDENTIFIER_FIELDS]

        # Fallback to dynamic classification for unknown tables
        return self._fallback_field_classification(columns)

    def _get_aggregator_class(self, table_name: str):
        """Get the aggregator class for a given table name."""
        try:
            # Convert table name to module path
            # e.g., "user_razor_diversity" -> "sotd.aggregate.aggregators.users.razor_diversity_aggregator.RazorDiversityAggregator"
            module_name = f"sotd.aggregate.aggregators.users.{table_name}_aggregator"
            class_name = f"{table_name.replace('_', ' ').title().replace(' ', '')}Aggregator"

            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError):
            # Return None if aggregator class can't be found
            return None

    def _fallback_field_classification(self, columns: list) -> list[str]:
        """Fallback field classification for tables without explicit metadata."""

        def is_identifier_column(col: str) -> bool:
            """Dynamically classify whether a column is suitable for user/entity matching."""

            # Exclude columns that are clearly not identifiers
            if col.startswith("avg_"):  # All average fields (avg_shaves_per_*)
                return False
            if col.startswith("unique_"):  # All unique count fields (unique_*)
                return False
            if col in ["rank", "shaves", "missed_days", "missed_dates"]:  # Known non-identifiers
                return False
            if col.startswith("Δ"):  # Delta columns
                return False
            if col in ["date", "timestamp"]:  # Date/time fields
                return False

            # Include columns that are likely identifiers
            if col in ["user", "author", "brand", "name", "model", "maker"]:
                return True

            # Default: include if it looks like a string identifier
            # This handles future fields we haven't explicitly classified
            return True

        return [col for col in columns if is_identifier_column(col)]

    def _parse_columns_parameter(self, columns_spec: str) -> tuple[list[str], dict[str, str]]:
        """Parse the columns parameter specification.

        Args:
            columns_spec: String like "rank, name=soap, shaves, unique_users"

        Returns:
            Tuple of (column_order, rename_mapping)

        Raises:
            ValueError: If syntax is invalid
        """
        if not columns_spec.strip():
            raise ValueError("Columns parameter cannot be empty")

        column_order = []
        rename_mapping = {}

        for part in columns_spec.split(","):
            part = part.strip()
            if not part:
                continue

            if "=" in part:
                # Handle renaming: "name=soap"
                if part.count("=") != 1:
                    raise ValueError(f"Invalid rename syntax: {part}")
                original, alias = part.split("=", 1)
                original = original.strip()
                alias = alias.strip()

                if not original or not alias:
                    raise ValueError(f"Invalid rename syntax: {part}")

                column_order.append(original)
                rename_mapping[original] = alias
            else:
                # Simple column name
                column_order.append(part)

        if not column_order:
            raise ValueError("No valid columns specified")

        return column_order, rename_mapping

    def _apply_column_operations(
        self, df: pd.DataFrame, columns_spec: Optional[str] = None
    ) -> pd.DataFrame:
        """Apply column reordering and renaming operations.

        Args:
            df: DataFrame to modify
            columns_spec: Optional columns specification string

        Returns:
            Modified DataFrame
        """
        if not columns_spec:
            return df

        try:
            column_order, rename_mapping = self._parse_columns_parameter(columns_spec)
        except ValueError as e:
            raise ValueError(f"Invalid columns parameter: {e}")

        # Validate that specified columns exist
        missing_columns = [col for col in column_order if col not in df.columns]
        if missing_columns:
            # Silently omit missing columns as per requirements
            column_order = [col for col in column_order if col in df.columns]
            if not column_order:
                raise ValueError("No valid columns found in data")

        # Identify delta columns (they should always be preserved at the end)
        delta_columns = [col for col in df.columns if col.startswith("Δ")]

        # Reorder specified columns, then add delta columns at the end
        final_columns = column_order + delta_columns
        df = df[final_columns].copy()

        if rename_mapping:
            df = df.rename(columns=rename_mapping)

        return df

    def _apply_numeric_limits(self, df: pd.DataFrame, numeric_limits: dict) -> pd.DataFrame:
        """Apply numeric column limits to the DataFrame.

        Args:
            df: DataFrame to limit
            numeric_limits: Dictionary of column_name: threshold pairs (should contain only one limit)

        Returns:
            Limited DataFrame

        Raises:
            ValueError: If multiple limits specified, column doesn't exist, threshold is invalid, or limits create gaps
        """
        # Only allow one numeric column limit per table
        if len(numeric_limits) > 1:
            limit_names = list(numeric_limits.keys())
            raise ValueError(
                f"Only one numeric column limit allowed per table, got: {', '.join(limit_names)}"
            )

        limited_df = df.copy()

        for column_name, threshold in numeric_limits.items():
            # Validate column exists
            if column_name not in limited_df.columns:
                raise ValueError(f"Column '{column_name}' not found in table data")

            # Validate threshold is numeric
            try:
                numeric_threshold = float(threshold)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid threshold value '{threshold}' for column '{column_name}' - must be numeric"
                )

            # Apply limit (>= threshold) - cut from bottom
            limited_df = limited_df[limited_df[column_name] >= numeric_threshold]

        # Check for gaps in the rank column specifically
        # If we have a rank column, check if filtering created gaps in the rank sequence
        if "rank" in limited_df.columns and not limited_df.empty:
            # Get the ranks in order
            ranks = sorted(limited_df["rank"].tolist())

            # Check if there are gaps in the rank sequence
            # For example: [1, 2, 4, 5] has a gap (missing 3)
            if len(ranks) > 1:
                expected_ranks = list(range(ranks[0], ranks[-1] + 1))
                if ranks != expected_ranks:
                    raise ValueError(
                        "Numeric column limits created gaps in table data - limits may be too aggressive"
                    )

        return limited_df

    def generate_table(
        self,
        table_name: str,
        ranks: Optional[int] = None,
        rows: Optional[int] = None,
        columns: Optional[str] = None,
        deltas: bool = False,
        **numeric_limits,
    ) -> str:
        """Generate a markdown table by table name.

        Args:
            table_name: Name of the table (e.g., 'soap-makers', 'razors')
            ranks: Maximum rank to include (inclusive with ties)
            rows: Maximum number of rows to include
            columns: Optional column specification (e.g., "rank, name=soap, shaves")
            deltas: Whether to include delta calculations
            **numeric_limits: Single numeric column limit (e.g., shaves=50)

        Returns:
            Markdown table string

        Raises:
            ValueError: If table name is not recognized, parameters are invalid,
                      rank column is missing, columns parameter is invalid,
                      or numeric limits create gaps in data
        """
        # Validate parameters
        if ranks is not None and ranks <= 0:
            raise ValueError("ranks must be greater than 0")
        if rows is not None and rows <= 0:
            raise ValueError("rows must be greater than 0")

        # Convert kebab-case template name to snake_case data key
        data_key = table_name.replace("-", "_")

        if data_key not in self.data:
            available_keys = list(self.data.keys())
            raise ValueError(
                f"Unknown table: {table_name} (converted to '{data_key}'). "
                f"Available keys: {available_keys}"
            )

        table_data = self.data[data_key]

        # Convert data to DataFrame first
        df = pd.DataFrame(table_data)

        if df.empty:
            return ""

        # Validate that rank column exists
        if "rank" not in df.columns:
            raise ValueError(f"Data for {table_name} is missing 'rank' column")

        # Apply ranks filter if specified
        if ranks is not None:
            df = df[df["rank"] <= ranks]

        # Apply rows limit if specified
        if rows is not None:
            df = df.head(rows)

        # Apply numeric column limits if specified
        if numeric_limits:
            df = self._apply_numeric_limits(df, numeric_limits)

        # Add delta columns if requested (BEFORE rank formatting so numeric ranks are available)
        if deltas:
            # Determine current month from data (this is a simplified approach)
            # In practice, this should come from the report context
            current_month = self.current_month or "2025-06"  # TODO: Make this configurable

            # Use the data key (with underscore) for delta calculation, not the table name (with hyphen)
            data_key = table_name.replace("-", "_")
            df = self._calculate_deltas(df, data_key, current_month)

            # Format delta column names
            delta_name_mapping = self._format_delta_column_names(current_month)
            df = df.rename(columns=delta_name_mapping)

        # Apply rank formatting AFTER delta calculation (so deltas use numeric ranks)
        if "rank" in df.columns and df["rank"].duplicated().any():
            df = self._format_rank_column(df)

        # Apply column operations AFTER delta calculation (so rank column is available for deltas)
        if columns:
            df = self._apply_column_operations(df, columns)

        # Convert to markdown
        result = df.to_markdown(index=False)

        # Format column names to Title Case with acronym preservation as the very last step
        # This ensures all operations (including delta calculation) work with original column names
        if result and result != "":
            # Parse the markdown back to DataFrame for column formatting
            from io import StringIO

            formatted_df = pd.read_csv(StringIO(result), sep="|", skipinitialspace=True)
            formatted_df = formatted_df.iloc[
                :, 1:-1
            ]  # Remove empty first/last columns from markdown parsing

            # Format usernames with "u/" prefix for Reddit display
            formatted_df = self._format_usernames(formatted_df)

            # Format column names
            formatted_df = self._format_column_names(formatted_df)

            # Convert back to markdown
            result = formatted_df.to_markdown(index=False)

        return result if result is not None else ""

    def get_available_table_names(self) -> List[str]:
        """Get list of available table names.

        Returns:
            List of available table names
        """
        # Return all available data keys (these are the table names)
        return list(self.data.keys())

    def generate_table_by_name(self, table_name: str) -> str:
        """Generate a table by its placeholder name (backward compatibility).

        Args:
            table_name: Name of the table (e.g., 'razors', 'blades')

        Returns:
            Generated table content as markdown string

        Raises:
            ValueError: If table name is not recognized or parameters are invalid
        """
        return self.generate_table(table_name)
