#!/usr/bin/env python3
"""Original analysis tool using focused module."""

from typing import List

from sotd.match.tools.field_analyzer import FieldAnalyzer


def get_parser():
    """Get CLI parser for original analysis tool."""
    analyzer = FieldAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the original analysis tool."""
    analyzer = FieldAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the original analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
