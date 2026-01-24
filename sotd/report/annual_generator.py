"""Annual report generator for SOTD pipeline."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from sotd.utils.performance import PerformanceMonitor
from sotd.utils.template_processor import TemplateProcessor

from . import annual_load
from .base import BaseReportGenerator
from .table_generators.table_generator import TableGenerator

logger = logging.getLogger(__name__)


class AnnualReportGenerator(BaseReportGenerator):
    """Annual report generator that follows unified patterns."""

    def __init__(
        self,
        year: str,
        report_type: str,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        debug: bool = False,
        template_path: Optional[str] = None,
    ):
        """Initialize the annual report generator.

        Args:
            year: Year to generate report for (YYYY format)
            report_type: Type of report ('hardware' or 'software')
            metadata: Metadata from annual aggregated data
            data: Data from annual aggregated data
            comparison_data: Historical data for delta calculations
            debug: Enable debug logging
            template_path: Optional custom path to template file for testing
        """
        super().__init__(metadata, data, comparison_data, debug, template_path)
        self.year = year
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
        """Generate the complete annual report content using the templating system."""

        # Prepare variables for template
        def _count(val):
            if isinstance(val, list):
                return len(val)
            if isinstance(val, int):
                return val
            return 0

        missing_months_count = _count(self.metadata.get("missing_months", []))
        included_months_count = _count(self.metadata.get("included_months", []))

        # Format all numeric values with commas
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)
        total_samples = self.metadata.get("total_samples", 0)
        sample_users = self.metadata.get("sample_users", 0)
        sample_brands = self.metadata.get("sample_brands", 0)

        # Calculate unique counts from aggregated data for software reports
        unique_soaps = 0
        unique_brands = 0

        if self.report_type == "software":
            # Calculate unique_soaps from aggregated soaps list
            soaps = self.data.get("soaps", [])
            unique_soaps = len(soaps) if soaps else 0

            # Calculate unique_brands from aggregated soap_makers list
            soap_makers = self.data.get("soap_makers", [])
            unique_brands = len(soap_makers) if soap_makers else 0

        variables = {
            "year": self.year,
            "total_shaves": f"{total_shaves:,}",
            "unique_shavers": f"{unique_shavers:,}",
            "avg_shaves_per_user": f"{self.metadata.get('avg_shaves_per_user', 0):.1f}",
            "median_shaves_per_user": f"{self.metadata.get('median_shaves_per_user', 0):.1f}",
            "total_samples": f"{total_samples:,}",
            "sample_percentage": f"{self.metadata.get('sample_percentage', 0):.1f}%",
            "sample_users": f"{sample_users:,}",
            "sample_brands": f"{sample_brands:,}",
            "included_months": f"{included_months_count:,}",
            "missing_months": f"{missing_months_count:,}",
            "missing_months_note": (
                f"* Note: {missing_months_count:,} month{'s' if missing_months_count != 1 else ''} "
                f"{'were' if missing_months_count != 1 else 'was'} missing from the data set."
                if missing_months_count > 0
                else ""
            ),
        }

        # Add software-specific variables if this is a software report
        if self.report_type == "software":
            variables["unique_soaps"] = f"{unique_soaps:,}"
            variables["unique_brands"] = f"{unique_brands:,}"
            # Get unique_sample_soaps from metadata (calculated during annual aggregation)
            unique_sample_soaps = self.metadata.get("unique_sample_soaps", 0)
            variables["unique_sample_soaps"] = f"{unique_sample_soaps:,}"

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Generate report using annual template
        annual_template_name = f"annual_{self.report_type}"
        template_content = processor.get_template(annual_template_name)

        # Create table generator for table placeholders
        # For annual reports, use year-12 (December) as the "current month" for delta calculations
        # This allows the delta calculator to work with year-based comparisons
        current_month_for_deltas = f"{self.year}-12"
        table_generator = TableGenerator(
            self.data, self.comparison_data, current_month_for_deltas, self.debug
        )

        # Scan template for table placeholders (like monthly reports do)
        # This ensures we use the exact placeholder names from the template (with hyphens)
        import re

        template_table_pattern = r"\{\{tables\.([^|}]+)(?:\|[^}]*)?\}\}"
        template_table_names = re.findall(template_table_pattern, template_content)

        # Generate tables for all template placeholders found
        tables = {}
        for table_name in template_table_names:
            try:
                # Generate table using the template name (with hyphens)
                # TableGenerator.generate_table() handles hyphen-to-underscore conversion internally
                table_content = table_generator.generate_table(table_name, deltas=True)
                if table_content:
                    # Use the full placeholder as the key to match template syntax
                    placeholder = f"{{{{tables.{table_name}}}}}"
                    tables[placeholder] = table_content
                else:
                    placeholder = f"{{{{tables.{table_name}}}}}"
                    tables[placeholder] = "*No data available for this category*"
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] AnnualReport: Error generating table '{table_name}': {e}")
                placeholder = f"{{{{tables.{table_name}}}}}"
                tables[placeholder] = f"*Error generating table {table_name}: {e}*"

        # Process enhanced table syntax with parameters (like monthly reports)
        enhanced_tables = self._process_enhanced_table_syntax(template_content, table_generator)
        tables.update(enhanced_tables)

        return processor.process_template(annual_template_name, variables, tables)

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
        import re

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
                        f"[DEBUG] AnnualReport({self.report_type}): "
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
                        f"[DEBUG] AnnualReport({self.report_type}): "
                        f"Generated enhanced table for {table_name}"
                    )

            except Exception as e:
                # Handle enhanced table syntax errors gracefully
                if self.debug:
                    print(
                        f"[DEBUG] AnnualReport({self.report_type}): "
                        f"Error processing enhanced table '{full_placeholder}': {e}"
                    )
                enhanced_tables[full_placeholder] = f"*Error processing enhanced table syntax: {e}*"

        return enhanced_tables

    def generate_tables(self) -> list[str]:
        """Generate all tables for the annual report.

        Note: This method is now deprecated in favor of the templating system.
        Tables are now generated through the template placeholders.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []

    def get_structured_data(self) -> Dict[str, Any]:
        """Get structured data for API consumption (no row limits).

        Returns:
            Dictionary with keys: metadata, tables, stats
            - metadata: Report metadata (year, counts, etc.)
            - tables: Dictionary of table names to list of row dictionaries
            - stats: Additional statistics
        """
        # Create table generator for table data
        # For annual reports, use year-12 (December) as the "current month" for delta calculations
        current_month_for_deltas = f"{self.year}-12"
        table_generator = TableGenerator(
            self.data, self.comparison_data, current_month_for_deltas, self.debug
        )

        # Get all available table names from the data
        available_tables = {}
        for key in self.data.keys():
            if isinstance(self.data[key], list):
                # Convert snake_case to kebab-case for table names
                table_name = key.replace("_", "-")
                try:
                    # Get structured data without row limits
                    # Empty lists will return empty list from get_structured_table_data
                    table_data = table_generator.get_structured_table_data(table_name, deltas=True)
                    available_tables[table_name] = table_data
                except Exception as e:
                    if self.debug:
                        print(
                            f"[DEBUG] AnnualReport({self.report_type}): "
                            f"Error getting structured data for '{table_name}': {e}"
                        )
                    # Include empty list for failed tables
                    available_tables[table_name] = []

        # Prepare metadata (convert numeric values to appropriate types)
        structured_metadata = {}
        for key, value in self.metadata.items():
            if isinstance(value, (int, float)):
                structured_metadata[key] = value
            elif isinstance(value, list):
                structured_metadata[key] = value
            else:
                structured_metadata[key] = str(value)

        # Add year to metadata
        structured_metadata["year"] = self.year

        # Calculate stats
        stats = {
            "total_tables": len(available_tables),
            "tables_with_data": sum(1 for v in available_tables.values() if len(v) > 0),
        }

        return {
            "metadata": structured_metadata,
            "tables": available_tables,
            "stats": stats,
        }


