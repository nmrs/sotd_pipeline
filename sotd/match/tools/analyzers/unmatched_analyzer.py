#!/usr/bin/env python3
"""Analyze unmatched products in matched data."""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path for importing SOTD modules
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.tools.utils.analysis_base import AnalysisTool  # noqa: E402


def extract_text(field_data: Any, field: str = "") -> str:
    """Extract normalized text from field data.

    Args:
        field_data: Field data from record (can be string or dict)
        field: Field name for context (optional)

    Returns:
        Normalized text string
    """
    if isinstance(field_data, str):
        # Legacy format - already normalized
        return field_data
    elif isinstance(field_data, dict):
        # New structured format - use normalized field
        normalized = field_data.get("normalized", "")
        if normalized:
            return normalized
        # Fallback to original if normalized is not available
        return field_data.get("original", "")
    else:
        return ""


class UnmatchedAnalyzer(AnalysisTool):
    """Analyze unmatched products in matched data."""

    def get_parser(self):
        """Get CLI parser for the unmatched analyzer."""
        from sotd.cli_utils.base_parser import BaseCLIParser

        parser = BaseCLIParser(
            description="Analyze unmatched products in matched data",
            add_help=True,
        )
        parser.add_argument(
            "--field",
            choices=["razor", "blade", "soap", "brush"],
            default="blade",
            help="Field to analyze (default: blade)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Limit number of results to show (default: 50)",
        )
        return parser

    def run(self, args) -> None:
        """Run the unmatched analyzer."""
        results = self.analyze_unmatched(args)
        self._print_unmatched_results(results, args.field, args.limit)

    def analyze_unmatched(self, args) -> dict:
        """Analyze unmatched products in matched data."""
        data = self.load_matched_data(args)
        all_unmatched = defaultdict(list)

        for record in data:
            self._process_field_unmatched(record, args.field, all_unmatched)

        return all_unmatched

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
            "comment_id": record.get("id", ""),
        }

        if isinstance(field_val, str):
            # Legacy format - use the string as-is since it should already be normalized
            all_unmatched[field_val].append(file_info)
        elif isinstance(field_val, dict):
            # Skip intentionally skipped blades (now using match_type)
            if field == "blade" and field_val.get("match_type") in [
                "filtered",
                "irrelevant_razor_format",
            ]:
                return

            # Check if matched field is missing, empty, or doesn't contain valid match data
            matched = field_val.get("matched")
            if not matched or (isinstance(matched, dict) and not matched.get("brand")):
                # Use extract_text helper for consistency
                normalized = extract_text(field_val, field)
                all_unmatched[normalized].append(file_info)

    def _process_brush_unmatched(self, record: Dict, all_unmatched: Dict) -> None:
        """Process unmatched brush records with handle/knot granularity."""
        brush = record.get("brush")
        if not isinstance(brush, dict):
            return

        matched = brush.get("matched")

        file_info = {
            "file": record.get("_source_file", ""),
            "line": record.get("_source_line", "unknown"),
            "comment_id": record.get("id", ""),
        }

        # If nothing matched at all, count as unmatched brush
        if matched is None:
            # Use extract_text helper for consistency
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(file_info)
            return

        if not isinstance(matched, dict):
            # Use extract_text helper for consistency
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(file_info)
            return

        # Check if we have a complete brush match (brand and model identified)
        # If so, consider it matched regardless of handle/knot component details
        if matched.get("brand") and matched.get("model"):
            # Complete brush match - don't add to unmatched
            return

        # Only check handle/knot components if we don't have a complete brush match
        # Check handle component
        handle = matched.get("handle")
        handle_unmatched = None
        if handle and (
            handle.get("brand") is None or handle.get("brand") in ["UnknownMaker", "Unknown"]
        ):
            handle_text = handle.get("source_text", "unknown handle")
            handle_unmatched = {"text": handle_text, "pattern": None}

        # Check knot component
        knot = matched.get("knot")
        knot_unmatched = None
        if knot and (knot.get("brand") is None or knot.get("brand") in ["UnknownKnot", "Unknown"]):
            knot_text = knot.get("source_text", "unknown knot")
            knot_unmatched = {"text": knot_text, "pattern": None}

        # If we have unmatched components, add to the list
        if handle_unmatched or knot_unmatched:
            # Use extract_text helper for consistency
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(
                {
                    **file_info,
                    "unmatched_components": {
                        "handle": handle_unmatched,
                        "knot": knot_unmatched,
                    },
                }
            )
        # If neither handle nor knot issues, but still unmatched, show as general brush issue
        elif matched.get("brand") is None:
            # Use extract_text helper for consistency
            normalized = extract_text(brush, "brush")
            all_unmatched[normalized].append(file_info)

    def _strip_use_count(self, text: str) -> str:
        """Strip use count from blade text.

        This method is deprecated since normalization now happens in extraction.
        Returns the text as-is since it should already be normalized.
        """
        return text

    def _print_unmatched_results(self, all_unmatched: Dict, field: str, limit: int) -> None:
        """Print unmatched analysis results."""
        print(
            f"\n🔍 Found {len(all_unmatched)} unique unmatched {field} "
            f"descriptions across all files:\n"
        )
        # Sort alphabetically by value, then by file count descending
        for value, file_infos in sorted(
            all_unmatched.items(), key=lambda x: (x[0].lower(), -len(x[1]))
        )[:limit]:
            # Extract comment IDs for display
            comment_ids = [
                info.get("comment_id", "") for info in file_infos if info.get("comment_id")
            ]

            # Format comment IDs display
            if comment_ids:
                if len(comment_ids) <= 5:
                    comment_ids_text = ", ".join(comment_ids)
                else:
                    comment_ids_text = (
                        f"{', '.join(comment_ids[:5])}... (+{len(comment_ids) - 5} more)"
                    )
                print(f"{value:<60}  ({len(file_infos)} uses) - Comment IDs: {comment_ids_text}")
            else:
                print(f"{value:<60}  ({len(file_infos)} uses)")

            # Group by file and show line numbers
            file_lines = defaultdict(list)
            for file_info in file_infos:
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
