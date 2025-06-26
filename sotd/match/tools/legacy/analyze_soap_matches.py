#!/usr/bin/env python3
"""Soap matches analysis tool using focused module."""

from typing import List

from sotd.match.tools.analyzers.soap_analyzer import SoapAnalyzer


def get_parser():
    """Get CLI parser for soap matches analysis tool."""
    analyzer = SoapAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the soap matches analysis tool."""
    analyzer = SoapAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the soap matches analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
