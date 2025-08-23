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

    def generate_table(
        self, table_name: str, ranks: Optional[int] = None, rows: Optional[int] = None
    ) -> str:
        """Generate a markdown table by table name.

        Args:
            table_name: Name of the table (e.g., 'soap-makers', 'razors')
            ranks: Maximum rank to include (inclusive with ties)
            rows: Maximum number of rows to include

        Returns:
            Markdown table string

        Raises:
            ValueError: If table name is not recognized, parameters are invalid,
                      or rank column is missing
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
