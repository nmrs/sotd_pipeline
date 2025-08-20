"""Unified monthly report generator for the SOTD pipeline report phase."""

from pathlib import Path
from typing import Any, Dict, Optional

from sotd.utils.template_processor import TemplateProcessor

from .base import BaseReportGenerator
from .table_generator import TableGenerator


class MonthlyReportGenerator(BaseReportGenerator):
    """Unified monthly report generator for both hardware and software reports."""

    def __init__(
        self,
        report_type: str,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        template_path: Optional[str] = None,
    ):
        """Initialize the unified monthly report generator.

        Args:
            report_type: Type of report ('hardware' or 'software')
            metadata: Metadata from aggregated data
            data: Data from aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
            template_path: Optional custom path to template file for testing
        """
        super().__init__(metadata, data, comparison_data, debug, template_path)
        self.report_type = report_type

    def generate_header(self) -> str:
        """Generate the report header.

        Note: This method is deprecated in favor of the templating system.
        The template now contains the complete report structure including headers.
        """
        # This method is kept for backward compatibility but is no longer used
        # Headers are now generated through the template system
        return ""

    def generate_notes_and_caveats(self) -> str:
        """Generate the complete monthly report content using the templating system."""
        # Get all available data collection statistics
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)
        avg_shaves_per_user = self.metadata.get("avg_shaves_per_user", 0)
        median_shaves_per_user = self.metadata.get("median_shaves_per_user", 0)

        # Hardware-specific metrics
        unique_razors = self.metadata.get("unique_razors", 0)
        unique_blades = self.metadata.get("unique_blades", 0)
        unique_brushes = self.metadata.get("unique_brushes", 0)

        # Software-specific metrics
        unique_soaps = self.metadata.get("unique_soaps", 0)
        unique_brands = self.metadata.get("unique_brands", 0)
        total_samples = self.metadata.get("total_samples", 0)
        sample_percentage = self.metadata.get("sample_percentage", 0)
        sample_users = self.metadata.get("sample_users", 0)
        sample_brands = self.metadata.get("sample_brands", 0)

        month = self.metadata.get("month", "Unknown")

        # Parse month for display
        try:
            from datetime import datetime

            date_obj = datetime.strptime(month, "%Y-%m")
            month_year = date_obj.strftime("%B %Y")
        except (ValueError, TypeError):
            month_year = month

        # Prepare ALL available variables for template
        # Templates can choose which ones to use
        variables = {
            "month_year": month_year,
            "total_shaves": f"{total_shaves:,}",
            "unique_shavers": str(unique_shavers),
            "avg_shaves_per_user": f"{avg_shaves_per_user:.1f}",
            "median_shaves_per_user": f"{median_shaves_per_user:.1f}",
            # Hardware variables
            "unique_razors": str(unique_razors),
            "unique_blades": str(unique_blades),
            "unique_brushes": str(unique_brushes),
            # Software variables
            "unique_soaps": str(unique_soaps),
            "unique_brands": str(unique_brands),
            "total_samples": str(total_samples),
            "sample_percentage": f"{sample_percentage:.1f}%",
            "sample_users": str(sample_users),
            "sample_brands": str(sample_brands),
        }

        # Create table generator for table placeholders
        if self.debug:
            print(f"[DEBUG] MonthlyReport({self.report_type}): Creating TableGenerator")
            print(
                f"[DEBUG] MonthlyReport({self.report_type}): "
                f"self.data keys: {list(self.data.keys())}"
            )
            print(
                f"[DEBUG] MonthlyReport({self.report_type}): self.comparison_data keys: "
                f"{list(self.comparison_data.keys()) if self.comparison_data else 'None'}"
            )

        table_generator = TableGenerator(self.data, self.comparison_data, self.debug)

        # Generate ALL available tables for the template
        # Templates can choose which ones to use
        tables = {}
        for table_name in table_generator.get_available_table_names():
            try:
                tables[table_name] = table_generator.generate_table_by_name(table_name)
            except Exception as e:
                if self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Error generating table {table_name}: {e}"
                    )
                tables[table_name] = f"*Error generating table {table_name}: {e}*"

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Generate report using the correct template name
        template_name = self.report_type

        if self.debug:
            print(
                f"[DEBUG] MonthlyReport({self.report_type}): Processing template: {template_name}"
            )
            print(f"[DEBUG] MonthlyReport({self.report_type}): Variables: {variables}")
            print(f"[DEBUG] MonthlyReport({self.report_type}): Tables: {list(tables.keys())}")

        return processor.process_template(template_name, variables, tables)

    def generate_tables(self) -> list[str]:
        """Generate all tables for the report.

        Note: This method is deprecated in favor of the templating system.
        Tables are now generated through the template system.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []
