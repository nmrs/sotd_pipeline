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
from .table_generators.cross_product_tables import (
    HighestUseCountPerBladeTableGenerator,
    RazorBladeCombinationsTableGenerator,
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
    StraightGrindsTableGenerator,
    StraightPointsTableGenerator,
    StraightWidthsTableGenerator,
    SuperSpeedTipsTableGenerator,
)
from .table_generators.user_tables import TopShaversTableGenerator


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

        # Parse month for display
        try:
            from datetime import datetime

            date_obj = datetime.strptime(month, "%Y-%m")
            month_display = date_obj.strftime("%B %Y")
        except (ValueError, TypeError):
            month_display = month

        return f"Welcome to your SOTD Hardware Report for {month_display}\n\n"

    def generate_observations(self) -> str:
        """Generate the observations section."""
        # TODO: Add automated trend analysis based on data patterns
        return (
            "## Observations\n\n"
            "*(This section will be populated with automated observations about trends "
            "and patterns in the hardware data, including notable changes and insights.)*\n\n"
        )

    def generate_notes_and_caveats(self) -> str:
        """Generate the notes and caveats section."""
        return """## Notes & Caveats

### Data Collection
- This data is collected from the r/wetshaving community's Shave of the Day (SOTD) posts
- Only posts that include product information are included in the analysis
- Users may post multiple SOTDs per day, which are all counted
- The data represents community participation, not necessarily market share or sales figures

### Product Matching
- Product matching is performed automatically and may contain errors
- Product names are normalized for consistency across reports
- Some products may be grouped under generic categories (e.g., "Other Straight Razor")

### Brush Data
- Brush handle makers and knot makers are attributed based on user input
- Fiber types are normalized to title case to prevent duplicates
- Knot sizes are filtered to reasonable ranges (15-50mm) to exclude invalid data
- Mixed fiber brushes are categorized separately from single-fiber types

### Razor Data
- Razor formats are categorized based on blade type (DE, GEM, Injector, etc.)
- Straight razors include specifications for grind, width, and point types
- Plate-specific data is tracked for razors with interchangeable plates

### Blade Data
- Blade formats are differentiated (DE, GEM, Injector, AC, etc.)
- Use counts represent individual blade usage, not package counts

### Delta Calculations
- Position-based deltas show movement in rankings between periods
- ↑ indicates improved position, ↓ indicates declined position, ↔ indicates no change
- "n/a" indicates the item was not present in the comparison period
- Delta calculations are based on position rankings, not absolute values

### User Statistics
- "avg shaves per user" represents the average number of shaves per unique user for each product
- Cross-product tables show combinations and highest individual usage patterns
- User data is anonymized and aggregated for privacy

### Data Quality
- Invalid or missing data is filtered out during processing
- Debug logging is available to identify data quality issues
- Historical comparisons require data from previous periods to be available

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
        tables.append(self._generate_table("Knot Fibers", BrushFibersTableGenerator))
        tables.append(self._generate_table("Knot Sizes", BrushKnotSizesTableGenerator))

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

        # Cross-product tables
        tables.append(
            self._generate_table(
                "Most Used Blades in Most Used Razors", RazorBladeCombinationsTableGenerator
            )
        )
        tables.append(
            self._generate_table(
                "Highest Use Count per Blade", HighestUseCountPerBladeTableGenerator
            )
        )

        # User tables
        tables.append(self._generate_table("Top Shavers", TopShaversTableGenerator))

        return tables

    def _generate_table(self, title: str, generator_class) -> str:
        """Generate a single table using the specified generator."""
        generator = generator_class(self.data, self.debug)

        # Check if we have comparison data for delta calculations
        include_delta = bool(self.comparison_data)

        # If we have comparison data, pass all available periods
        if self.comparison_data:
            # Pass all comparison data to the generator
            table_content = generator.generate_table(
                include_delta=include_delta,
                comparison_data=self.comparison_data,
            )
        else:
            table_content = generator.generate_table(
                include_delta=include_delta,
                comparison_data=None,
            )

        # If the table is empty, provide a "No data available" message
        if not table_content:
            return f"### {title}\n\n*No data available*\n\n"

        return table_content
