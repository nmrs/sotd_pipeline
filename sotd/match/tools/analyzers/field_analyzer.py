#!/usr/bin/env python3
"""Focused module for basic field analysis functionality."""

import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.table import Table  # noqa: E402

from sotd.cli_utils.base_parser import BaseCLIParser  # noqa: E402
from sotd.match.tools.utils.analysis_base import AnalysisTool  # noqa: E402
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI  # noqa: E402


class FieldAnalyzer(AnalysisTool):
    """Analyzer for basic field analysis and table generation."""

    def get_parser(self):
        """Get CLI parser for field analysis tool."""
        parser = BaseCLIParser(
            description="Analyze matched fields using regex patterns and generate tables",
            add_help=True,
        )
        BaseAnalysisCLI.add_common_arguments(parser)
        BaseAnalysisCLI.add_pattern_arguments(parser)
        return parser

    def run(self, args) -> None:
        """Run the field analysis tool."""
        data = self.load_matched_data(args)

        if not data:
            self.console.print("[red]No data found for the specified time period[/red]")
            return

        if args.pattern:
            self.analyze_regex_patterns(data, args.field, args.pattern, args.limit)
        else:
            if args.field == "handle":
                self._analyze_handle_records(data)
            else:
                self._analyze_field_records(data, args.field)

    def _analyze_handle_records(self, data: List[Dict]) -> None:
        """Analyze handle records specifically."""
        table = Table(title="Matched Handle Records")
        table.add_column("Handle Maker")
        table.add_column("Original Brush")
        table.add_column("Match Type")
        table.add_column("Strategy")
        table.add_column("Handle Metadata")
        seen: Set[tuple] = set()

        for record in data:
            brush = record.get("brush")
            if (
                isinstance(brush, dict)
                and isinstance(brush.get("matched"), dict)
                and brush["matched"].get("handle_maker")
            ):
                matched = brush["matched"]
                handle_maker = matched.get("handle_maker", "")
                original = brush.get("original", "")
                match_type = brush.get("match_type", "")
                strategy = matched.get("_matched_by_strategy", "")
                handle_metadata = matched.get("handle_maker_metadata", {})
                row = [
                    str(handle_maker),
                    str(original),
                    str(match_type),
                    str(strategy),
                    str(handle_metadata) if handle_metadata else "",
                ]
                row_key = tuple(row)
                if row_key not in seen:
                    seen.add(row_key)

        for row_key in sorted(seen, key=lambda x: (x[0] == "", x[0].lower(), x[1].lower())):
            table.add_row(*row_key)
        self.console.print(table)

    def _analyze_field_records(self, data: List[Dict], field: str) -> None:
        """Analyze general field records."""
        table = self.create_field_table(f"Matched {field} Records", field)
        include_match_type = False
        include_strategy = False

        # Determine if match_type or strategy fields are present
        for record in data:
            field_data = record.get(field)
            if isinstance(field_data, dict) and "matched" in field_data:
                if "match_type" in field_data:
                    include_match_type = True
                if "strategy" in field_data:
                    include_strategy = True

        # Print matched table
        seen: Set[tuple] = set()
        for record in data:
            field_data = record.get(field)
            if isinstance(field_data, dict) and isinstance(field_data.get("matched"), dict):
                matched = field_data["matched"]
                main_name = self.format_field_name(field, matched)
                row = [
                    main_name,
                    field_data.get("original", ""),
                    field_data.get("match_type", "") if include_match_type else "",
                    field_data.get("strategy", "") if include_strategy else "",
                ]

                row_key = tuple(str(x) if x is not None else "" for x in row)
                if row_key not in seen:
                    seen.add(row_key)

        for row_key in sorted(seen, key=lambda x: (x[0] == "", x[0].lower(), x[1].lower())):
            table.add_row(*row_key)
        self.console.print(table)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the field analysis tool."""
    analyzer = FieldAnalyzer()
    parser = analyzer.get_parser()
    args = parser.parse_args(argv)
    analyzer.run(args)


if __name__ == "__main__":
    main()
