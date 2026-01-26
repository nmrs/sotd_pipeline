"""
Data directory path resolution utility.

Provides a unified way to determine the data directory path with precedence:
1. CLI argument (--data-dir)
2. SOTD_DATA_DIR environment variable
3. Default: ./data
"""

import os
from pathlib import Path
from typing import Optional


def get_data_dir(cli_arg: Optional[Path | str] = None) -> Path:
    """
    Get data directory path with precedence: CLI arg > env var > default.

    Args:
        cli_arg: Optional Path or str from CLI argument (--data-dir).
                 If None or equals default "data", checks SOTD_DATA_DIR env var first.

    Returns:
        Path: Resolved data directory path

    Examples:
        >>> # CLI arg takes precedence (non-default value)
        >>> get_data_dir(Path("/custom/path"))
        Path('/custom/path')

        >>> # Env var used when CLI arg is None or default
        >>> os.environ['SOTD_DATA_DIR'] = '/data'
        >>> get_data_dir(None)
        Path('/data')
        >>> get_data_dir(Path("data"))
        Path('/data')

        >>> # Default when neither is set
        >>> del os.environ['SOTD_DATA_DIR']
        >>> get_data_dir(None)
        Path('data')
    """
    # Convert to Path for comparison
    cli_path = Path(cli_arg) if cli_arg is not None else None
    default_path = Path("data")

    # If CLI arg is None or equals the default, check env var first
    # This allows env var to work even when argparse uses default value
    if cli_path is None or cli_path == default_path:
        sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
        if sotd_data_dir:
            return Path(sotd_data_dir)
        # If no env var, use the default (or the provided default if explicitly given)
        return default_path if cli_path is None else cli_path

    # CLI argument takes highest precedence (non-default value)
    return cli_path