def create_annual_report_generator(
    report_type: str,
    year: str,
    metadata: Dict[str, Any],
    data: Dict[str, Any],
    comparison_data: Optional[Dict[str, Any]] = None,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> AnnualReportGenerator:
    """Create an annual report generator based on the report type.

    Args:
        report_type: Type of report ('hardware' or 'software')
        year: Year to generate report for (YYYY format)
        metadata: Metadata from annual aggregated data
        data: Data from annual aggregated data
        comparison_data: Historical data for delta calculations
        debug: Enable debug logging
        template_path: Optional custom path to template file for testing

    Returns:
        Annual report generator instance

    Raises:
        ValueError: If report_type is not supported
    """
    if report_type not in ["hardware", "software"]:
        raise ValueError(f"Unsupported report type: {report_type}")

    return AnnualReportGenerator(
        year, report_type, metadata, data, comparison_data, debug, template_path
    )


def generate_annual_report_content(
    report_type: str,
    year: str,
    metadata: Dict[str, Any],
    data: Dict[str, Any],
    comparison_data: Optional[Dict[str, Any]] = None,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> str:
    """Generate complete annual report content.

    Args:
        report_type: Type of report ('hardware' or 'software')
        year: Year to generate report for (YYYY format)
        metadata: Metadata from annual aggregated data
        data: Data from annual aggregated data
        comparison_data: Historical data for delta calculations
        debug: Enable debug logging
        template_path: Optional custom path to template file for testing

    Returns:
        Complete annual report content as a string
    """
    generator = create_annual_report_generator(
        report_type, year, metadata, data, comparison_data, debug, template_path
    )
    return generator.generate_report()


def generate_annual_report(
    report_type: str,
    year: str,
    data_dir: Path,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> str:
    """Generate an annual report for the specified year and type with performance monitoring.

    Args:
        report_type: Type of report ('hardware' or 'software')
        year: Year to generate report for (YYYY format)
        data_dir: Directory containing annual aggregated data
        debug: Enable debug logging
        template_path: Optional custom path to template file for testing

    Returns:
        Generated report content as a string

    Raises:
        FileNotFoundError: If annual data file doesn't exist
        ValueError: If report_type is not supported
        KeyError: If required data is missing
    """
    monitor = PerformanceMonitor("annual_generator")
    monitor.start_total_timing()

    try:
        if debug:
            logger.info(f"Generating annual {report_type} report for {year}")
            logger.info(f"Data directory: {data_dir}")

        # Load annual data
        monitor.start_file_io_timing()
        annual_data_file = annual_load.get_annual_file_path(data_dir, year)
        if not annual_data_file.exists():
            raise FileNotFoundError(f"Annual data file not found: {annual_data_file}")

        metadata, data = annual_load.load_annual_data(annual_data_file, debug=debug)
        monitor.end_file_io_timing()

        if debug:
            logger.info(f"Loaded annual data for {year}")
            logger.info(f"Total shaves: {metadata['total_shaves']}")
            logger.info(f"Unique shavers: {metadata['unique_shavers']}")

        # Load comparison data for delta calculations (previous year, 5 years ago)
        comparison_data = {}
        try:
            from .annual_comparison_loader import AnnualComparisonLoader

            # Calculate comparison years: previous year and 5 years ago
            year_int = int(year)
            comparison_years = [str(year_int - 1), str(year_int - 5)]

            loader = AnnualComparisonLoader(debug=debug)
            annual_data_dir = data_dir / "aggregated" / "annual"
            comparison_years_data = loader.load_comparison_years(comparison_years, annual_data_dir)

            # Convert to format expected by TableGenerator: {YYYY-MM: (metadata, data)}
            # Use December (12) as the representative month for each year
            # Annual data structure: {metadata: {...}, razors: [...], blades: [...], ...}
            # We need to extract metadata and put everything else in a "data" dict
            for comp_year, comp_data in comparison_years_data.items():
                # Extract metadata
                comp_metadata = comp_data.get("metadata", {})
                # Extract all non-metadata keys as the data section
                comp_data_section = {k: v for k, v in comp_data.items() if k != "metadata"}
                # Use YYYY-12 format to match monthly comparison data format
                comparison_data[f"{comp_year}-12"] = (comp_metadata, comp_data_section)

            if debug:
                logger.info(
                    f"Loaded comparison data for years: {list(comparison_years_data.keys())}"
                )
                print(
                    f"[DEBUG] Loaded comparison data for years: {list(comparison_years_data.keys())}"
                )
        except Exception as e:
            if debug:
                logger.warning(f"Failed to load comparison data: {e}")
                print(f"[DEBUG] Warning: Failed to load comparison data: {e}")
            comparison_data = {}

        # Generate report content using unified patterns
        monitor.start_processing_timing()
        result = generate_annual_report_content(
            report_type, year, metadata, data, comparison_data, debug, template_path
        )
        monitor.end_processing_timing()

        # Update metrics
        monitor.metrics.record_count = 1

        if debug:
            logger.info(f"Generated annual {report_type} report for {year}")

        return result

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


class LegacyAnnualReportGenerator:
    """Legacy annual report generator for backward compatibility."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def generate_table_with_deltas(
        self,
        current_year_data: dict,
        comparison_data: dict,
        categories: list[str],
        comparison_years: list[str],
    ) -> str:
        """
        Generate a markdown table for the given categories with delta columns for comparison years.
        """
        # Use the first category for simplicity in tests
        if not categories:
            return "*No categories specified*"
        category = categories[0]
        data = current_year_data.get("data", {})
        # Prepare comparison_data in the format expected by table generators.
        # Format: {period: (metadata, data)}
        formatted_comparison = {}
        for year in comparison_years:
            if year in comparison_data:
                meta = comparison_data[year].get("meta", {})
                d = comparison_data[year].get("data", {})
                formatted_comparison[year] = (meta, d)
            else:
                # Add empty placeholder for missing years
                formatted_comparison[year] = ({}, {})
        tg = TableGenerator(data, formatted_comparison, None, self.debug)
        try:
            # Pass deltas=True to include delta columns in the table
            table_md = tg.generate_table(category, deltas=True)
        except Exception as e:
            if self.debug:
                logger.warning(f"Error generating table for {category}: {e}")
            return f"*Error generating table for {category}: {e}*"
        return table_md
