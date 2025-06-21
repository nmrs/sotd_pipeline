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
--data-root DIR            → root directory for all input data (default: data)
--out-dir DIR              → output directory for report file (default: data)
--debug                    → enable debug logging
--force                    → force overwrite existing files
"""

from typing import Sequence

from . import cli
from .annual_run import run_annual_report
from .report_core import run_report


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for the report phase."""
    try:
        parser = cli.get_parser()
        args = parser.parse_args(argv)
        cli.validate_args(args)

        # Route to appropriate function based on annual flag
        if args.annual:
            run_annual_report(args)
        else:
            run_report(args)
    except KeyboardInterrupt:
        print("\n[INFO] Report generation interrupted by user")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        # Note: args might not be defined if parse_report_args fails
        # We'll handle this in the exception handler


if __name__ == "__main__":
    main()
