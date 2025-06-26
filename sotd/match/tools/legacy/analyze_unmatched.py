#!/usr/bin/env python3
"""Unmatched analysis tool using focused module."""

from typing import List

from sotd.match.tools.unmatched_analyzer import UnmatchedAnalyzer


def get_parser():
    """Get CLI parser for unmatched analysis tool."""
    analyzer = UnmatchedAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the unmatched analysis tool."""
    analyzer = UnmatchedAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the unmatched analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
