"""Table generator for report templates."""

from typing import Any, Dict, Optional

from .enhanced_table_generator import EnhancedTableGenerator
from .table_generators.blade_tables import (
    BladeManufacturersTableGenerator,
    BladesTableGenerator,
    BladeUsageDistributionTableGenerator,
)
from .table_generators.brush_tables import (
    BrushesTableGenerator,
    BrushFibersTableGenerator,
    BrushHandleMakersTableGenerator,
    BrushKnotMakersTableGenerator,
    BrushKnotSizesTableGenerator,
)
from .table_generators.cross_product_tables import (
    HighestUseCountPerBladeTableGenerator,
    RazorBladeCombinationsTableGenerator,
)
from .table_generators.razor_tables import (
    RazorFormatsTableGenerator,
    RazorManufacturersTableGenerator,
    RazorsTableGenerator,
)
from .table_generators.soap_tables import (
    BrandDiversityTableGenerator,
    SoapMakersTableGenerator,
    SoapsTableGenerator,
    TopSampledSoapsTableGenerator,
)
from .table_generators.specialized_tables import (
    BlackbirdPlatesTableGenerator,
    ChristopherBradleyPlatesTableGenerator,
    GameChangerPlatesTableGenerator,
    StraightGrindsTableGenerator,
    StraightPointsTableGenerator,
    StraightWidthsTableGenerator,
    SuperSpeedTipsTableGenerator,
)
from .table_generators.user_tables import TopShaversTableGenerator


