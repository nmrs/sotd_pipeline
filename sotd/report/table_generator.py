"""Table generator for report templates."""

from typing import Any, Dict, Optional

from .table_generators.blade_tables import (
    BladeManufacturersTableGenerator,
    BladesTableGenerator,
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
            data: Data from aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
        """
        self.data = data
        self.comparison_data = comparison_data or {}
        self.debug = debug

        # Map table names to generator classes
        self.table_generators = {
            # Hardware tables
            "razors": RazorsTableGenerator,
            "razor-manufacturers": RazorManufacturersTableGenerator,
            "razor-formats": RazorFormatsTableGenerator,
            "blades": BladesTableGenerator,
            "blade-manufacturers": BladeManufacturersTableGenerator,
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
            "brand-diversity": BrandDiversityTableGenerator,
        }

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

        # Generate the table (without header since template provides section headers)
        if self.comparison_data:
            table_content = generator.generate_table(
                include_delta=include_delta,
                comparison_data=self.comparison_data,
                include_header=False,
            )
        else:
            table_content = generator.generate_table(
                include_delta=include_delta,
                comparison_data=None,
                include_header=False,
            )

        # If the table is empty, return a "No data available" message
        if not table_content:
            return f"*No data available for {table_name}*"

        return table_content

    def get_available_table_names(self) -> list:
        """Get list of available table names.

        Returns:
            List of available table names
        """
        return list(self.table_generators.keys())
