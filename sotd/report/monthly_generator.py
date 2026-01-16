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

        Raises:
            ValueError: If there's no meaningful data to process (fail-fast behavior)
        """
        # Fail-fast check: ensure there's meaningful data to process
        if not data or not isinstance(data, dict):
            raise ValueError("No data provided for report generation")

        # Check if there are any non-empty data sections
        has_meaningful_data = False
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                has_meaningful_data = True
                break

        if not has_meaningful_data:
            raise ValueError(
                "No meaningful data available for report generation. "
                "All data sections are empty or missing."
            )

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
        # Get month for display formatting
        month = self.metadata.get("month", "Unknown")

        # Parse month for display
        try:
            from datetime import datetime

            date_obj = datetime.strptime(month, "%Y-%m")
            month_year = date_obj.strftime("%B %Y")
        except (ValueError, TypeError):
            month_year = month

        # Prepare variables dynamically from metadata
        # Start with month_year for display formatting
        variables = {"month_year": month_year}

        # Get metadata from the data structure
        # For CLI calls, self.data is just the data section, so we need to get metadata
        # from the metadata parameter that was passed to the constructor
        if "meta" in self.data:
            # Direct call with full structure
            data_metadata = self.data["meta"]
        else:
            # CLI call - use the metadata passed to constructor
            data_metadata = self.metadata

        # Dynamically add all metadata fields with appropriate formatting
        for key, value in data_metadata.items():
            if key == "month":
                continue  # Skip month as we handle it separately with month_year
            elif key == "avg_shaves_per_user" or key == "median_shaves_per_user":
                # Format decimal numbers
                variables[key] = f"{value:.1f}"
            elif key == "sample_percentage":
                # Format percentage
                variables[key] = f"{value:.1f}%"
            elif isinstance(value, (int, float)):
                # Format all numeric values with commas (integers) or as decimals (floats)
                if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
                    variables[key] = f"{int(value):,}"
                else:
                    # For non-integer floats, format with appropriate decimal places
                    variables[key] = f"{value:.1f}"
            else:
                # Convert everything else to string
                variables[key] = str(value)

        # Initialize table generator with the new universal approach
        # self.data is already the data section (not the entire JSON structure)
        table_generator = TableGenerator(
            self.data,
            self.comparison_data,
            current_month=self.metadata.get("month"),
            debug=self.debug,
        )

        # Get the template content to detect enhanced table syntax
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        template_name = self.report_type
        template_content = processor.get_template(template_name)

        # Generate basic tables for all available aggregators
        tables = {}

        # First, scan the template for all table placeholders
        import re

        template_table_pattern = r"\{\{tables\.([^|}]+)\}\}"
        template_table_names = re.findall(template_table_pattern, template_content)

        # Generate tables for all template placeholders found
        for table_name in template_table_names:
            try:
                table_content = table_generator.generate_table(table_name, deltas=True)
                if table_content:
                    placeholder = f"{{{{tables.{table_name}}}}}"
                    tables[placeholder] = table_content
                else:
                    # If table generation fails or returns empty, provide a placeholder message
                    placeholder = f"{{{{tables.{table_name}}}}}"
                    tables[placeholder] = "*No data available for this category*"
            except Exception as e:
                if self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Error generating table '{table_name}': {e}"
                    )
                # Provide a placeholder message for failed tables
                placeholder = f"{{{{tables.{table_name}}}}}"
                tables[placeholder] = "*No data available for this category*"

        # Process enhanced table syntax with parameters
        enhanced_tables = self._process_enhanced_table_syntax(template_content, table_generator)

        # Merge enhanced tables with basic tables
        tables.update(enhanced_tables)

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

        # Find all unique full placeholders (not just table names) to handle multiple
        # placeholders with the same table name but different parameters
        full_placeholder_pattern = r"\{\{tables\.[^}]+\|[^}]+\}\}"
        full_placeholders = re.findall(full_placeholder_pattern, template_content)

        # Process each unique placeholder
        for full_placeholder in set(full_placeholders):
            try:
                # Parse the placeholder to extract table name and parameters
                from .table_parameter_parser import TableParameterParser

                parser = TableParameterParser()
                table_name, parameters = parser.parse_placeholder(full_placeholder)

                if self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Processing enhanced table: {table_name} "
                        f"with parameters: {parameters}"
                    )

                # Generate the table with parameters
                # Extract numeric limits (any parameter that's not ranks, rows,
                # columns, deltas, or wsdb)
                numeric_limits = {}
                for key, value in parameters.items():
                    if key not in ["ranks", "rows", "columns", "deltas", "wsdb"]:
                        numeric_limits[key] = value

                table_content = table_generator.generate_table(
                    table_name,
                    ranks=parameters.get("ranks"),
                    rows=parameters.get("rows"),
                    columns=parameters.get("columns"),
                    deltas=parameters.get("deltas") == "true",
                    wsdb=parameters.get("wsdb") == "true",
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
                # Handle enhanced table syntax errors gracefully
                if self.debug:
                    print(
                        f"[DEBUG] MonthlyReport({self.report_type}): "
                        f"Enhanced table syntax error for "
                        f"'{full_placeholder}' - {e}. "
                        "Adding error message placeholder."
                    )

                # Add error message placeholder so the template processor can replace it
                # This ensures the placeholder doesn't appear as raw text in the output
                enhanced_tables[full_placeholder] = "*No data available for this category*"
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
