"""
CLI argument parsing for the enrich phase.

This module provides standardized CLI argument parsing for the enrich phase
using the BaseCLIParser to eliminate code duplication.
"""

from sotd.cli_utils.base_parser import BaseCLIParser


def get_parser() -> BaseCLIParser:
    """
    Get the argument parser for the enrich phase.

    Returns:
        BaseCLIParser: Configured argument parser for enrich phase
    """
    parser = BaseCLIParser(description="Enrich SOTD data with detailed specifications")

    # Add standardized parallel processing arguments
    parser.add_parallel_processing_arguments(
        default_max_workers=4,
        help_max_workers="Maximum parallel workers for month processing (default: 4)",
    )

    return parser
