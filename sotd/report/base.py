"""Base classes for the report phase."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseReportGenerator(ABC):
    """Base class for report generators."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        template_path: Optional[str] = None,
    ):
        """Initialize the report generator.

        Args:
            metadata: Metadata from aggregated data
            data: Data from aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
            template_path: Optional custom path to template file for testing
        """
        self.metadata = metadata
        self.data = data
        self.comparison_data = comparison_data or {}
        self.debug = debug
        self.template_path = template_path

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

        # Notes and caveats (now includes tables via templating)
        notes = self.generate_notes_and_caveats()
        sections.append(notes)

        return "\n".join(sections)
