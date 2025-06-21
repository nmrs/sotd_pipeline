"""
CLI argument parsing for the fetch phase.

This module provides standardized CLI argument parsing for the fetch phase
using the BaseCLIParser to eliminate code duplication.
"""

from sotd.cli_utils.base_parser import BaseCLIParser


def get_parser() -> BaseCLIParser:
    """
    Get the argument parser for the fetch phase.

    Returns:
        BaseCLIParser: Configured argument parser for fetch phase
    """
    parser = BaseCLIParser(description="Fetch & persist SOTD data")

    # Add fetch-specific arguments
    parser.add_argument(
        "--audit", action="store_true", help="Audit existing data for missing files and days"
    )
    parser.add_argument(
        "--list-months",
        action="store_true",
        help="List months with existing threads or comments files",
    )

    return parser
