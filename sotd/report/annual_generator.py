"""Annual report generator for SOTD pipeline."""

from pathlib import Path
from typing import Optional

from sotd.utils.template_processor import TemplateProcessor

from . import annual_load
from .table_generator import TableGenerator


def generate_annual_report(
    report_type: str,
    year: str,
    data_dir: Path,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> str:
    """Generate an annual report for the specified year and type.

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
    if debug:
        print(f"[DEBUG] Generating annual {report_type} report for {year}")
        print(f"[DEBUG] Data directory: {data_dir}")

    # Load annual data
    annual_data_file = annual_load.get_annual_file_path(data_dir, year)
    if not annual_data_file.exists():
        raise FileNotFoundError(f"Annual data file not found: {annual_data_file}")

    metadata, data = annual_load.load_annual_data(annual_data_file, debug=debug)

    if debug:
        print(f"[DEBUG] Loaded annual data for {year}")
        print(f"[DEBUG] Total shaves: {metadata['total_shaves']}")
        print(f"[DEBUG] Unique shavers: {metadata['unique_shavers']}")

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
    table_generator = TableGenerator(data, {}, debug)  # No comparison data for annual reports yet

    # Create template processor with custom path if provided
    if template_path:
        processor = TemplateProcessor(Path(template_path))
    else:
        processor = TemplateProcessor()

    # Generate report using annual template
    annual_template_name = f"annual_{report_type}"
    result = processor.render_template(
        annual_template_name, "report_template", variables, table_generator
    )

    if debug:
        print(f"[DEBUG] Generated annual {report_type} report for {year}")

    return result


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
                print(f"[DEBUG] Error generating table for {category}: {e}")
            return f"*Error generating table for {category}: {e}*"
        return table_md
