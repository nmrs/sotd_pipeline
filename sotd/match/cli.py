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

    # Parallel processing options
    parallel_group = parser.add_mutually_exclusive_group()
    parallel_group.add_argument("--parallel", action="store_true", help="Force parallel processing")
    parallel_group.add_argument(
        "--sequential", action="store_true", help="Force sequential processing"
    )

    parser.add_argument(
        "--max-workers", type=int, default=4, help="Maximum parallel workers (default: 4)"
    )

    return parser