class TableGenerator:
    """Generates tables by name for template placeholders."""

    def __init__(
        self,
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize the table generator.

        Args:
            data: Data from aggregated data (can be full structure with meta/data or just data)
            comparison_data: Historical data for delta calculations
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

        # Map table names to generator classes
        self.table_generators = {
            # Hardware tables
            "razors": RazorsTableGenerator,
            "razor-manufacturers": RazorManufacturersTableGenerator,
            "razor-formats": RazorFormatsTableGenerator,
            "blades": BladesTableGenerator,
            "blade-manufacturers": BladeManufacturersTableGenerator,
            "blade-usage-distribution": BladeUsageDistributionTableGenerator,
            "brushes": BrushesTableGenerator,
            "brush-handle-makers": BrushHandleMakersTableGenerator,
            "brush-knot-makers": BrushKnotMakersTableGenerator,
            "knot-fibers": BrushFibersTableGenerator,
            "knot-sizes": BrushKnotSizesTableGenerator,
            # Specialized tables
            "blackbird-plates": BlackbirdPlatesTableGenerator,
            "christopher-bradley-plates": ChristopherBradleyPlatesTableGenerator,
            "game-changer-plates": GameChangerPlatesTableGenerator,
            "super-speed-tips": SuperSpeedTipsTableGenerator,
            "straight-widths": StraightWidthsTableGenerator,
            "straight-grinds": StraightGrindsTableGenerator,
            "straight-points": StraightPointsTableGenerator,
            # Cross-product tables
            "razor-blade-combinations": RazorBladeCombinationsTableGenerator,
            "highest-use-count-per-blade": HighestUseCountPerBladeTableGenerator,
            # User tables
            "top-shavers": TopShaversTableGenerator,
            # Software tables
            "soap-makers": SoapMakersTableGenerator,
            "soaps": SoapsTableGenerator,
            "top-sampled-soaps": TopSampledSoapsTableGenerator,
            "brand-diversity": BrandDiversityTableGenerator,
        }

        # Initialize enhanced table generator for parameter support
        self.enhanced_table_generator = EnhancedTableGenerator()

    def generate_table_by_name(self, table_name: str) -> str:
        """Generate a table by its placeholder name.

        Args:
            table_name: Name of the table (e.g., 'razors', 'blades')

        Returns:
            Generated table content as markdown string

        Raises:
            ValueError: If table name is not recognized
        """
        if table_name not in self.table_generators:
            raise ValueError(f"Unknown table name: {table_name}")

        generator_class = self.table_generators[table_name]
        generator = generator_class(self.data, self.debug)

        # Check if we have comparison data for delta calculations
        include_delta = bool(self.comparison_data)

        # Check if this table generator supports delta calculations
        # Tables with NoDeltaMixin should not show delta columns
        if include_delta and hasattr(generator, "generate_table"):
            # Check if the generator is a NoDeltaMixin by looking at its MRO
            from .table_generators.base import NoDeltaMixin

            if NoDeltaMixin in type(generator).__mro__:
                include_delta = False

        # For enhanced templating, let the enhanced system handle all limits
        # Only apply default limits for basic table generation
        if hasattr(generator, "should_limit_rows") and not generator.should_limit_rows():
            max_rows = 10000  # Effectively unlimited
        else:
            max_rows = 10000  # Effectively unlimited for enhanced templating

        # Generate the table (without header since template provides section headers)
        if self.comparison_data:
            table_content = generator.generate_table(
                max_rows=max_rows,
                include_delta=include_delta,
                comparison_data=self.comparison_data,
                include_header=False,
            )
        else:
            table_content = generator.generate_table(
                max_rows=max_rows,
                include_delta=include_delta,
                comparison_data=None,
                include_header=False,
            )

        # If the table is empty, return a "No data available" message
        if not table_content:
            return f"*No data available for {table_name}*"

        return table_content

    def generate_table_with_parameters(self, table_name: str, parameters: Dict[str, Any]) -> str:
        """Generate a table with enhanced parameters using the EnhancedTableGenerator.

        Args:
            table_name: Name of the table (e.g., 'razors', 'blades')
            parameters: Dictionary of parameters to apply (e.g., {'shaves': 5, 'rows': 20})

        Returns:
            Generated table content as markdown string

        Raises:
            ValueError: If table name is not recognized or parameters are invalid
        """
        if table_name not in self.table_generators:
            raise ValueError(f"Unknown table name: {table_name}")

        # Get the raw table data from the generator
        generator_class = self.table_generators[table_name]
        generator = generator_class(self.data, self.debug)

        # Get the raw table data (before any formatting or row limiting)
        raw_data = generator.get_table_data()

        if not raw_data:
            return f"*No data available for {table_name}*"

        # Apply enhanced parameters using the EnhancedTableGenerator
        processed_data = self.enhanced_table_generator.generate_table(
            table_name, raw_data, parameters
        )

        if not processed_data:
            return f"*No data available for {table_name} with specified parameters*"

        # Now generate the formatted table using the original generator
        # but with the processed data
        # We need to temporarily replace the generator's data to use our processed version

        # Store original data
        original_data = generator.data

        # Create a temporary data structure that preserves the original structure
        # The generator expects data in the same format as the original
        temp_data = {}

        # Copy all original data keys
        for key in original_data:
            temp_data[key] = original_data[key]

        # Find the key that the table generator actually uses for its data
        # by checking what get_table_data() accesses
        if hasattr(generator, "get_table_data"):
            # Map table names to their expected data keys
            table_data_key_mapping = {
                "top-shavers": "users",
                "razors": "razors",
                "blades": "blades",
                "brushes": "brushes",
                "soaps": "soaps",
                "razor-blade-combinations": "razor_blade_combinations",
                "highest-use-count-per-blade": "highest_use_count_per_blade",
                "razor-manufacturers": "razor_manufacturers",
                "razor-formats": "razor_formats",
                "blade-manufacturers": "blade_manufacturers",
                "blade-usage-distribution": "blade_usage_distribution",
                "brush-handle-makers": "brush_handle_makers",
                "brush-knot-makers": "brush_knot_makers",
                "knot-fibers": "knot_fibers",
                "knot-sizes": "knot_sizes",
                "soap-makers": "soap_makers",
                "top-sampled-soaps": "top_sampled_soaps",
                "brand-diversity": "brand_diversity",
            }

            # Get the correct data key for this table
            data_key = table_data_key_mapping.get(table_name, table_name)
            temp_data[data_key] = processed_data

        # Temporarily replace the generator's data
        generator.data = temp_data

        try:
            # Generate the table with the processed data
            # Use a high max_rows since we've already applied our own limits
            # Check if we have comparison data for delta calculations
            include_delta = bool(self.comparison_data)

            # Check if this table generator supports delta calculations
            # Tables with NoDeltaMixin should not show delta columns
            if include_delta and hasattr(generator, "generate_table"):
                # Check if the generator is a NoDeltaMixin by looking at its MRO
                from .table_generators.base import NoDeltaMixin

                if NoDeltaMixin in type(generator).__mro__:
                    include_delta = False

            table_content = generator.generate_table(
                max_rows=len(processed_data),
                include_delta=include_delta,
                comparison_data=self.comparison_data,
                include_header=False,
            )
        finally:
            # Restore original data
            generator.data = original_data

        # If the table is empty, return a "No data available" message
        if not table_content:
            return f"*No data available for {table_name} with specified parameters*"

        return table_content

    def get_available_table_names(self) -> list:
        """Get list of available table names.

        Returns:
            List of available table names
        """
        return list(self.table_generators.keys())
