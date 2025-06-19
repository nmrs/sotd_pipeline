#!/usr/bin/env python3
"""Core report generation logic for the report phase."""

from datetime import datetime
from typing import Any, Dict, List

from .base import BaseReportGenerator
from .hardware_report import HardwareReportGenerator


class SoftwareReportGenerator(BaseReportGenerator):
    """Software report generator."""

    def generate_header(self) -> str:
        """Generate software report header."""
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
            f"# Software Report - {month_display}",
            "",
            f"**Total Shaves:** {total_shaves:,}",
            f"**Unique Shavers:** {unique_shavers:,}",
            "",
        ]

        return "\n".join(header_lines)

    def generate_observations(self) -> str:
        """Generate software observations section."""
        return (
            "## Observations\n\n"
            "*(This section will be populated with automated observations "
            "about trends and patterns in the software data.)*"
        )

    def generate_notes_and_caveats(self) -> str:
        """Generate software notes and caveats section."""
        return (
            "## Notes & Caveats\n\n"
            "- This data is collected from the r/wetshaving community's "
            "Shave of the Day (SOTD) posts\n"
            "- Only posts that include product information are included in the analysis\n"
            "- Product matching is performed automatically and may contain errors\n"
            "- Users may post multiple SOTDs per day, which are all counted\n"
            "- The data represents community participation, not necessarily "
            "market share or sales figures\n"
            "- Software includes soaps, creams, and other lathering products"
        )

    def generate_tables(self) -> List[str]:
        """Generate software tables."""
        if self.debug:
            print("[DEBUG] Generating software tables")

        # TODO: Implement table generation
        return ["## Tables\n\n", "*(Table generation will be implemented in subsequent steps)*"]


def create_report_generator(
    report_type: str, metadata: Dict[str, Any], data: Dict[str, Any], debug: bool = False
) -> BaseReportGenerator:
    """Create a report generator based on the report type.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        debug: Enable debug logging

    Returns:
        Appropriate report generator instance

    Raises:
        ValueError: If report_type is not supported
    """
    if report_type == "hardware":
        return HardwareReportGenerator(metadata, data, debug)
    elif report_type == "software":
        return SoftwareReportGenerator(metadata, data, debug)
    else:
        raise ValueError(f"Unsupported report type: {report_type}")


def generate_report_content(
    report_type: str, metadata: Dict[str, Any], data: Dict[str, Any], debug: bool = False
) -> str:
    """Generate complete report content.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        debug: Enable debug logging

    Returns:
        Complete report content as a string
    """
    generator = create_report_generator(report_type, metadata, data, debug)
    return generator.generate_report()
