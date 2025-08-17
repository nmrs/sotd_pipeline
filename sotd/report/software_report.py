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
        """Generate the report header.

        Note: This method is deprecated in favor of the templating system.
        The template now contains the complete report structure including headers.
        """
        # This method is kept for backward compatibility but is no longer used
        # Headers are now generated through the template system
        return ""

    def generate_notes_and_caveats(self) -> str:
        """Generate the complete report content using the templating system."""
        # Get specific data collection statistics
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)
        unique_soaps = self.metadata.get("unique_soaps", 0)
        unique_brands = self.metadata.get("unique_brands", 0)
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
            "unique_soaps": str(unique_soaps),
            "unique_brands": str(unique_brands),
        }

        # Create table generator for table placeholders
        table_generator = TableGenerator(self.data, self.comparison_data, self.debug)

        # Generate all tables for the template
        tables = {}
        for table_name in table_generator.get_available_table_names():
            try:
                tables[table_name] = table_generator.generate_table_by_name(table_name)
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] SoftwareReport: Error generating table {table_name}: {e}")
                tables[table_name] = f"*Error generating table {table_name}: {e}*"

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Use the new template structure - this now returns the complete report
        return processor.process_template("software", variables, tables)

    def generate_tables(self) -> List[str]:
        """Generate all tables for the software report.

        Note: This method is now deprecated in favor of the templating system.
        Tables are now generated through the template placeholders.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []
