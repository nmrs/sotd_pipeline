"""Software report generator for the SOTD pipeline report phase."""

from typing import List

from .base import BaseReportGenerator
from .table_generators.soap_tables import (
    BrandDiversityTableGenerator,
    SoapMakersTableGenerator,
    SoapsTableGenerator,
)


class SoftwareReportGenerator(BaseReportGenerator):
    """Software report generator."""

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
            f"# Software Report - {month_display}\n\n"
            f"**Total Shaves:** {total_shaves:,}\n"
            f"**Unique Shavers:** {unique_shavers:,}\n\n"
        )

    def generate_observations(self) -> str:
        """Generate the observations section."""
        return (
            "## Observations\n\n"
            "*(This section will be populated with automated observations about trends "
            "and patterns in the software data.)*\n\n"
        )

    def generate_notes_and_caveats(self) -> str:
        """Generate the notes and caveats section."""
        return """## Notes & Caveats

- This data is collected from the r/wetshaving community's Shave of the Day (SOTD) posts
- Only posts that include product information are included in the analysis
- Product matching is performed automatically and may contain errors
- Users may post multiple SOTDs per day, which are all counted
- The data represents community participation, not necessarily market share or sales figures
- Software refers to shaving soaps, creams, and other lathering products

"""

    def generate_tables(self) -> List[str]:
        """Generate all tables for the software report."""
        tables = []
        tables.append("## Tables\n\n")

        # Soap Makers Table
        soap_makers_table = SoapMakersTableGenerator(self.data, self.debug).generate_table()
        if soap_makers_table.strip():
            tables.append(soap_makers_table)
        else:
            tables.append("### Soap Makers\n\n*No data available*\n\n")

        # Soaps Table
        soaps_table = SoapsTableGenerator(self.data, self.debug).generate_table()
        if soaps_table.strip():
            tables.append(soaps_table)
        else:
            tables.append("### Soaps\n\n*No data available*\n\n")

        # Brand Diversity Table
        brand_diversity_table = BrandDiversityTableGenerator(self.data, self.debug).generate_table()
        if brand_diversity_table.strip():
            tables.append(brand_diversity_table)
        else:
            tables.append("### Brand Diversity\n\n*No data available*\n\n")

        return tables
