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
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize the table generator.

        Args:
            data: Dictionary containing aggregated data with keys like 'soap_makers',
                  'razors', etc.
            comparison_data: Historical data for delta calculations (not yet supported
                           in new system)
            debug: Enable debug logging (not yet supported in new system)
        """
        # Extract data section if full structure is passed (meta + data)
        if "meta" in data and "data" in data:
            self.data = data["data"]
        else:
            self.data = data

        # Store comparison data for future delta support (not yet implemented)
        self.comparison_data = comparison_data or {}
        self.debug = debug

        # Map template names to data keys (convert hyphens to underscores)
        self.table_mappings = {
            # Hardware tables
            "razors": "razors",
            "razor-manufacturers": "razor_manufacturers",
            "razor-formats": "razor_formats",
            "blades": "blades",
            "blade-manufacturers": "blade_manufacturers",
            "blade-usage-distribution": "blade_usage_distribution",
            "brushes": "brushes",
            "brush-handle-makers": "brush_handle_makers",
            "brush-knot-makers": "brush_knot_makers",
            "knot-fibers": "brush_fibers",
            "knot-sizes": "brush_knot_sizes",
            # Specialized tables
            "blackbird-plates": "blackbird_plates",
            "christopher-bradley-plates": "christopher_bradley_plates",
            "game-changer-plates": "game_changer_plates",
            "super-speed-tips": "super_speed_tips",
            "straight-widths": "straight_widths",
            "straight-grinds": "straight_grinds",
            "straight-points": "straight_points",
            # Cross-product tables
            "razor-blade-combinations": "razor_blade_combinations",
            "highest-use-count-per-blade": "highest_use_count_per_blade",
            # User tables
            "top-shavers": "users",
            # Software tables
            "soap-makers": "soap_makers",
            "soap-brands": "soap_brands",
            "soaps": "soaps",
            "top-sampled-soaps": "top_sampled_soaps",
            "brand-diversity": "brand_diversity",
        }

    def _format_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format column names to Title Case while preserving acronyms.
        
        Args:
            df: DataFrame with original column names
            
        Returns:
            DataFrame with formatted column names
        """
        # Define common acronyms that should stay uppercase
        acronyms = {
            'de', 'ac', 'oc', 'sb', 'aa', 'b', 'c', 'd', 'f',  # Razor formats
            'mm', 'ptfe', 'gem', 'weck', 'valet', 'rolls',  # Brand/model acronyms
            'oc', 'lite', 'standard', 'sb', 'aa', 'b', 'c', 'd', 'f'  # Plate types
        }
        
        formatted_columns = {}
        for col in df.columns:
            if col.lower() in acronyms:
                # Preserve acronyms in uppercase
                formatted_columns[col] = col.upper()
            else:
                # Convert snake_case to Title Case
                formatted_col = col.replace('_', ' ').title()
                formatted_columns[col] = formatted_col
        
        # Rename columns
        df = df.rename(columns=formatted_columns)
        return df

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
        
        for part in columns_spec.split(','):
            part = part.strip()
            if not part:
                continue
                
            if '=' in part:
                # Handle renaming: "name=soap"
                if part.count('=') != 1:
                    raise ValueError(f"Invalid rename syntax: {part}")
                original, alias = part.split('=', 1)
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

    def _apply_column_operations(self, df: pd.DataFrame, columns_spec: Optional[str] = None) -> pd.DataFrame:
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
        
        # Reorder and rename columns
        df = df[column_order].copy()
        if rename_mapping:
            df = df.rename(columns=rename_mapping)
            
        return df

    def generate_table(
        self, 
        table_name: str, 
        ranks: Optional[int] = None, 
        rows: Optional[int] = None,
        columns: Optional[str] = None
    ) -> str:
        """Generate a markdown table by table name.

        Args:
            table_name: Name of the table (e.g., 'soap-makers', 'razors')
            ranks: Maximum rank to include (inclusive with ties)
            rows: Maximum number of rows to include
            columns: Optional column specification (e.g., "rank, name=soap, shaves")

        Returns:
            Markdown table string

        Raises:
            ValueError: If table name is not recognized, parameters are invalid,
                      rank column is missing, or columns parameter is invalid
        """
        if table_name not in self.table_mappings:
            raise ValueError(f"Unknown table name: {table_name}")

        # Validate parameters
        if ranks is not None and ranks <= 0:
            raise ValueError("ranks must be greater than 0")
        if rows is not None and rows <= 0:
            raise ValueError("rows must be greater than 0")

        # Get the data for this table
        aggregator_name = self.table_mappings[table_name]

        if aggregator_name not in self.data:
            return f"*No data available for {table_name}*"

        table_data = self.data[aggregator_name]

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

        # Apply column operations if specified
        if columns:
            df = self._apply_column_operations(df, columns)

        # Format rank column to show equal ranks as N= (only if there are equal ranks)
        if "rank" in df.columns and df["rank"].duplicated().any():
            df = self._format_rank_column(df)

        # Format column names to Title Case with acronym preservation
        df = self._format_column_names(df)

        # Convert to markdown
        result = df.to_markdown(index=False)
        return result if result is not None else ""

    def get_available_table_names(self) -> List[str]:
        """Get list of available table names.

        Returns:
            List of available table names
        """
        return list(self.table_mappings.keys())

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
