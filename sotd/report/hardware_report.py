"""Hardware report generator for the SOTD pipeline report phase."""

from datetime import datetime
from typing import List

from .base import BaseReportGenerator
from .table_generators.razor_tables import (
    RazorFormatsTableGenerator,
    RazorManufacturersTableGenerator,
    RazorsTableGenerator,
)


class HardwareReportGenerator(BaseReportGenerator):
    """Hardware report generator."""

    def generate_header(self) -> str:
        """Generate hardware report header."""
        month = self.metadata["month"]
        total_shaves = self.metadata["total_shaves"]
        unique_shavers = self.metadata["unique_shavers"]

        # Parse month for display
        try:
            date_obj = datetime.strptime(month, "%Y-%m")
            month_display = date_obj.strftime("%B %Y")
        except ValueError:
            month_display = month

        header_lines = [
            f"# Hardware Report - {month_display}",
            "",
            f"**Total Shaves:** {total_shaves:,}",
            f"**Unique Shavers:** {unique_shavers:,}",
            "",
        ]

        return "\n".join(header_lines)

    def generate_observations(self) -> str:
        """Generate hardware observations section."""
        return (
            "## Observations\n\n"
            "*(This section will be populated with automated observations "
            "about trends and patterns in the hardware data.)*"
        )

    def generate_notes_and_caveats(self) -> str:
        """Generate hardware notes and caveats section."""
        return (
            "## Notes & Caveats\n\n"
            "- This data is collected from the r/wetshaving community's "
            "Shave of the Day (SOTD) posts\n"
            "- Only posts that include product information are included in the analysis\n"
            "- Product matching is performed automatically and may contain errors\n"
            "- Users may post multiple SOTDs per day, which are all counted\n"
            "- The data represents community participation, not necessarily "
            "market share or sales figures"
        )

    def generate_tables(self) -> List[str]:
        """Generate hardware tables."""
        if self.debug:
            print("[DEBUG] Generating hardware tables")

        tables = []
        tables.append("## Tables\n\n")

        # Generate razor format table
        if "razor_formats" in self.data:
            formats_generator = RazorFormatsTableGenerator(self.data, debug=self.debug)
            formats_table = formats_generator.generate_table()
            if formats_table:
                tables.append(formats_table)
                tables.append("")  # Empty line

        # Generate razors table
        if "razors" in self.data:
            razors_generator = RazorsTableGenerator(self.data, debug=self.debug)
            razors_table = razors_generator.generate_table()
            if razors_table:
                tables.append(razors_table)
                tables.append("")  # Empty line

        # Generate razor manufacturers table
        if "razor_manufacturers" in self.data:
            manufacturers_generator = RazorManufacturersTableGenerator(self.data, debug=self.debug)
            manufacturers_table = manufacturers_generator.generate_table()
            if manufacturers_table:
                tables.append(manufacturers_table)
                tables.append("")  # Empty line

        return tables
