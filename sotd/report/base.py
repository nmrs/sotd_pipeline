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
    def generate_notes_and_caveats(self) -> str:
        """Generate the notes and caveats section."""
        pass

    @abstractmethod
    def generate_tables(self) -> List[str]:
        """Generate all tables for the report."""
        pass

    def generate_report(self) -> str:
        """Generate the complete report.

        Returns:
            Complete report as a string
        """
        if self.debug:
            print("[DEBUG] Generating complete report")

        # With the new templating system, the template contains the complete report structure
        # including the welcome message and all sections, so we just return the rendered template
        return self.generate_notes_and_caveats()

    @abstractmethod
    def get_structured_data(self) -> Dict[str, Any]:
        """Get structured data for API consumption (no row limits).

        Returns:
            Dictionary with keys: metadata, tables, stats
            - metadata: Report metadata (month/year, counts, etc.)
            - tables: Dictionary of table names to list of row dictionaries
            - stats: Additional statistics
        """
        pass
