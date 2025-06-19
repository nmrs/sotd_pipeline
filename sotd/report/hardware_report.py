"""Hardware report generator for the SOTD pipeline report phase."""

from typing import Any, Dict, List, Optional

from .base import BaseReportGenerator
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
from .table_generators.razor_tables import (
    RazorFormatsTableGenerator,
    RazorManufacturersTableGenerator,
    RazorsTableGenerator,
)
from .table_generators.specialized_tables import (
    BlackbirdPlatesTableGenerator,
    ChristopherBradleyPlatesTableGenerator,
    GameChangerPlatesTableGenerator,
    StraightRazorSpecsTableGenerator,
    SuperSpeedTipsTableGenerator,
    StraightWidthsTableGenerator,
    StraightGrindsTableGenerator,
    StraightPointsTableGenerator,
)


class HardwareReportGenerator(BaseReportGenerator):
    """Hardware report generator."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ):
        """Initialize the hardware report generator.

        Args:
            metadata: Metadata from aggregated data
            data: Data from aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
        """
        super().__init__(metadata, data, comparison_data, debug)

    def generate_header(self) -> str:
        """Generate the report header."""
        month = self.metadata.get("month", "Unknown")
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)

        # Parse month for display
        try:
            from datetime import datetime

            date_obj = datetime.strptime(month, "%Y-%m")
            month_display = date_obj.strftime("%B %Y")
        except (ValueError, TypeError):
            month_display = month

        return (
            f"# Hardware Report - {month_display}\n\n"
            f"**Total Shaves:** {total_shaves:,}\n"
            f"**Unique Shavers:** {unique_shavers:,}\n\n"
        )

    def generate_observations(self) -> str:
        """Generate the observations section."""
        return (
            "## Observations\n\n"
            "*(This section will be populated with automated observations about trends "
            "and patterns in the hardware data.)*\n\n"
        )

    def generate_notes_and_caveats(self) -> str:
        """Generate the notes and caveats section."""
        return """## Notes & Caveats

- This data is collected from the r/wetshaving community's Shave of the Day (SOTD) posts
- Only posts that include product information are included in the analysis
- Product matching is performed automatically and may contain errors
- Users may post multiple SOTDs per day, which are all counted
- The data represents community participation, not necessarily market share or sales figures

"""

    def generate_tables(self) -> List[str]:
        """Generate all tables for the hardware report."""
        tables = []
        tables.append("## Tables\n\n")

        # Core product tables
        tables.append(self._generate_table("Razors", RazorsTableGenerator))
        tables.append(self._generate_table("Razor Manufacturers", RazorManufacturersTableGenerator))
        tables.append(self._generate_table("Razor Formats", RazorFormatsTableGenerator))
        tables.append(self._generate_table("Blades", BladesTableGenerator))
        tables.append(self._generate_table("Blade Manufacturers", BladeManufacturersTableGenerator))
        tables.append(self._generate_table("Brushes", BrushesTableGenerator))
        tables.append(self._generate_table("Brush Handle Makers", BrushHandleMakersTableGenerator))
        tables.append(self._generate_table("Brush Knot Makers", BrushKnotMakersTableGenerator))
        tables.append(self._generate_table("Brush Fibers", BrushFibersTableGenerator))
        tables.append(self._generate_table("Brush Knot Sizes", BrushKnotSizesTableGenerator))

        # Specialized tables
        tables.append(self._generate_table("Blackbird Plates", BlackbirdPlatesTableGenerator))
        tables.append(
            self._generate_table(
                "Christopher Bradley Plates", ChristopherBradleyPlatesTableGenerator
            )
        )
        tables.append(self._generate_table("Game Changer Plates", GameChangerPlatesTableGenerator))
        tables.append(self._generate_table("Super Speed Tips", SuperSpeedTipsTableGenerator))
        tables.append(self._generate_table("Straight Widths", StraightWidthsTableGenerator))
        tables.append(self._generate_table("Straight Grinds", StraightGrindsTableGenerator))
        tables.append(self._generate_table("Straight Points", StraightPointsTableGenerator))
        tables.append(
            self._generate_table("Straight Razor Specifications", StraightRazorSpecsTableGenerator)
        )

        return tables

    def _generate_table(self, title: str, generator_class) -> str:
        """Generate a single table using the specified generator."""
        generator = generator_class(self.data, self.debug)

        # Check if we have comparison data for delta calculations
        include_delta = bool(self.comparison_data)
        comparison_period = "previous month"  # Default comparison period

        # If we have comparison data, use the first available period
        if self.comparison_data:
            # Get the first available comparison period
            available_periods = list(self.comparison_data.keys())
            if available_periods:
                comparison_period = available_periods[0]
                comparison_data = self.comparison_data[comparison_period][
                    1
                ]  # Get the data, not metadata
            else:
                comparison_data = None
        else:
            comparison_data = None

        table_content = generator.generate_table(
            include_delta=include_delta,
            comparison_data=comparison_data,
            comparison_period=comparison_period,
        )

        # If the table is empty, provide a "No data available" message
        if not table_content:
            return f"### {title}\n\n*No data available*\n\n"

        return table_content
