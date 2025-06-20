"""Hardware report generator for the SOTD pipeline report phase."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from sotd.utils.template_processor import TemplateProcessor

from .base import BaseReportGenerator
from .table_generator import TableGenerator


class HardwareReportGenerator(BaseReportGenerator):
    """Hardware report generator."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        template_path: Optional[str] = None,
    ):
        """Initialize the hardware report generator.

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
        """Generate the notes and caveats section using the new templating system."""
        # Get specific data collection statistics
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)
        avg_shaves_per_user = self.metadata.get("avg_shaves_per_user", 0)
        month = self.metadata.get("month", "Unknown")

        # Parse month for display
        try:
            from datetime import datetime

            date_obj = datetime.strptime(month, "%Y-%m")
            month_year = date_obj.strftime("%B %Y")
        except (ValueError, TypeError):
            month_year = month

        # Prepare variables for template
        variables = {
            "month_year": month_year,
            "total_shaves": f"{total_shaves:,}",
            "unique_shavers": str(unique_shavers),
            "avg_shaves_per_user": f"{avg_shaves_per_user:.1f}",
        }

        # Create table generator for table placeholders
        table_generator = TableGenerator(self.data, self.comparison_data, self.debug)

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Use the new template structure
        return processor.render_template("hardware", "report_template", variables, table_generator)

    def generate_tables(self) -> List[str]:
        """Generate all tables for the hardware report.

        Note: This method is now deprecated in favor of the templating system.
        Tables are now generated through the template placeholders.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []
