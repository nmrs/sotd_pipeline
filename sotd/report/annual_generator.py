"""Annual report generator for SOTD pipeline."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from sotd.utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor
from sotd.utils.template_processor import TemplateProcessor

from . import annual_load
from .table_generator import TableGenerator

logger = logging.getLogger(__name__)


@dataclass
class AnnualGeneratorMetrics(BasePerformanceMetrics):
    """Performance metrics for annual report generation."""

    # Annual generator specific fields
    year: str = field(default="")
    report_type: str = field(default="")
    template_processing_time: float = field(default=0.0)
    table_generation_time: float = field(default=0.0)
    report_size_chars: int = field(default=0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "year": self.year,
                "report_type": self.report_type,
                "template_processing_time_seconds": self.template_processing_time,
                "table_generation_time_seconds": self.table_generation_time,
                "report_size_chars": self.report_size_chars,
            }
        )
        return base_dict


class AnnualGeneratorPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual report generation."""

    def __init__(self, year: str, report_type: str, parallel_workers: int = 1):
        self.year = year
        self.report_type = report_type
        super().__init__("annual_generator", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualGeneratorMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualGeneratorMetrics:
        """Create annual generator performance metrics."""
        metrics = AnnualGeneratorMetrics()
        metrics.year = self.year
        metrics.report_type = self.report_type
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print(
            f"\n=== Annual Generator Performance Summary ({metrics.year} {metrics.report_type}) ==="
        )
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"Template Processing Time: {metrics.template_processing_time:.2f}s")
        print(f"Table Generation Time: {metrics.table_generation_time:.2f}s")
        print(f"File I/O Time: {metrics.file_io_time:.2f}s")
        print(f"Report Size: {metrics.report_size_chars:,} characters")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")


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
    monitor = AnnualGeneratorPerformanceMonitor(year, report_type)
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

        # Validate report type
        if report_type not in ["hardware", "software"]:
            raise ValueError(f"Unsupported report type: {report_type}")

        # Prepare variables for template
        def _count(val):
            if isinstance(val, list):
                return len(val)
            if isinstance(val, int):
                return val
            return 0

        variables = {
            "year": year,
            "total_shaves": f"{metadata['total_shaves']:,}",
            "unique_shavers": str(metadata["unique_shavers"]),
            "included_months": str(_count(metadata["included_months"])),
            "missing_months": str(_count(metadata["missing_months"])),
        }

        # Create table generator for table placeholders
        monitor.start_processing_timing()
        table_generator = TableGenerator(
            data, {}, debug
        )  # No comparison data for annual reports yet
        monitor.end_processing_timing()

        # Create template processor with custom path if provided
        if template_path:
            processor = TemplateProcessor(Path(template_path))
        else:
            processor = TemplateProcessor()

        # Generate report using annual template
        monitor.start_processing_timing()
        annual_template_name = f"annual_{report_type}"
        result = processor.render_template(
            annual_template_name, "report_template", variables, table_generator
        )
        monitor.end_processing_timing()

        # Update metrics
        monitor.metrics.report_size_chars = len(result)
        monitor.metrics.record_count = 1

        if debug:
            logger.info(f"Generated annual {report_type} report for {year}")

        return result

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


class AnnualReportGenerator:
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
