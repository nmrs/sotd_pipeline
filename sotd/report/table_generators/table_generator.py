"""Universal table generator for report templates."""

import json
import logging
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from sotd.utils.wsdb_lookup import WSDBLookup

logger = logging.getLogger(__name__)


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
        self._wsdb_soaps: List[Dict[str, Any]] | None = None
        self._wsdb_lookup: WSDBLookup | None = None

        # No more hardcoded mappings - we'll convert kebab-case to snake_case dynamically

    def _load_wsdb_data(self) -> List[Dict[str, Any]]:
        """Lazily load WSDB soap data from software.json.

        Returns:
            List of WSDB soap entries (filtered for type="Soap")
        """
        if self._wsdb_soaps is not None:
            return self._wsdb_soaps

        # Try to find the project root (go up from this file to find data/wsdb)
        current_file = Path(__file__)
        # This file is at: sotd/report/table_generators/table_generator.py
        # Project root is 3 levels up
        project_root = current_file.parent.parent.parent.parent
        wsdb_file = project_root / "data" / "wsdb" / "software.json"

        if not wsdb_file.exists():
            if self.debug:
                logger.debug(f"WSDB file not found at {wsdb_file}, skipping link generation")
            self._wsdb_soaps = []
            return []

        try:
            with wsdb_file.open("r", encoding="utf-8") as f:
                all_software = json.load(f)

            # Filter for soaps only
            soaps = [item for item in all_software if item.get("type") == "Soap"]
            self._wsdb_soaps = soaps

            if self.debug:
                logger.debug(f"Loaded {len(soaps)} soaps from WSDB")

            return soaps
        except Exception as e:
            if self.debug:
                logger.debug(f"Failed to load WSDB data: {e}, skipping link generation")
            self._wsdb_soaps = []
            return []

    def _normalize_string(self, text: str) -> str:
        """Normalize a string to Unicode NFC (Normalization Form Canonical Composed).

        This ensures that visually identical characters are treated the same regardless
        of their Unicode encoding.

        Args:
            text: The string to normalize

        Returns:
            The normalized string in NFC form
        """
        if not text:
            return text
        return unicodedata.normalize("NFC", text)

    def _get_wsdb_lookup(self) -> WSDBLookup:
        """Get or create WSDB lookup utility instance.

        Returns:
            WSDBLookup instance
        """
        if self._wsdb_lookup is None:
            # Find project root (same logic as _load_wsdb_data)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            self._wsdb_lookup = WSDBLookup(project_root=project_root)
        return self._wsdb_lookup

    def _get_wsdb_slug(self, brand: str, scent: str) -> str | None:
        """Lookup WSDB slug for a given brand and scent, respecting aliases.

        Uses case-insensitive matching with Unicode normalization for consistency.
        Checks aliases from soaps.yaml for both brand and scent.

        Args:
            brand: Brand name to match
            scent: Scent name to match

        Returns:
            WSDB slug if found, None otherwise
        """
        lookup = self._get_wsdb_lookup()
        return lookup.get_wsdb_slug(brand, scent)

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

        # OPTIMIZED: Use pandas Series operations for vectorized text processing
        if not text:
            return text

        # Convert to pandas Series for vectorized operations
        words = pd.Series(text.split())

        # Create mask for acronyms and apply vectorized operations
        acronym_mask = words.str.lower().isin(acronyms)
        per_mask = words.str.lower() == "per"

        # Apply formatting using vectorized operations
        # Ensure we're working with Series for type checking
        formatted_words: pd.Series = words.copy()  # type: ignore
        acronym_words: pd.Series = words[acronym_mask]  # type: ignore
        per_words: pd.Series = words[per_mask]  # type: ignore
        formatted_words[acronym_mask] = acronym_words.str.upper()
        formatted_words[per_mask] = per_words.str.lower()

        # Apply title case to remaining words
        other_mask = ~(acronym_mask | per_mask)
        other_words: pd.Series = words[other_mask]  # type: ignore
        formatted_words[other_mask] = other_words.str.title()

        return " ".join(formatted_words)

    def _format_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format column names to Title Case with acronym preservation.

        Args:
            df: DataFrame to format

        Returns:
            DataFrame with formatted column names
        """
        formatted_df = df.copy()

        # OPTIMIZED: Use pandas operations for vectorized column name formatting
        # Get columns that need formatting (exclude delta columns)
        columns_to_format = [col for col in formatted_df.columns if not col.startswith("Δ")]

        if columns_to_format:
            # Create mapping of old names to new formatted names
            rename_mapping = {}
            for col in columns_to_format:
                formatted_name = self._preserve_acronyms(col.replace("_", " ").title())
                rename_mapping[col] = formatted_name

            # Apply all renames at once using pandas operations
            formatted_df = formatted_df.rename(columns=rename_mapping)

        return formatted_df

    def _format_usernames(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format usernames with "u/" prefix for Reddit display.

        Args:
            df: DataFrame to format

        Returns:
            DataFrame with formatted usernames
        """
        formatted_df = df.copy()

        # OPTIMIZED: Use pandas operations for vectorized username formatting
        # Check if this table has user-related columns
        user_columns = [col for col in formatted_df.columns if col.lower() in ["user", "author"]]

        # Apply vectorized operations to all user columns at once
        for col in user_columns:
            if col in formatted_df.columns:
                # Use pandas string operations for vectorized prefix addition
                mask = (formatted_df[col].notna()) & (
                    ~formatted_df[col].astype(str).str.startswith("u/")
                )
                formatted_df.loc[mask, col] = "u/" + formatted_df.loc[mask, col].astype(str)

        return formatted_df

    def _format_soap_links(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Format soap names with WSDB links when slug is found.

        Only applies to "soaps" table. Wraps soap names in markdown links
        when a matching WSDB slug is found.

        Args:
            df: DataFrame to format
            table_name: Name of the table being generated

        Returns:
            DataFrame with formatted soap names (with links when available)
        """
        # Only apply to soaps table
        if table_name != "soaps":
            return df

        # Check if required columns exist
        if "name" not in df.columns or "brand" not in df.columns or "scent" not in df.columns:
            return df

        formatted_df = df.copy()

        # Apply vectorized operations to add links
        def add_link(row: pd.Series) -> str:
            """Add markdown link to soap name if slug is found."""
            name = str(row.get("name", ""))
            brand = str(row.get("brand", ""))
            scent = str(row.get("scent", ""))

            slug = self._get_wsdb_slug(brand, scent)
            if slug:
                return f"[{name}](https://www.wetshavingdatabase.com/software/{slug}/)"
            return name

        # Apply link formatting to name column
        formatted_df["name"] = formatted_df.apply(add_link, axis=1)

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

        # OPTIMIZED: Use pandas operations for vectorized rank formatting
        # Count occurrences of each rank
        rank_counts = df["rank"].value_counts()

        # Create vectorized formatting using pandas operations
        # Use numpy.where for vectorized conditional formatting
        import numpy as np

        # Format ranks: add = for equal ranks, space for single ranks
        df["rank"] = np.where(
            rank_counts[df["rank"]].values > 1,  # type: ignore
            df["rank"].astype(str) + "=",
            df["rank"].astype(str) + " ",
        )

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

        # Return periods in YYYY-MM format to match comparison data keys
        return [
            prev_month.strftime("%Y-%m"),
            prev_year.strftime("%Y-%m"),
            five_years_ago.strftime("%Y-%m"),
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
        string_columns = self._get_string_columns(list(df.columns), table_name)
        if not string_columns:
            return df

        # Calculate deltas for each comparison period
        for i, period in enumerate(comparison_periods):
            if period not in self.comparison_data:
                continue

            # Get the comparison data for this period
            # Handle both tuple format (metadata, data) and direct data format
            period_data = self.comparison_data[period]
            if isinstance(period_data, tuple) and len(period_data) >= 2:
                # Tuple format: (metadata, data)
                # Type ignore for tuple indexing - we've verified length >= 2
                period_data = period_data[1]  # type: ignore

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

    def _get_string_columns(self, columns: list, table_name: Optional[str] = None) -> list[str]:
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
            # e.g., "user_razor_diversity" ->
            # "sotd.aggregate.aggregators.users.razor_diversity_aggregator.RazorDiversityAggregator"
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

        # Get all identifier columns
        identifier_columns = [col for col in columns if is_identifier_column(col)]

        # Prioritize 'name' column for product tables (soaps, razors, brushes, etc.)
        # since it's the unique identifier, not brand_normalized
        if "name" in identifier_columns:
            # Move 'name' to the front of the list
            identifier_columns.remove("name")
            identifier_columns.insert(0, "name")

        return identifier_columns

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

        # OPTIMIZED: Use pandas operations for vectorized parsing
        # Split and clean parts using pandas operations
        parts = pd.Series(columns_spec.split(",")).str.strip()
        parts = parts[parts != ""]  # Remove empty parts

        # Process parts using vectorized operations where possible
        for part in parts:
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
        # Ensure result is DataFrame, not Series (if only one column selected)
        selected_df = df[final_columns]
        if isinstance(selected_df, pd.Series):
            df = selected_df.to_frame().T
        else:
            df = selected_df.copy()

        if rename_mapping:
            df = df.rename(columns=rename_mapping)

        return df

    def _apply_numeric_limits(self, df: pd.DataFrame, numeric_limits: dict) -> pd.DataFrame:
        """Apply numeric column limits to the DataFrame.

        Args:
            df: DataFrame to limit
            numeric_limits: Dictionary of column_name: threshold pairs
                (should contain only one limit)

        Returns:
            Limited DataFrame

        Raises:
            ValueError: If multiple limits specified, column doesn't exist, or threshold is invalid
        """
        # Only allow one numeric column limit per table
        if len(numeric_limits) > 1:
            limit_names = list(numeric_limits.keys())
            raise ValueError(
                f"Only one numeric column limit allowed per table, got: {', '.join(limit_names)}"
            )

        limited_df = df.copy()

        # OPTIMIZED: Use pandas operations for vectorized numeric limit application
        # Since only one limit is allowed, we can process it directly
        column_name, threshold = next(iter(numeric_limits.items()))

        # Validate column exists
        if column_name not in limited_df.columns:
            raise ValueError(f"Column '{column_name}' not found in table data")

        # Validate threshold is numeric
        try:
            numeric_threshold = float(threshold)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid threshold value '{threshold}' for column "
                f"'{column_name}' - must be numeric"
            )

        # Apply limit (>= threshold) - cut from bottom using pandas boolean indexing
        # Ensure result is DataFrame, not Series
        filtered_df = limited_df[limited_df[column_name] >= numeric_threshold]
        if isinstance(filtered_df, pd.Series):
            limited_df = filtered_df.to_frame().T
        else:
            limited_df = filtered_df

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

        # Handle both flat and nested data structures
        if data_key in self.data:
            table_data = self.data[data_key]
        elif "data" in self.data and data_key in self.data["data"]:
            table_data = self.data["data"][data_key]
        else:
            available_keys = list(self.data.keys())
            if "data" in self.data:
                available_keys.extend([f"data.{k}" for k in self.data["data"].keys()])
            raise ValueError(
                f"Unknown table: {table_name} (converted to '{data_key}'). "
                f"Available keys: {available_keys}"
            )

        # Convert data to DataFrame first
        df = pd.DataFrame(table_data)

        if df.empty:
            return ""

        # Validate that rank column exists only when needed
        rank_required = ranks is not None or deltas or columns is not None

        if rank_required and "rank" not in df.columns:
            raise ValueError(f"Data for {table_name} is missing 'rank' column")

        # Apply ranks filter if specified
        if ranks is not None:
            df = df[df["rank"] <= ranks]

        # Apply rows limit if specified
        if rows is not None:
            # Implement tie-aware row limiting
            if "rank" in df.columns:
                # Sort by rank first to ensure proper ordering
                # Type ignore for sort_values - pandas supports string key parameter
                sorted_df = df.sort_values("rank")  # type: ignore
                df = sorted_df if isinstance(sorted_df, pd.DataFrame) else df

                # Find the rank at the row limit boundary
                if len(df) > rows:
                    # Get the rank at position 'rows' (0-indexed)
                    boundary_rank = df.iloc[rows - 1]["rank"]

                    # Include all items with the same rank as the boundary
                    # This ensures ties are respected
                    filtered_df = df[df["rank"] <= boundary_rank]
                    df = filtered_df if isinstance(filtered_df, pd.DataFrame) else df
            else:
                # No rank column, use simple head
                head_df = df.head(rows)
                df = head_df if isinstance(head_df, pd.DataFrame) else df

        # Ensure df is DataFrame for type checking
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Expected DataFrame but got other type")

        # Apply numeric column limits if specified
        if numeric_limits:
            limited_df = self._apply_numeric_limits(df, numeric_limits)
            if isinstance(limited_df, pd.DataFrame):
                df = limited_df

        # Add delta columns if requested (BEFORE rank formatting so numeric ranks are available)
        if deltas:
            # Determine current month from data (this is a simplified approach)
            # In practice, this should come from the report context
            current_month = self.current_month or "2025-06"  # TODO: Make this configurable

            # Use the data key (with underscore) for delta calculation,
            # not the table name (with hyphen)
            data_key = table_name.replace("-", "_")
            delta_df = self._calculate_deltas(df, data_key, current_month)
            if isinstance(delta_df, pd.DataFrame):
                df = delta_df

            # Format delta column names
            delta_name_mapping = self._format_delta_column_names(current_month)
            # Type ignore for rename - pandas supports columns parameter
            df = df.rename(columns=delta_name_mapping)  # type: ignore

        # Apply rank formatting AFTER delta calculation (so deltas use numeric ranks)
        if "rank" in df.columns:
            rank_series: pd.Series = df["rank"]  # type: ignore
            if rank_series.duplicated().any():
                formatted_df = self._format_rank_column(df)
                if isinstance(formatted_df, pd.DataFrame):
                    df = formatted_df

        # Apply column operations AFTER delta calculation (so rank column is available for deltas)
        if columns:
            column_df = self._apply_column_operations(df, columns)
            if isinstance(column_df, pd.DataFrame):
                df = column_df

        # Format soap names with WSDB links (only for soaps table)
        # Do this BEFORE column name formatting so we can access columns by their original names
        df = self._format_soap_links(df, table_name)

        # Format column names to Title Case with acronym preservation BEFORE converting to markdown
        # This ensures clean column names in the final output
        formatted_df = self._format_column_names(df)
        if isinstance(formatted_df, pd.DataFrame):
            df = formatted_df

        # Format usernames with "u/" prefix for Reddit display
        df = self._format_usernames(df)

        # Convert to markdown
        result = df.to_markdown(index=False)

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
