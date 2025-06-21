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

    # Enrich phase doesn't need any additional arguments beyond the base ones
    # All common arguments (month, year, range, start/end, out-dir, debug, force)
    # are provided by BaseCLIParser

    return parser
