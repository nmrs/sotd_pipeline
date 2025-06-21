"""
CLI argument parsing for the extract phase.

This module provides standardized CLI argument parsing for the extract phase
using the BaseCLIParser to eliminate code duplication.
"""

from sotd.cli_utils.base_parser import BaseCLIParser


def get_parser() -> BaseCLIParser:
    """
    Get the argument parser for the extract phase.

    Returns:
        BaseCLIParser: Configured argument parser for extract phase
    """
    parser = BaseCLIParser(
        description="Extract razors, blades, soaps, and brushes from SOTD comments"
    )

    # Extract phase doesn't need any additional arguments beyond the base ones
    # All common arguments (month, year, range, start/end, out-dir, debug, force)
    # are provided by BaseCLIParser

    return parser
