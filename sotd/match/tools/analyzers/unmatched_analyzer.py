#!/usr/bin/env python3
"""Unmatched analysis tool for SOTD pipeline."""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sotd.cli_utils.base_parser import BaseCLIParser  # noqa: E402
from sotd.match.tools.utils.analysis_base import AnalysisTool  # noqa: E402
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI  # noqa: E402
from sotd.utils.match_filter_utils import (
    clear_competition_tags_cache,
    normalize_for_matching,
)  # noqa: E402


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
        # Clear all caches to ensure fresh data
        clear_competition_tags_cache()

        # Clear other caches if available
        try:
            from sotd.match.base_matcher import clear_catalog_cache
            from sotd.match.loaders import clear_yaml_cache

            clear_yaml_cache()
            clear_catalog_cache()
        except ImportError:
            pass  # Cache clearing functions might not be available

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
            # Extract examples from source files (limit to 3 for API response)
            examples = []
            comment_ids = []
            for file_info in file_infos[:3]:  # Limit to 3 examples
                if isinstance(file_info, dict):
                    file_name = file_info.get("file", "")
                    if file_name:
                        examples.append(file_name)
                    comment_id = file_info.get("comment_id", "")
                    if comment_id:
                        comment_ids.append(comment_id)
                else:
                    # Backward compatibility for string file_info
                    examples.append(str(file_info))

            if args.field == "brush":
                # For brush field, return detailed structure with component information
                # Extract component-level unmatched data from file_infos
                handle_unmatched = None
                knot_unmatched = None

                # Look for component-level unmatched data in file_infos
                for info in file_infos:
                    if isinstance(info, dict) and "unmatched_components" in info:
                        components = info["unmatched_components"]
                        if components.get("handle") and not handle_unmatched:
                            handle_unmatched = components["handle"]
                        if components.get("knot") and not knot_unmatched:
                            knot_unmatched = components["knot"]

                # If we found component data, use it; otherwise use generic structure
                if handle_unmatched or knot_unmatched:
                    unmatched_items.append(
                        {
                            "item": original_text,
                            "count": len(file_infos),
                            "examples": examples,
                            "comment_ids": comment_ids,
                            "match_type": None,  # Unmatched items don't have match_type
                            "matched": None,  # Unmatched items don't have matched data
                            "unmatched": {
                                "handle": handle_unmatched
                                or {"text": original_text, "pattern": None},
                                "knot": knot_unmatched or {"text": original_text, "pattern": None},
                            },
                        }
                    )
                else:
                    # Use generic unmatched structure for brushes without component data
                    unmatched_items.append(
                        {
                            "item": original_text,
                            "count": len(file_infos),
                            "examples": examples,
                            "comment_ids": comment_ids,
                            "match_type": None,  # Unmatched items don't have match_type
                            "matched": None,  # Unmatched items don't have matched data
                            "unmatched": {
                                "handle": {"text": original_text, "pattern": None},
                                "knot": {"text": original_text, "pattern": None},
                            },
                        }
                    )
            else:
                # For other fields, return simple structure
                unmatched_items.append(
                    {
                        "item": original_text,
                        "count": len(file_infos),
                        "examples": examples,
                        "comment_ids": comment_ids,
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
            "comment_id": record.get("id", ""),
        }

        if isinstance(field_val, str):
            # Use standardized normalization for all fields
            normalized = normalize_for_matching(field_val, field=field)
            all_unmatched[normalized].append(file_info)
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
                    # Use normalized field if available, otherwise normalize original
                    normalized = field_val.get("normalized", "")
                    if not normalized:
                        original = field_val.get("original", "")
                        normalized = normalize_for_matching(original, field=field)
                    all_unmatched[normalized].append(file_info)

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
            "comment_id": record.get("id", ""),
        }

        # If nothing matched at all, count as unmatched brush
        if matched is None:
            # Use normalized field if available, otherwise normalize original
            normalized = brush.get("normalized", "")
            if not normalized:
                normalized = normalize_for_matching(original, field="brush")
            all_unmatched[normalized].append(file_info)
            return

        if not isinstance(matched, dict):
            # Use normalized field if available, otherwise normalize original
            normalized = brush.get("normalized", "")
            if not normalized:
                normalized = normalize_for_matching(original, field="brush")
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
            # Use normalized field if available, otherwise normalize original
            normalized = brush.get("normalized", "")
            if not normalized:
                normalized = normalize_for_matching(original, field="brush")
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
            # Use normalized field if available, otherwise normalize original
            normalized = brush.get("normalized", "")
            if not normalized:
                normalized = normalize_for_matching(original, field="brush")
            all_unmatched[normalized].append(file_info)

    def _strip_use_count(self, text: str) -> str:
        """Strip use count from blade text using shared normalization logic.

        This method uses the standardized normalize_for_matching function to ensure
        consistency with other blade processing in the pipeline.
        """
        return normalize_for_matching(text, field="blade")

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
