"""
Phase-1 entry point: retrieve SOTD thread headers for a month and print them.

Later chunks will expand this into full download, merge and save logic.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sotd.fetch.reddit import search_threads


def _parse_month(value: str) -> tuple[int, int]:
    """Convert YYYY-MM to (year, month)."""
    try:
        dt = datetime.strptime(value, "%Y-%m")
        return dt.year, dt.month
    except ValueError as exc:  # pragma: no cover
        raise argparse.ArgumentTypeError(
            f"Invalid month '{value}'. Expected format YYYY-MM."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SOTD thread IDs for a month")
    parser.add_argument(
        "--month",
        required=True,
        type=_parse_month,
        help="Target month in YYYY-MM format (e.g. 2025-05)",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--force", action="store_true")  # placeholder
    args = parser.parse_args()

    year, month = args.month
    threads = search_threads("wetshaving", year, month, debug=args.debug)

    if not threads:
        print("[WARN] No results – check credentials, search query, or month.")

    for sub in threads:
        print(f"{sub.id:>8}  {sub.title}")


if __name__ == "__main__":
    main()
