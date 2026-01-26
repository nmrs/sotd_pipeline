"""
CLI argument parsing for the extract phase.

This module provides standardized CLI argument parsing for the extract phase
using the BaseCLIParser to eliminate code duplication.
"""

from pathlib import Path

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

    # Add standardized parallel processing arguments
    parser.add_parallel_processing_arguments(
        default_max_workers=8,
        help_max_workers="Maximum parallel workers for month processing (default: 8)",
    )

    # Add delta processing support
    parser.add_delta_arguments()

    # Note: override file is now automatically relative to --data-dir
    # No need for --override-file flag - it's always data_dir/extract_overrides.yaml

    return parser
