#!/usr/bin/env python3
"""CLI entry point for mismatch identification tool."""

from typing import List

from sotd.match.tools.mismatch_analyzer import MismatchAnalyzer


def get_parser():
    """Get CLI parser for mismatch identification tool."""
    analyzer = MismatchAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the mismatch identification tool."""
    analyzer = MismatchAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the mismatch identification tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
