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

    # Add test string argument for direct brush matching
    parser.add_argument(
        "--test-string",
        type=str,
        help="Test a specific brush string directly through the matcher",
    )

    # Add standardized parallel processing arguments
    parser.add_parallel_processing_arguments(
        default_max_workers=8,
        help_max_workers="Maximum parallel workers for month processing (default: 8)",
    )

    # Add delta processing support
    parser.add_delta_arguments()

    return parser
