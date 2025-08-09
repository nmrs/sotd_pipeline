"""
CLI argument parsing for the match phase.

This module provides standardized CLI argument parsing for the match phase
using the BaseCLIParser to eliminate code duplication.
"""

from sotd.cli_utils.base_parser import BaseCLIParser


def get_parser() -> BaseCLIParser:
    """
    Get the argument parser for the match phase.

    Returns:
        BaseCLIParser: Configured argument parser for match phase
    """
    parser = BaseCLIParser(
        description="Match razors, blades, soaps, and brushes from extracted SOTD data"
    )

    # Add match-specific arguments
    parser.add_argument(
        "--mode",
        choices=["match", "analyze_unmatched_razors"],
        default="match",
        help="Operation mode (default: match)",
    )

    # Add brush system selection flag (new system is now default)
    parser.add_argument(
        "--brush-system",
        choices=["new", "legacy"],
        default="new",
        help="Brush matching system to use (default: new multi-strategy scoring system)",
    )

    # Add standardized parallel processing arguments
    parser.add_parallel_processing_arguments(
        default_max_workers=4,
        help_max_workers="Maximum parallel workers for month processing (default: 4)",
    )

    return parser
