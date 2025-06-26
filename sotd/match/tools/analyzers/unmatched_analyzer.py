#!/usr/bin/env python3
"""Focused module for unmatched analysis functionality."""

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.utils.analysis_base import AnalysisTool
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI


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
                file_info = {
                    "file": record.get("_source_file", ""),
                    "line": record.get("_source_line", "unknown"),
                }
                all_unmatched[original].append(file_info)
            elif isinstance(matched, dict):
                handle_maker = matched.get("handle_maker")
                if not handle_maker:
                    original = brush.get("original", "")
                    file_info = {
                        "file": record.get("_source_file", ""),
                        "line": record.get("_source_line", "unknown"),
                    }
                    all_unmatched[original].append(file_info)

    def _process_field_unmatched(self, record: Dict, field: str, all_unmatched: Dict) -> None:
        """Process unmatched field records."""
        field_val = record.get(field)
        file_info = {
            "file": record.get("_source_file", ""),
            "line": record.get("_source_line", "unknown"),
        }

        if isinstance(field_val, str):
            # For blades, strip use count before adding to unmatched
            if field == "blade":
                field_val = self._strip_use_count(field_val)
            all_unmatched[field_val].append(file_info)
        elif isinstance(field_val, dict):
            if "matched" not in field_val or not field_val["matched"]:
                # For blades, strip use count from original text
                original = field_val.get("original", "")
                if field == "blade":
                    original = self._strip_use_count(original)
                all_unmatched[original].append(file_info)

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

            # Group by file and show line numbers
            file_lines = defaultdict(list)
            for file_info in files:
                if isinstance(file_info, dict):
                    # If file_info is a dict with line number
                    file_name = file_info.get("file", file_info.get("_source_file", "unknown"))
                    line_num = file_info.get("line", file_info.get("_source_line", "unknown"))
                    file_lines[file_name].append(line_num)
                else:
                    # If file_info is just a string (backward compatibility)
                    file_lines[file_info].append("unknown")

            for file_name in sorted(set(file_lines.keys())):
                line_numbers = file_lines[file_name]
                if len(line_numbers) == 1 and line_numbers[0] != "unknown":
                    print(f"    ↳ {file_name} (line {line_numbers[0]})")
                else:
                    # Show multiple occurrences or unknown line numbers
                    unique_lines = sorted(set(line_numbers))
                    if "unknown" in unique_lines:
                        print(f"    ↳ {file_name}")
                    else:
                        line_str = ", ".join(
                            str(line) for line in unique_lines[:5]
                        )  # Limit to 5 line numbers
                        if len(unique_lines) > 5:
                            line_str += f" (+{len(unique_lines) - 5} more)"
                        print(f"    ↳ {file_name} (lines {line_str})")


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the unmatched analysis tool."""
    analyzer = UnmatchedAnalyzer()
    parser = analyzer.get_parser()
    args = parser.parse_args(argv)
    analyzer.run(args)


if __name__ == "__main__":
    main()
