#!/usr/bin/env python3
"""Focused module for unmatched analysis functionality."""

import re
from collections import defaultdict
from typing import Dict, List

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.analysis_base import AnalysisTool
from sotd.match.tools.cli_utils import BaseAnalysisCLI


class UnmatchedAnalyzer(AnalysisTool):
    """Analyzer for unmatched field values."""

    def get_parser(self):
        """Get CLI parser for unmatched analysis tool."""
        parser = BaseCLIParser(
            description="Analyze unmatched field values (razor, blade, soap, brush) "
            "for pattern and candidate discovery",
            add_help=True,
        )
        BaseAnalysisCLI.add_common_arguments(parser)
        return parser

    def run(self, args) -> None:
        """Run the unmatched analysis tool."""
        all_unmatched = defaultdict(list)

        for record in self.load_matched_data(args):
            if args.field == "handle":
                self._process_handle_unmatched(record, all_unmatched)
            else:
                self._process_field_unmatched(record, args.field, all_unmatched)

        self._print_unmatched_results(all_unmatched, args.field, args.limit)

    def _process_handle_unmatched(self, record: Dict, all_unmatched: Dict) -> None:
        """Process unmatched handle records."""
        brush = record.get("brush")
        if isinstance(brush, dict):
            matched = brush.get("matched")
            if matched is None:
                # If nothing matched at all, count as unmatched handle
                original = brush.get("original", "")
                all_unmatched[original].append(record.get("_source_file", ""))
            elif isinstance(matched, dict):
                handle_maker = matched.get("handle_maker")
                if not handle_maker:
                    original = brush.get("original", "")
                    all_unmatched[original].append(record.get("_source_file", ""))

    def _process_field_unmatched(self, record: Dict, field: str, all_unmatched: Dict) -> None:
        """Process unmatched field records."""
        field_val = record.get(field)
        if isinstance(field_val, str):
            # For blades, strip use count before adding to unmatched
            if field == "blade":
                field_val = self._strip_use_count(field_val)
            all_unmatched[field_val].append(record.get("_source_file", ""))
        elif isinstance(field_val, dict):
            if "matched" not in field_val or not field_val["matched"]:
                # For blades, strip use count from original text
                original = field_val.get("original", "")
                if field == "blade":
                    original = self._strip_use_count(original)
                all_unmatched[original].append(record.get("_source_file", ""))

    def _strip_use_count(self, text: str) -> str:
        """Strip use count from blade text, e.g. 'Koraat (5)' -> 'Koraat'."""
        return re.sub(r"\s*[\(\[\{](?:x)?\d+(?:x)?[\)\]\}]", "", text, flags=re.IGNORECASE).strip()

    def _print_unmatched_results(self, all_unmatched: Dict, field: str, limit: int) -> None:
        """Print unmatched analysis results."""
        print(
            f"\n🔍 Found {len(all_unmatched)} unique unmatched {field} "
            f"descriptions across all files:\n"
        )
        # Sort alphabetically by value, then by file count descending
        for value, files in sorted(all_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1])))[
            :limit
        ]:
            print(f"{value:<60}  ({len(files)} uses)")
            for f in sorted(set(files)):
                print(f"    ↳ {f}")


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the unmatched analysis tool."""
    analyzer = UnmatchedAnalyzer()
    parser = analyzer.get_parser()
    args = parser.parse_args(argv)
    analyzer.run(args)


if __name__ == "__main__":
    main()
