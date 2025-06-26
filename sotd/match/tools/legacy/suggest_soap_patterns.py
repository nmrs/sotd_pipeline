#!/usr/bin/env python3
"""Suggest soap patterns tool using focused module."""

from typing import List

from sotd.match.tools.analyzers.soap_analyzer import SoapAnalyzer


def get_parser():
    """Get CLI parser for suggest soap patterns tool."""
    analyzer = SoapAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the suggest soap patterns tool."""
    analyzer = SoapAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the suggest soap patterns tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
