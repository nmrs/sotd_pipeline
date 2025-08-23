"""Unified monthly report generator for the SOTD pipeline report phase."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from sotd.utils.template_processor import TemplateProcessor

from .base import BaseReportGenerator
from .table_generators.table_generator import TableGenerator


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

        # Initialize table generator with the new universal approach
        table_generator = TableGenerator(self.data, self.comparison_data, debug=self.debug)

        # Get the template content to detect enhanced table syntax
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        template_name = self.report_type
        template_content = processor.get_template(template_name)

        # Generate basic tables for all available aggregators
        tables = {}
        for table_name in table_generator.get_available_table_names():
            try:
                table_content = table_generator.generate_table(table_name)
                if table_content:
                    tables[f"{{{{tables.{table_name}}}}}"] = table_content
                elif self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Table '{table_name}' generated empty content"
                    )
            except Exception as e:
                if self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Error generating table '{table_name}': {e}"
                    )

        # Process enhanced table syntax with parameters
        enhanced_tables = self._process_enhanced_table_syntax(template_content, table_generator)

        # Merge enhanced tables with basic tables
        tables.update(enhanced_tables)

        if self.debug:
            print(
                f"[DEBUG] MonthlyReport({self.report_type}): Processing template: {template_name}"
            )
            print(f"[DEBUG] MonthlyReport({self.report_type}): Variables: {variables}")
            print(f"[DEBUG] MonthlyReport({self.report_type}): Tables: {list(tables.keys())}")

        return processor.process_template(template_name, variables, tables)

    def _process_enhanced_table_syntax(
        self, template_content: str, table_generator: TableGenerator
    ) -> Dict[str, str]:
        """Process enhanced table syntax with parameters in the template.

        Args:
            template_content: The template content to scan for enhanced syntax
            table_generator: The table generator instance

        Returns:
            Dictionary of enhanced table placeholders to their generated content
        """
        enhanced_tables = {}

        # Pattern to match enhanced table syntax: {{tables.table_name|param:value|param:value}}
        # This pattern specifically looks for the pipe character to identify enhanced syntax
        # It must contain at least one pipe character to be considered enhanced
        enhanced_pattern = r"\{\{tables\.([^|}]+)\|[^}]+\}\}"

        # Find all enhanced table placeholders
        matches = re.findall(enhanced_pattern, template_content)

        for match in matches:
            # Extract the full placeholder to get parameters
            full_placeholder_pattern = r"\{\{tables\." + re.escape(match) + r"\|[^}]+\}\}"
            full_match = re.search(full_placeholder_pattern, template_content)

            if full_match:
                full_placeholder = full_match.group(0)

                try:
                    # Parse the placeholder to extract table name and parameters
                    from .table_parameter_parser import TableParameterParser

                    parser = TableParameterParser()
                    table_name, parameters = parser.parse_placeholder(full_placeholder)

                    if self.debug:
                        print(
                            f"[DEBUG] MonthlyReport({self.report_type}): "
                            f"Processing enhanced table: {table_name} with parameters: {parameters}"
                        )

                    # Generate the table with parameters
                    # Extract numeric limits (any parameter that's not ranks, rows, columns, or deltas)
                    numeric_limits = {}
                    for key, value in parameters.items():
                        if key not in ["ranks", "rows", "columns", "deltas"]:
                            numeric_limits[key] = value

                    table_content = table_generator.generate_table(
                        table_name,
                        ranks=parameters.get("ranks"),
                        rows=parameters.get("rows"),
                        columns=parameters.get("columns"),
                        deltas=parameters.get("deltas") == "true",
                        **numeric_limits,
                    )

                    # Use the full placeholder as the key for replacement
                    enhanced_tables[full_placeholder] = table_content

                    if self.debug:
                        print(
                            f"[DEBUG] MonthlyReport({self.report_type}): "
                            f"Generated enhanced table for {table_name}"
                        )

                except Exception as e:
                    # Handle enhanced table syntax errors gracefully by falling back to basic table
                    # generation
                    if self.debug:
                        print(
                            f"[DEBUG] MonthlyReport({self.report_type}): "
                            f"Enhanced table syntax error for "
                            f"'{{tables.{match}}}' - {e}. "
                            f"Falling back to basic table generation."
                        )

                    # Don't add this placeholder to enhanced_tables - let it be processed as basic
                    # table
                    # This allows the template processor to handle it normally
                    continue

        return enhanced_tables

    def generate_tables(self) -> list[str]:
        """Generate all tables for the report.

        Note: This method is deprecated in favor of the templating system.
        Tables are now generated through the template system.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []
