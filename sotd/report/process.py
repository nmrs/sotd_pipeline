#!/usr/bin/env python3
"""Core report generation logic for the report phase."""

from typing import Any, Dict, Optional

from .base import BaseReportGenerator
from .hardware_report import HardwareReportGenerator
from .software_report import SoftwareReportGenerator


def create_report_generator(
    report_type: str,
    metadata: Dict[str, Any],
    data: Dict[str, Any],
    comparison_data: Optional[Dict[str, Any]] = None,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> BaseReportGenerator:
    """Create a report generator based on the report type.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        comparison_data: Historical data for delta calculations
        debug: Enable debug logging
        template_path: Optional custom path to template file for testing

    Returns:
        Appropriate report generator instance

    Raises:
        ValueError: If report_type is not supported
    """
    if comparison_data is None:
        comparison_data = {}

    if report_type == "hardware":
        return HardwareReportGenerator(metadata, data, comparison_data, debug, template_path)
    elif report_type == "software":
        return SoftwareReportGenerator(metadata, data, comparison_data, debug, template_path)
    else:
        raise ValueError(f"Unsupported report type: {report_type}")


def generate_report_content(
    report_type: str,
    metadata: Dict[str, Any],
    data: Dict[str, Any],
    comparison_data: Optional[Dict[str, Any]] = None,
    debug: bool = False,
    template_path: Optional[str] = None,
) -> str:
    """Generate complete report content.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        comparison_data: Historical data for delta calculations
        debug: Enable debug logging
        template_path: Optional custom path to template file for testing

    Returns:
        Complete report content as a string
    """
    generator = create_report_generator(
        report_type, metadata, data, comparison_data, debug, template_path
    )
    return generator.generate_report()
