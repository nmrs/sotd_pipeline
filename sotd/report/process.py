#!/usr/bin/env python3
"""Core report generation logic for the report phase."""

from typing import Any, Dict

from .base import BaseReportGenerator
from .hardware_report import HardwareReportGenerator
from .software_report import SoftwareReportGenerator


def create_report_generator(
    report_type: str, metadata: Dict[str, Any], data: Dict[str, Any], debug: bool = False
) -> BaseReportGenerator:
    """Create a report generator based on the report type.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        debug: Enable debug logging

    Returns:
        Appropriate report generator instance

    Raises:
        ValueError: If report_type is not supported
    """
    if report_type == "hardware":
        return HardwareReportGenerator(metadata, data, debug)
    elif report_type == "software":
        return SoftwareReportGenerator(metadata, data, debug)
    else:
        raise ValueError(f"Unsupported report type: {report_type}")


def generate_report_content(
    report_type: str, metadata: Dict[str, Any], data: Dict[str, Any], debug: bool = False
) -> str:
    """Generate complete report content.

    Args:
        report_type: Type of report ('hardware' or 'software')
        metadata: Metadata from aggregated data
        data: Data from aggregated data
        debug: Enable debug logging

    Returns:
        Complete report content as a string
    """
    generator = create_report_generator(report_type, metadata, data, debug)
    return generator.generate_report()
