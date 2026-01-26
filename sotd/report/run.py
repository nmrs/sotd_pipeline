#!/usr/bin/env python3
"""
Generate statistical analysis reports from aggregated SOTD data.

CLI matrix
──────────
(no flags)                 → current month, hardware report
--month YYYY-MM            → that single month
--annual --year YYYY       → annual report for specific year
--annual --range YYYY:YYYY → annual reports for year range
--type hardware|software   → report type (default: hardware)
--data-dir DIR             → data directory for report file and input data (default: data, or SOTD_DATA_DIR env var)
--debug                    → enable debug logging
--force                    → force overwrite existing files
"""

import logging
import os
from pathlib import Path
from typing import Sequence

from sotd.utils.logging_config import setup_pipeline_logging

from . import cli
from .annual_run import run_annual_report
from .report_core import run_report


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the report phase."""
    # Setup logging with timestamp format matching shell script
    # Note: Don't use file handler - shell script redirects stdout to log file
    # Set logging level based on debug flag (will be updated after parsing args)
    setup_pipeline_logging(log_file=None, level=logging.INFO)

    try:
        parser = cli.get_parser()
        args = parser.parse_args(argv)

        # Update logging level if debug is enabled
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # Route to appropriate function based on annual flag
        if args.annual:
            # Annual reports handle missing files gracefully
            run_annual_report(args)
            return 0
        else:
            has_errors = run_report(args)
            return 1 if has_errors else 0
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Report generation interrupted by user")
        return 1  # Interrupted
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Report generation failed: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
