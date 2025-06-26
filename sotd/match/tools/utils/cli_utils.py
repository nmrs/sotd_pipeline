#!/usr/bin/env python3
"""CLI utilities for analysis tools."""

from sotd.cli_utils.base_parser import BaseCLIParser


class BaseAnalysisCLI:
    """Base CLI class for analysis tools with common argument patterns."""

    @staticmethod
    def add_common_arguments(parser: BaseCLIParser) -> None:
        """Add common arguments to analysis tool parsers."""
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of entries to show (default: 20)",
        )
        parser.add_argument(
            "--field",
            choices=["razor", "blade", "brush", "soap", "handle"],
            default="razor",
            help="Field to analyze (default: razor)",
        )
        # Note: --debug is already provided by BaseCLIParser

    @staticmethod
    def add_pattern_arguments(parser: BaseCLIParser) -> None:
        """Add pattern analysis arguments to parsers."""
        parser.add_argument("--pattern", help="Regex pattern to match against field values")
        parser.add_argument(
            "--show-details", action="store_true", help="Show detailed match analysis"
        )
        parser.add_argument(
            "--show-patterns", action="store_true", help="Show pattern effectiveness"
        )
        parser.add_argument(
            "--show-opportunities", action="store_true", help="Show improvement opportunities"
        )
        parser.add_argument(
            "--show-mismatches", action="store_true", help="Show potential mismatches"
        )
        parser.add_argument(
            "--show-examples",
            type=str,
            help="Show examples for specific pattern (e.g., 'Chisel & Hound Badger')",
        )
        parser.add_argument("--mismatch-limit", type=int, default=20, help="Limit mismatches shown")
        parser.add_argument("--example-limit", type=int, default=15, help="Limit examples shown")

    @staticmethod
    def add_soap_arguments(parser: BaseCLIParser) -> None:
        """Add soap-specific arguments to parsers."""
        parser.add_argument(
            "--threshold", type=float, default=0.9, help="Fuzzy similarity threshold (default: 0.9)"
        )
        parser.add_argument(
            "--mode",
            choices=["scent", "brand"],
            default="scent",
            help="Suggest patterns for 'scent' or 'brand'",
        )
        parser.add_argument(
            "--reverse", action="store_true", help="Reverse the sort order (lowest count first)"
        )

    @staticmethod
    def add_confidence_arguments(parser: BaseCLIParser) -> None:
        """Add confidence analysis arguments to parsers."""
        parser.add_argument(
            "--confidence-threshold",
            type=float,
            default=70.0,
            help="Confidence threshold for analysis (default: 70.0)",
        )
        parser.add_argument(
            "--show-confidence-distribution",
            action="store_true",
            help="Show confidence score distribution",
        )
        parser.add_argument(
            "--show-low-confidence",
            action="store_true",
            help="Show only low confidence matches",
        )

    @staticmethod
    def add_field_analysis_arguments(parser: BaseCLIParser) -> None:
        """Add field analysis arguments to parsers."""
        parser.add_argument(
            "--show-field-breakdown",
            action="store_true",
            help="Show breakdown by field components",
        )
        parser.add_argument(
            "--show-field-patterns",
            action="store_true",
            help="Show field-specific pattern analysis",
        )
        parser.add_argument(
            "--field-detail-level",
            choices=["basic", "detailed", "exhaustive"],
            default="basic",
            help="Level of detail for field analysis (default: basic)",
        )
