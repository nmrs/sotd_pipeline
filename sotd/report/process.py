#!/usr/bin/env python3
"""Core report generation logic for the report phase."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List


class BaseReportGenerator(ABC):
    """Base class for report generators."""

    def __init__(self, metadata: Dict[str, Any], data: Dict[str, Any], debug: bool = False):
        """Initialize the report generator.

        Args:
            metadata: Metadata from aggregated data
            data: Data from aggregated data
            debug: Enable debug logging
        """
        self.metadata = metadata
        self.data = data
        self.debug = debug

    @abstractmethod
    def generate_header(self) -> str:
        """Generate the report header."""
        pass

    @abstractmethod
    def generate_observations(self) -> str:
        """Generate the observations section."""
        pass

    @abstractmethod
    def generate_notes_and_caveats(self) -> str:
        """Generate the notes and caveats section."""
        pass

    @abstractmethod
    def generate_tables(self) -> List[str]:
        """Generate all tables for the report."""
        pass

    def generate_report(self) -> str:
        """Generate the complete report."""
        if self.debug:
            print("[DEBUG] Generating complete report")

        sections = []

        # Header
        header = self.generate_header()
        sections.append(header)
        sections.append("")  # Empty line

        # Observations
        observations = self.generate_observations()
        sections.append(observations)
        sections.append("")  # Empty line

        # Notes and caveats
        notes = self.generate_notes_and_caveats()
        sections.append(notes)
        sections.append("")  # Empty line

        # Tables
        tables = self.generate_tables()
        sections.extend(tables)

        return "\n".join(sections)


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

        # TODO: Implement table generation
        return ["## Tables\n\n", "*(Table generation will be implemented in subsequent steps)*"]


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
