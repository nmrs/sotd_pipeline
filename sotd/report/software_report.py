"""Software report generator for the SOTD pipeline report phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from sotd.utils.template_processor import TemplateProcessor

from .base import BaseReportGenerator
from .table_generator import TableGenerator


class SoftwareReportGenerator(BaseReportGenerator):
    """Software report generator."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        template_path: Optional[str] = None,
    ):
        """Initialize the software report generator.

        Args:
            metadata: Metadata from aggregated data
            data: Data from aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
            template_path: Optional custom path to template file for testing
        """
        super().__init__(metadata, data, comparison_data, debug, template_path)

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
        """Generate the notes and caveats section using the new templating system."""
        # Create table generator for table placeholders
        table_generator = TableGenerator(self.data, self.comparison_data, self.debug)

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Use the simplified template structure
        return processor.render_template("software", "template", {}, table_generator)

    def generate_tables(self) -> List[str]:
        """Generate all tables for the software report.

        Note: This method is now deprecated in favor of the templating system.
        Tables are now generated through the template placeholders.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []
