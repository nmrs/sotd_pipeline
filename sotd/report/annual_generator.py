"""Annual report generator for SOTD pipeline."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from sotd.utils.performance import PerformanceMonitor
from sotd.utils.template_processor import TemplateProcessor

from . import annual_load
from .base import BaseReportGenerator
from .table_generator import TableGenerator

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

        variables = {
            "year": self.year,
            "total_shaves": f"{self.metadata.get('total_shaves', 0):,}",
            "unique_shavers": str(self.metadata.get("unique_shavers", 0)),
            "included_months": str(_count(self.metadata.get("included_months", []))),
            "missing_months": str(_count(self.metadata.get("missing_months", []))),
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
                    print(f"[DEBUG] AnnualReport: Error generating table {table_name}: {e}")
                tables[table_name] = f"*Error generating table {table_name}: {e}*"

        # Create template processor with custom path if provided
        if self.template_path:
            processor = TemplateProcessor(Path(self.template_path))
        else:
            processor = TemplateProcessor()

        # Generate report using annual template
        annual_template_name = f"annual_{self.report_type}"
        return processor.process_template(annual_template_name, variables, tables)

    def generate_tables(self) -> list[str]:
        """Generate all tables for the annual report.

        Note: This method is now deprecated in favor of the templating system.
        Tables are now generated through the template placeholders.
        """
        # This method is kept for backward compatibility but is no longer used
        # Tables are now generated through the template system
        return []


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

        # Generate report content using unified patterns
        monitor.start_processing_timing()
        result = generate_annual_report_content(
            report_type, year, metadata, data, {}, debug, template_path
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
        tg = TableGenerator(data, formatted_comparison, self.debug)
        try:
            table_md = tg.generate_table_by_name(category)
        except Exception as e:
            if self.debug:
                logger.warning(f"Error generating table for {category}: {e}")
            return f"*Error generating table for {category}: {e}*"
        return table_md
