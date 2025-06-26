#!/usr/bin/env python3
"""Base classes and utilities for analysis tools."""

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.cli_utils.date_span import month_span


class AnalysisTool(ABC):
    """Base class for analysis tools with common functionality."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    @abstractmethod
    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for the analysis tool."""
        pass

    @abstractmethod
    def run(self, args) -> None:
        """Run the analysis tool."""
        pass

    def load_matched_data(self, args) -> List[Dict[str, Any]]:
        """Load matched data from files for the specified time period."""
        all_data = []

        for year, month in month_span(args):
            path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
            if path.exists():
                if args.debug:
                    print(f"Loading: {path}")

                with path.open("r", encoding="utf-8") as f:
                    content = json.load(f)
                data = content.get("data", [])

                for record in data:
                    record["_source_file"] = f"{year:04d}-{month:02d}.json"
                    record["_source_line"] = "unknown"

                all_data.extend(data)
            else:
                if args.debug:
                    print(f"Skipped (missing): {path}")

        return all_data

    def extract_field_data(
        self, data: List[Dict[str, Any]], field: str
    ) -> Tuple[List[Dict[str, Any]], List[str], List[float]]:
        """Extract field data, match types, and confidence scores from records."""
        field_matches = []
        match_types = []
        confidence_scores = []

        for record in data:
            field_data = record.get(field)
            if isinstance(field_data, dict):
                matched = field_data.get("matched")
                if matched:
                    field_matches.append(field_data)
                    match_types.append(field_data.get("match_type", ""))
                    confidence_scores.append(field_data.get("confidence", 0.0))

        return field_matches, match_types, confidence_scores

    def create_field_table(self, title: str, field: str) -> Table:
        """Create a standard table for field analysis."""
        table = Table(title=title)
        table.add_column(field.capitalize())
        table.add_column("Original")
        table.add_column("Match Type")
        table.add_column("Strategy")
        return table

    def format_field_name(self, field: str, matched: Dict[str, Any]) -> str:
        """Format field name based on field type."""
        if field == "soap":
            maker = matched.get("maker", "")
            scent = matched.get("scent", "")
            if maker and scent:
                return f"{maker} - {scent}"
            else:
                return maker or scent
        elif field == "razor":
            manufacturer = matched.get("manufacturer", "")
            model = matched.get("model", "")
            return f"{manufacturer} {model}".strip()
        elif field == "blade":
            return f"{matched.get('brand', '')} {matched.get('model', '')}".strip()
        elif field == "brush":
            return f"{matched.get('brand', '')} {matched.get('model', '')}".strip()
        else:
            return ""

    def analyze_regex_patterns(
        self, data: List[Dict[str, Any]], field: str, pattern: str, limit: int = 20
    ) -> None:
        """Analyze matched fields using regex patterns."""
        import re

        regex = re.compile(pattern, re.IGNORECASE)
        original_matches_exact_pattern = defaultdict(list)
        original_matches_other_pattern = defaultdict(list)

        for record in data:
            field_data = record.get(field)
            if isinstance(field_data, dict):
                original = field_data.get("original", "")
                pattern_val = field_data.get("pattern", "")
                source_file = record.get("_source_file", "")

                if isinstance(original, str) and regex.search(original):
                    if regex.pattern == pattern_val:
                        original_matches_exact_pattern[original].append(source_file)
                    else:
                        original_matches_other_pattern[(original, pattern_val)].append(source_file)

        print(
            f"\n🟢 Matched original {field} string AND pattern == regex "
            f"({len(original_matches_exact_pattern)} unique):\n"
        )
        for name, files in sorted(original_matches_exact_pattern.items(), key=lambda x: -len(x[1]))[
            :limit
        ]:
            print(f"{name:<60}  ({len(files)} uses)")
            for f in sorted(set(files)):
                print(f"    ↳ {f}")

        print(
            f"\n🟡 Matched original {field} string BUT pattern != regex "
            f"({len(original_matches_other_pattern)} unique):\n"
        )
        for (name, pat), files in sorted(
            original_matches_other_pattern.items(), key=lambda x: -len(x[1])
        )[:limit]:
            print(f"{name:<60}  (pattern: {pat})  ({len(files)} uses)")
            for f in sorted(set(files)):
                print(f"    ↳ {f}")
