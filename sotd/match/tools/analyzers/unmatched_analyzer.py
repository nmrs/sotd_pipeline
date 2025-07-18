#!/usr/bin/env python3
"""Focused module for unmatched analysis functionality."""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.cli_utils.base_parser import BaseCLIParser  # noqa: E402
from sotd.match.tools.utils.analysis_base import AnalysisTool  # noqa: E402
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI  # noqa: E402
from sotd.utils.match_filter_utils import strip_blade_count_patterns  # noqa: E402


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
            self._process_field_unmatched(record, args.field, all_unmatched)

        self._print_unmatched_results(all_unmatched, args.field, args.limit)

    def analyze_unmatched(self, args) -> dict:
        """Analyze unmatched items and return structured results for API use."""
        all_unmatched = defaultdict(list)

        for record in self.load_matched_data(args):
            self._process_field_unmatched(record, args.field, all_unmatched)

        # Convert to structured format for API
        unmatched_items = []
        # Sort alphabetically by value, then by file count descending (same as CLI)
        sorted_items = sorted(all_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1])))[
            : args.limit
        ]

        for original_text, file_infos in sorted_items:
            # Extract examples from source files (limit to 5 examples)
            examples = list(set(info["file"] for info in file_infos if info["file"]))[:5]

            unmatched_items.append(
                {
                    "item": original_text,
                    "count": len(file_infos),
                    "examples": examples,
                }
            )

        return {
            "field": args.field,
            "total_unmatched": len(all_unmatched),
            "unmatched_items": unmatched_items,
        }

    def _process_field_unmatched(self, record: Dict, field: str, all_unmatched: Dict) -> None:
        """Process unmatched field records."""
        if field == "brush":
            # Use new brush-specific logic for handle/knot granularity
            self._process_brush_unmatched(record, all_unmatched)
        else:
            # Use existing simple logic for razor, blade, soap
            self._process_simple_field_unmatched(record, field, all_unmatched)

    def _process_simple_field_unmatched(
        self, record: Dict, field: str, all_unmatched: Dict
    ) -> None:
        """Process unmatched simple field records (razor, blade, soap)."""
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
            # Skip intentionally skipped blades
            if field == "blade" and field_val.get("_intentionally_skipped", False):
                return

            # Check if matched field is missing, empty, or doesn't contain valid match data
            matched = field_val.get("matched")
            if not matched or (isinstance(matched, dict) and not matched.get("brand")):
                # For blades, strip use count from original text
                original = field_val.get("original", "")
                if field == "blade":
                    normalized = self._strip_use_count(original)
                    all_unmatched[normalized].append(file_info)
                else:
                    all_unmatched[original].append(file_info)

    def _process_brush_unmatched(self, record: Dict, all_unmatched: Dict) -> None:
        """Process unmatched brush records with handle/knot granularity."""
        brush = record.get("brush")
        if not isinstance(brush, dict):
            return

        matched = brush.get("matched")
        original = brush.get("original", "")
        file_info = {
            "file": record.get("_source_file", ""),
            "line": record.get("_source_line", "unknown"),
        }

        # If nothing matched at all, count as unmatched brush
        if matched is None:
            all_unmatched[original].append(file_info)
            return

        if not isinstance(matched, dict):
            all_unmatched[original].append(file_info)
            return

        # Check handle component
        handle = matched.get("handle")
        if handle and handle.get("brand") in [None, "UnknownMaker", "Unknown"]:
            handle_text = handle.get("source_text", "unknown handle")
            matched_knot = matched.get("knot", {}).get("brand")
            if matched_knot:
                all_unmatched[f"❌ Handle: {handle_text} (✅ Knot: {matched_knot})"].append(
                    file_info
                )
            else:
                all_unmatched[f"❌ Handle: {handle_text}"].append(file_info)

        # Check knot component
        knot = matched.get("knot")
        if knot and knot.get("brand") in [None, "UnknownKnot", "Unknown"]:
            knot_text = knot.get("source_text", "unknown knot")
            matched_handle = matched.get("handle", {}).get("brand")
            if matched_handle:
                all_unmatched[f"❌ Knot: {knot_text} (✅ Handle: {matched_handle})"].append(
                    file_info
                )
            else:
                all_unmatched[f"❌ Knot: {knot_text}"].append(file_info)

        # If neither handle nor knot issues, but still unmatched, show as general brush issue
        if not handle and not knot and matched.get("brand") is None:
            all_unmatched[original].append(file_info)

    def _strip_use_count(self, text: str) -> str:
        """Strip use count from blade text using shared normalization logic.

        This method uses the shared strip_blade_count_patterns function to ensure
        consistency with enrich phase and mismatch analyzer normalization.
        """
        return strip_blade_count_patterns(text)

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
