"""Table generator for report templates using the universal table generator."""

from typing import Any, Dict, Optional

from .table_generators.universal import UniversalTableGenerator


class TableGenerator:
    """Generates tables by name for template placeholders using the universal generator.

    This class replaces the complex legacy table generation system with a simple,
    pandas-first universal table generator that supports basic parameter filtering.
    """

    def __init__(
        self,
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize the table generator.

        Args:
            data: Data from aggregated data (can be full structure with meta/data or just data)
            comparison_data: Historical data for delta calculations (not yet supported)
            debug: Enable debug logging
        """
        # Extract data section if full structure is passed (meta + data)
        if "meta" in data and "data" in data:
            self.data = data["data"]
            if debug:
                print("[DEBUG] TableGenerator: Extracted data section from full structure")
        else:
            self.data = data
            if debug:
                print("[DEBUG] TableGenerator: Using data directly (no meta section)")

        # Extract data section from comparison data if it has the full structure
        if comparison_data:
            self.comparison_data = {}
            for period, (metadata, period_data) in comparison_data.items():
                if "meta" in period_data and "data" in period_data:
                    self.comparison_data[period] = (metadata, period_data["data"])
                    if debug:
                        print(f"[DEBUG] TableGenerator: Extracted data section from {period}")
                else:
                    self.comparison_data[period] = (metadata, period_data)
                    if debug:
                        print(f"[DEBUG] TableGenerator: Using {period} data directly")
        else:
            self.comparison_data = {}

        self.debug = debug

        # Map table names to aggregator names in the data
        # These should match the keys in the aggregated data
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
            "top-shavers": "top_shavers",
            # Software tables
            "soap-makers": "soap_makers",
            "soap-brands": "soap_brands",
            "soaps": "soaps",
            "top-sampled-soaps": "top_sampled_soaps",
            "brand-diversity": "brand_diversity",
        }

    def generate_table_by_name(self, table_name: str) -> str:
        """Generate a table by its placeholder name.

        Args:
            table_name: Name of the table (e.g., 'razors', 'blades')

        Returns:
            Generated table content as markdown string

        Raises:
            ValueError: If table name is not recognized or data is not available
        """
        if table_name not in self.table_mappings:
            raise ValueError(f"Unknown table name: {table_name}")

        aggregator_name = self.table_mappings[table_name]

        if aggregator_name not in self.data:
            return f"*No data available for {table_name}*"

        table_data = self.data[aggregator_name]

        if not table_data:
            return f"*No data available for {table_name}*"

        generator = UniversalTableGenerator(table_data, aggregator_name)
        return generator.generate_table()

    def generate_table_with_parameters(self, table_name: str, parameters: Dict[str, Any]) -> str:
        """Generate a table with parameters using the universal generator.

        Args:
            table_name: Name of the table (e.g., 'razors', 'blades')
            parameters: Dictionary of parameters to apply (e.g., {'ranks': 50, 'rows': 30})

        Returns:
            Generated table content as markdown string

        Raises:
            ValueError: If table name is not recognized or parameters are invalid
        """
        if table_name not in self.table_mappings:
            raise ValueError(f"Unknown table name: {table_name}")

        aggregator_name = self.table_mappings[table_name]

        if aggregator_name not in self.data:
            return f"*No data available for {table_name}*"

        table_data = self.data[aggregator_name]

        if not table_data:
            return f"*No data available for {table_name}*"

        # Extract ranks and rows parameters
        ranks = parameters.get("ranks")
        rows = parameters.get("rows")

        generator = UniversalTableGenerator(table_data, aggregator_name)
        return generator.generate_table(ranks=ranks, rows=rows)

    def get_available_table_names(self) -> list:
        """Get list of available table names.

        Returns:
            List of available table names
        """
        return list(self.table_mappings.keys())
