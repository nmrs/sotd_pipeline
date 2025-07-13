#!/usr/bin/env python3
"""Mismatch identification tool for analyzing potential regex mismatches."""

import sys
from pathlib import Path

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import hashlib  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from typing import Dict, List, Optional, Set  # noqa: E402

import yaml  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from sotd.cli_utils.base_parser import BaseCLIParser  # noqa: E402
from sotd.match.tools.utils.analysis_base import AnalysisTool  # noqa: E402
from sotd.utils.match_filter_utils import (  # noqa: E402
    load_competition_tags,
    normalize_for_matching,
    strip_competition_tags,
)
from sotd.utils.yaml_loader import load_yaml_with_nfc  # noqa: E402


class MismatchAnalyzer(AnalysisTool):
    """Analyzer for identifying potential mismatches in matched data."""

    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.mismatch_indicators = {
            "multiple_patterns": "🔄",
            "levenshtein_distance": "📏",
            "low_confidence": "⚠️",
            "regex_match": "🔍",
            "potential_mismatch": "❌",
            "perfect_regex_matches": "✨",
        }
        self._catalog_patterns = {}  # Cache for catalog patterns
        self._catalog_cache_info = {}  # Cache metadata (timestamps, hashes)
        self._correct_matches_file = Path("data/correct_matches.yaml")
        self._correct_matches: Set[str] = set()
        self._compiled_patterns = {}  # Cache for compiled regex patterns
        self._correct_matches_data = {}  # Added for new _load_correct_matches method
        self._test_correct_matches_file = None  # For test file support

    def _escape_pattern_for_display(self, pattern: str) -> str:
        """Escape square brackets in patterns for Rich table display."""
        if not pattern:
            return pattern
        # Only escape opening brackets that Rich might interpret as formatting
        # Leave closing brackets unescaped for proper display
        return pattern.replace("[", "\\[")

    def _truncate_pattern_for_display(self, pattern: str, max_length: int = 80) -> str:
        """Truncate pattern for display if it's too long."""
        if not pattern or len(pattern) <= max_length:
            return pattern
        return pattern[: max_length - 3] + "..."

    def _get_table(self, title: str = "", expand: bool = False):
        """Lazy load Rich Table to reduce startup time."""
        return Table(title=title, expand=expand)

    def get_parser(self) -> BaseCLIParser:
        """Get CLI parser for mismatch analysis."""
        parser = BaseCLIParser(
            description="Analyze mismatches in matched data",
            add_date_args=False,
            add_output_args=False,
            add_debug_args=False,
            add_force_args=False,
            require_date_args=False,
        )

        # Add debug argument
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug output to show detailed processing information",
        )

        # Main arguments
        parser.add_argument(
            "--field",
            choices=["razor", "blade", "brush", "soap"],
            help="Field to analyze (razor, blade, brush, soap)",
        )
        parser.add_argument(
            "--month",
            help="Month to analyze (YYYY-MM format)",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=3,
            help="Levenshtein distance threshold for similarity (default: 3)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of mismatches to display (default: 50)",
        )
        parser.add_argument(
            "--show-all",
            action="store_true",
            help="Show all matches, not just mismatches",
        )
        parser.add_argument(
            "--show-unconfirmed",
            action="store_true",
            help="Show only unconfirmed matches (not exact or previously confirmed)",
        )
        parser.add_argument(
            "--show-regex-matches",
            action="store_true",
            help="Show only regex matches that haven't been confirmed (excludes unmatched)",
        )
        parser.add_argument(
            "--mark-correct",
            action="store_true",
            help="Mark displayed matches as correct (requires --force for safety)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be marked as correct without making changes",
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt (use with caution)",
        )
        parser.add_argument(
            "--clear-correct",
            action="store_true",
            help="Clear all correct matches",
        )
        parser.add_argument(
            "--clear-field",
            help="Clear correct matches for a specific field (razor, blade, brush, soap)",
        )
        parser.add_argument(
            "--show-correct",
            action="store_true",
            help="Show summary of correct matches by field",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh of pattern cache",
        )
        parser.add_argument(
            "--pattern-width",
            type=int,
            default=80,
            help="Maximum width for pattern display (default: 80)",
        )
        parser.add_argument(
            "--test-correct-matches",
            help="Use test correct_matches file instead of data/correct_matches.yaml",
        )

        return parser

    def run(self, args) -> None:
        """Run the mismatch analyzer."""
        # Handle special commands first
        if args.clear_correct:
            self._clear_correct_matches()
            return

        if args.clear_field:
            if args.clear_field not in ["razor", "blade", "brush", "soap"]:
                self.console.print(
                    "[red]Error: Invalid field. Must be razor, blade, brush, or soap[/red]"
                )
                return
            self._clear_correct_matches_by_field(args.clear_field)
            return

        if args.show_correct:
            self._display_correct_matches_summary()
            return

        # For analysis commands, field and month are required
        if not args.field:
            self.console.print("[red]Error: --field is required for analysis commands[/red]")
            return

        if not args.month:
            self.console.print("[red]Error: --month is required for analysis commands[/red]")
            return

        # Safety check: require --force when using --mark-correct
        if args.mark_correct and not args.force:
            self.console.print("[red]Error: --mark-correct requires --force for safety[/red]")
            self.console.print(
                "[yellow]Use --dry-run to preview what would be marked as correct[/yellow]"
            )
            return

        # Load correct matches
        self._load_correct_matches()

        # Set test correct matches file if specified
        if args.test_correct_matches:
            self._set_test_correct_matches_file(args.test_correct_matches)
            # Reload correct matches with test file
            self._load_correct_matches()

        # Clear cache if forced
        if args.force:
            self._clear_pattern_cache()

        # Load data using the parent class method to get _source_file field
        # Set up args.out_dir for the load_matched_data method
        if not hasattr(args, "out_dir"):
            args.out_dir = Path("data")
        if not hasattr(args, "debug"):
            args.debug = False

        try:
            records = self.load_matched_data(args)
            # Convert to the expected format with data wrapper
            data = {"data": records}
        except Exception as e:
            self.console.print(f"[red]Error loading data: {e}[/red]")
            return

        # Identify mismatches
        mismatches = self.identify_mismatches(data, args.field, args)

        # Display results
        if args.show_all:
            self.display_all_matches(data, args.field, mismatches, args)
        elif args.show_unconfirmed:
            self.display_unconfirmed_matches(data, args.field, args)
        elif args.show_regex_matches:
            self.display_regex_matches(data, args.field, args)
        else:
            self.display_mismatches(mismatches, args.field, args)

        # --- New summary output ---
        # Count confirmed and unconfirmed entries for the selected field
        records = data.get("data", [])
        total_confirmed = 0
        total_unconfirmed = 0
        total_exact_matches = 0

        # Debug: Track missing entries
        missing_entries = []
        confirmed_but_not_exact = []

        for record in records:
            field_data = record.get(args.field)
            if not isinstance(field_data, dict):
                continue
            original = field_data.get("original", "")
            matched = field_data.get("matched", {})
            match_type = field_data.get("match_type", "")
            if not original or not matched:
                continue

            # Count exact matches (from correct_matches.yaml)
            if match_type == "exact":
                total_exact_matches += 1
                total_confirmed += 1
                continue

            # Count other confirmed matches (from previous manual marking)
            match_key = self._create_match_key(args.field, original, matched)
            if match_key in self._correct_matches:
                total_confirmed += 1
                # Debug: Track confirmed but not exact matches
                if args.debug:
                    confirmed_but_not_exact.append(
                        {
                            "original": original,
                            "matched": matched,
                            "match_key": match_key,
                            "match_type": match_type,
                        }
                    )
            else:
                total_unconfirmed += 1
                # Debug: Track missing entries
                if args.debug:
                    missing_entries.append(
                        {
                            "original": original,
                            "matched": matched,
                            "match_key": match_key,
                            "match_type": match_type,
                        }
                    )

        self.console.print("\n[bold][Summary][/bold]")
        if total_exact_matches > 0:
            self.console.print(
                f"  • Matches with match_type='exact' (found via correct_matches.yaml): "
                f"[green]{total_exact_matches}[/green]"
            )
        if total_confirmed > total_exact_matches:
            self.console.print(
                f"  • Matches in correct_matches.yaml but not found as exact: "
                f"[yellow]{total_confirmed - total_exact_matches}[/yellow]"
            )
        self.console.print(
            f"  • Matches not in correct_matches.yaml: [yellow]{total_unconfirmed}[/yellow]"
        )

        # Debug: Show missing entries
        if args.debug and missing_entries:
            self.console.print(
                f"\n[blue]DEBUG: Found {len(missing_entries)} missing entries:[/blue]"
            )
            for i, entry in enumerate(missing_entries[:10]):  # Show first 10
                self.console.print(
                    f"[blue]DEBUG: Missing {i + 1}: Original='{entry['original']}', "
                    f"Matched={entry['matched']}, Type={entry['match_type']}, "
                    f"Key={entry['match_key']}[/blue]"
                )
            if len(missing_entries) > 10:
                self.console.print(f"[blue]DEBUG: ... and {len(missing_entries) - 10} more[/blue]")

        # Debug: Show confirmed but not exact matches
        if args.debug and confirmed_but_not_exact:
            self.console.print(
                f"\n[blue]DEBUG: Found {len(confirmed_but_not_exact)} "
                f"confirmed but not exact matches:[/blue]"
            )
            for i, entry in enumerate(confirmed_but_not_exact[:10]):  # Show first 10
                self.console.print(
                    f"[blue]DEBUG: Confirmed but not exact {i + 1}: "
                    f"Original='{entry['original']}', "
                    f"Matched={entry['matched']}, Type={entry['match_type']}, "
                    f"Key={entry['match_key']}[/blue]"
                )
            if len(confirmed_but_not_exact) > 10:
                self.console.print(
                    f"[blue]DEBUG: ... and {len(confirmed_but_not_exact) - 10} more[/blue]"
                )

        self.console.print("")

    def _clear_pattern_cache(self) -> None:
        """Clear all pattern caches."""
        self._catalog_patterns.clear()
        self._catalog_cache_info.clear()
        self._compiled_patterns.clear()

    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA-256 hash of file contents."""
        try:
            with file_path.open("rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _is_cache_valid(self, field: str, catalog_path: Path) -> bool:
        """Check if cached patterns are still valid for a field."""
        if field not in self._catalog_cache_info:
            return False

        cache_info = self._catalog_cache_info[field]

        # Check if file still exists
        if not catalog_path.exists():
            return False

        # Check modification time
        current_mtime = catalog_path.stat().st_mtime
        if current_mtime != cache_info.get("mtime"):
            return False

        # Check file hash
        current_hash = self._get_file_hash(catalog_path)
        if current_hash != cache_info.get("hash"):
            return False

        return True

    def _update_cache_info(self, field: str, catalog_path: Path) -> None:
        """Update cache metadata for a field."""
        try:
            mtime = catalog_path.stat().st_mtime
            file_hash = self._get_file_hash(catalog_path)

            self._catalog_cache_info[field] = {
                "mtime": mtime,
                "hash": file_hash,
                "last_updated": time.time(),
            }
        except Exception as e:
            self.console.print(
                f"[yellow]Warning: Could not update cache info for {field}: {e}[/yellow]"
            )

    def identify_mismatches(self, data: Dict, field: str, args) -> Dict[str, List[Dict]]:
        """Identify potential mismatches in the data for a given field."""
        mismatches = {
            "multiple_patterns": [],
            "levenshtein_distance": [],
            "low_confidence": [],
            "exact_matches": [],
            "perfect_regex_matches": [],
        }

        # Extract the actual records from the data structure
        records = data.get("data", [])
        if not records:
            self.console.print("[yellow]No records found in data[/yellow]")
            return mismatches

        # Debug: Show correct matches loading info
        if args.debug:
            self.console.print(
                f"[blue]DEBUG: Loaded {len(self._correct_matches)} correct matches[/blue]"
            )
            self.console.print(
                f"[blue]DEBUG: Processing {len(records)} records for field '{field}'[/blue]"
            )

            # Show some examples of correct match keys
            correct_keys = list(self._correct_matches)[:5]
            for key in correct_keys:
                self.console.print(f"[blue]DEBUG: Correct match key example: {key}[/blue]")

            # Debug: Show blade-specific correct match keys
            if field == "blade":
                blade_keys = [k for k in self._correct_matches if k.startswith("blade:")]
                self.console.print(
                    f"[blue]DEBUG: Found {len(blade_keys)} blade-specific correct match keys[/blue]"
                )
                for key in blade_keys[:5]:
                    self.console.print(f"[blue]DEBUG: Blade correct match key: {key}[/blue]")

        # Sort records by a stable key for deterministic processing order
        # Use the original text as the primary sort key, with record ID as secondary
        def record_sort_key(record):
            field_data = record.get(field, {})
            original = field_data.get("original", "")
            record_id = record.get("id", "")
            return (original.lower(), record_id)

        sorted_records = sorted(records, key=record_sort_key)

        # Pre-load catalog patterns to avoid repeated loading
        catalog_patterns = self._load_catalog_patterns(field)

        for record in sorted_records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue

            original = field_data.get("original", "")
            matched = field_data.get("matched", {})
            pattern = field_data.get("pattern", "")
            match_type = field_data.get("match_type", "")
            confidence = field_data.get("confidence", 1.0)

            if not original or not matched:
                continue

            # Debug: Show processing info for first few records
            if (
                args.debug
                and len(mismatches["exact_matches"])
                + len(mismatches["multiple_patterns"])
                + len(mismatches["levenshtein_distance"])
                < 10
            ):
                match_key = self._create_match_key(field, original, matched)
                self.console.print(
                    f"[blue]DEBUG: Processing record - Original: '{original}', "
                    f"Match type: {match_type}, Match key: {match_key}[/blue]"
                )
                if match_key in self._correct_matches:
                    self.console.print("[green]DEBUG: Found in correct matches[/green]")
                else:
                    self.console.print("[yellow]DEBUG: NOT found in correct matches[/yellow]")

            # Skip exact matches (from correct_matches.yaml) - these are already confirmed correct
            if match_type == "exact":
                mismatches["exact_matches"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": self._create_match_key(field, original, matched),
                        "reason": "Exact match from correct_matches.yaml",
                    }
                )
                continue  # Skip further analysis for exact matches

            # Create a unique key for this match
            match_key = self._create_match_key(field, original, matched)

            # Skip if this match was previously marked as correct (unless showing correct matches)
            if match_key in self._correct_matches and not args.show_correct:
                continue

            # Check for multiple regex patterns (only if we have catalog patterns)
            if catalog_patterns:
                multiple_patterns = self._find_multiple_pattern_matches_fast(
                    original, field, pattern, catalog_patterns
                )
                if multiple_patterns:
                    pattern_list = ", ".join(multiple_patterns[:3])
                    mismatches["multiple_patterns"].append(
                        {
                            "record": record,
                            "field_data": field_data,
                            "match_key": match_key,
                            "reason": f"Matches {len(multiple_patterns)} patterns: {pattern_list}",
                        }
                    )

            # Check Levenshtein distance (for non-exact matches only)
            matched_text = self._get_matched_text(field, matched)
            if self._levenshtein_distance_exceeds_threshold(original, matched_text, args.threshold):
                mismatches["levenshtein_distance"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": match_key,
                        "reason": "High Levenshtein distance",
                    }
                )

            # Check for perfect regex matches when threshold is 0
            # (to help populate correct_matches.yaml)
            if args.threshold == 0 and match_type == "regex":
                # Check if this is a perfect or near-perfect match (Levenshtein distance <= 2)
                distance = self._levenshtein_distance(original, matched_text)
                if distance <= 2:
                    reason = (
                        "Perfect regex match (threshold 0)"
                        if distance == 0
                        else f"Near-perfect regex match (distance {distance})"
                    )
                    mismatches["perfect_regex_matches"].append(
                        {
                            "record": record,
                            "field_data": field_data,
                            "match_key": match_key,
                            "reason": reason,
                        }
                    )

            # Check confidence scores (if confidence field exists)
            if hasattr(args, "confidence_threshold") and confidence < args.confidence_threshold:
                mismatches["low_confidence"].append(
                    {
                        "record": record,
                        "field_data": field_data,
                        "match_key": match_key,
                        "reason": f"Low confidence: {confidence:.2f}",
                    }
                )

        return mismatches

    def _create_match_key(self, field: str, original: str, matched: Dict) -> str:
        """Create a unique key for a match based on field, original text, and matched data."""
        # Handle None matched data
        if matched is None:
            matched = {}

        # Use format-free matched text for consistency with correct_matches.yaml storage
        if field == "soap":
            maker = matched.get("maker", "")
            scent = matched.get("scent", "")
            matched_text = f"{maker} {scent}".strip()
        elif field in ["razor", "blade"]:
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            matched_text = f"{brand} {model}".strip()
        elif field == "brush":
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            matched_text = f"{brand} {model}".strip()
        else:
            matched_text = str(matched)

        # Normalize for consistent key generation - use normalized original to match storage format
        original_normalized = normalize_for_matching(original, None, field=field).lower().strip()
        matched_normalized = matched_text.lower().strip()
        return f"{field}:{original_normalized}|{matched_normalized}"

    def _load_correct_matches(self) -> None:
        """Load previously marked correct matches from file."""
        self._correct_matches = set()
        self._correct_matches_data = {}
        if not self._get_correct_matches_file().exists():
            return

        try:
            with self._get_correct_matches_file().open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return
                for field, field_data in data.items():
                    if isinstance(field_data, dict):
                        if field == "blade":
                            # Handle format-first structure for blade field
                            for format_name, format_data in field_data.items():
                                if isinstance(format_data, dict):
                                    for brand, brand_data in format_data.items():
                                        if isinstance(brand_data, dict):
                                            for model, strings in brand_data.items():
                                                if isinstance(strings, list):
                                                    for original in strings:
                                                        brand_model = f"{brand} {model}"
                                                        match_key = (
                                                            f"{field}:{original.lower().strip()}|"
                                                            f"{brand_model.lower().strip()}"
                                                        )
                                                        self._correct_matches.add(match_key)
                                                        self._correct_matches_data[match_key] = {
                                                            "original": original,
                                                            "matched": {
                                                                "brand": brand,
                                                                "model": model,
                                                                "format": format_name,
                                                            },
                                                            "field": field,
                                                        }
                        else:
                            # Handle brand-first structure for other fields
                            for brand, brand_data in field_data.items():
                                if isinstance(brand_data, dict):
                                    for model, strings in brand_data.items():
                                        if isinstance(strings, list):
                                            for original in strings:
                                                brand_model = f"{brand} {model}"
                                                match_key = (
                                                    f"{field}:{original.lower().strip()}|"
                                                    f"{brand_model.lower().strip()}"
                                                )
                                                self._correct_matches.add(match_key)
                                                self._correct_matches_data[match_key] = {
                                                    "original": original,
                                                    "matched": {
                                                        "brand": (
                                                            brand
                                                            if field in ("razor", "blade", "brush")
                                                            else None
                                                        ),
                                                        "model": (
                                                            model
                                                            if field in ("razor", "blade", "brush")
                                                            else None
                                                        ),
                                                        "maker": brand if field == "soap" else None,
                                                        "scent": model if field == "soap" else None,
                                                    },
                                                    "field": field,
                                                }
        except (yaml.YAMLError, KeyError) as e:
            self.console.print(f"[yellow]Warning: Could not load correct matches: {e}[/yellow]")
            self._correct_matches = set()
            self._correct_matches_data = {}

    def _load_competition_tags(self) -> Dict[str, List[str]]:
        """Load competition tags configuration."""
        return load_competition_tags()

    def _strip_competition_tags(self, value: str, competition_tags: Dict[str, List[str]]) -> str:
        """
        Strip competition tags from a string while preserving useful ones.

        Args:
            value: Input string that may contain competition tags
            competition_tags: Configuration of tags to strip/preserve

        Returns:
            String with unwanted competition tags removed
        """
        return strip_competition_tags(value, competition_tags)

    def _normalize_for_matching(self, value: str, field: str) -> str:
        """
        Normalize a string for storage in correct_matches.yaml.

        This strips competition tags and normalizes whitespace to prevent
        bloat and duplicates in the file.
        """
        return normalize_for_matching(value, None, field)

    def _save_correct_matches(self) -> None:
        """Save correct matches to file in YAML format."""
        try:
            # Create backup before modifying
            if self._get_correct_matches_file().exists():
                backup_path = self._get_correct_matches_file().with_suffix(".yaml.backup")
                import shutil

                shutil.copy2(self._get_correct_matches_file(), backup_path)
                self.console.print(f"[dim]Backup created: {backup_path}[/dim]")

            # Ensure directory exists
            self._get_correct_matches_file().parent.mkdir(parents=True, exist_ok=True)

            # Organize matches hierarchically based on field type
            yaml_data = {}
            for match_key, stored_data in self._correct_matches_data.items():
                field = stored_data.get("field")
                original = stored_data.get("original")
                matched_dict = stored_data.get("matched", {})

                if field == "blade":
                    # Use format-first structure for blade field
                    canonical_format = matched_dict.get("format", "DE")  # Default to DE
                    canonical_brand = matched_dict.get("brand", "")
                    canonical_model = matched_dict.get("model", "")

                    canonical_format = canonical_format.strip()
                    canonical_brand = canonical_brand.strip()
                    canonical_model = canonical_model.strip()

                    if field not in yaml_data:
                        yaml_data[field] = {}
                    if canonical_format not in yaml_data[field]:
                        yaml_data[field][canonical_format] = {}
                    if canonical_brand not in yaml_data[field][canonical_format]:
                        yaml_data[field][canonical_format][canonical_brand] = {}
                    if canonical_model not in yaml_data[field][canonical_format][canonical_brand]:
                        yaml_data[field][canonical_format][canonical_brand][canonical_model] = []

                    # Normalize the original string before storing to prevent bloat
                    normalized_original = normalize_for_matching(original, None, field)
                    if (
                        normalized_original
                        and normalized_original
                        not in yaml_data[field][canonical_format][canonical_brand][canonical_model]
                    ):
                        yaml_data[field][canonical_format][canonical_brand][canonical_model].append(
                            normalized_original
                        )

                elif field in ("razor", "brush"):
                    # Use brand-first structure for razor and brush fields
                    canonical_brand = matched_dict.get("brand", "")
                    canonical_model = matched_dict.get("model", "")

                    canonical_brand = canonical_brand.strip()
                    canonical_model = canonical_model.strip()

                    if field not in yaml_data:
                        yaml_data[field] = {}
                    if canonical_brand not in yaml_data[field]:
                        yaml_data[field][canonical_brand] = {}
                    if canonical_model not in yaml_data[field][canonical_brand]:
                        yaml_data[field][canonical_brand][canonical_model] = []

                    # Normalize the original string before storing to prevent bloat
                    normalized_original = normalize_for_matching(original, None, field)
                    if (
                        normalized_original
                        and normalized_original
                        not in yaml_data[field][canonical_brand][canonical_model]
                    ):
                        yaml_data[field][canonical_brand][canonical_model].append(
                            normalized_original
                        )

                elif field == "soap":
                    # Use brand-first structure for soap field
                    canonical_brand = matched_dict.get("maker", "")
                    canonical_model = matched_dict.get("scent", "")

                    canonical_brand = canonical_brand.strip()
                    canonical_model = canonical_model.strip()

                    if field not in yaml_data:
                        yaml_data[field] = {}
                    if canonical_brand not in yaml_data[field]:
                        yaml_data[field][canonical_brand] = {}
                    if canonical_model not in yaml_data[field][canonical_brand]:
                        yaml_data[field][canonical_brand][canonical_model] = []

                    # Normalize the original string before storing to prevent bloat
                    normalized_original = normalize_for_matching(original, None, field)
                    if (
                        normalized_original
                        and normalized_original
                        not in yaml_data[field][canonical_brand][canonical_model]
                    ):
                        yaml_data[field][canonical_brand][canonical_model].append(
                            normalized_original
                        )
                else:
                    continue

            # Alphabetize entries within each field/brand/model (or field/format/brand/model)
            for field, field_data in yaml_data.items():
                if isinstance(field_data, dict):
                    if field == "blade":
                        # For blade field, sort by format -> brand -> model
                        for format_name, format_data in field_data.items():
                            if isinstance(format_data, dict):
                                for brand, brand_data in format_data.items():
                                    if isinstance(brand_data, dict):
                                        for model, entries in brand_data.items():
                                            if isinstance(entries, list):
                                                # Sort entries alphabetically (case-insensitive)
                                                entries.sort(key=str.lower)
                    else:
                        # For other fields, sort by brand -> model
                        for brand, brand_data in field_data.items():
                            if isinstance(brand_data, dict):
                                for model, entries in brand_data.items():
                                    if isinstance(entries, list):
                                        # Sort entries alphabetically (case-insensitive)
                                        entries.sort(key=str.lower)

            with self._get_correct_matches_file().open("w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, indent=2, allow_unicode=True)
        except Exception as e:
            self.console.print(f"[red]Error saving correct matches: {e}[/red]")

    def _get_correct_matches_by_field(self, field: str) -> Set[str]:
        """Get correct matches for a specific field."""
        field_matches = set()
        for match_key in self._correct_matches:
            if match_key.startswith(f"{field}:"):
                field_matches.add(match_key)
        return field_matches

    def _display_correct_matches_summary(self) -> None:
        """Display summary of correct matches by field."""
        if not self._correct_matches:
            return

        # Count by field
        field_counts = {}
        for match_key in self._correct_matches:
            if ":" in match_key:
                field = match_key.split(":", 1)[0]
                field_counts[field] = field_counts.get(field, 0) + 1

        self.console.print("[dim]Correct matches by field:[/dim]")
        for field, count in sorted(field_counts.items()):
            self.console.print(f"[dim]  • {field}: {count}[/dim]")
        self.console.print(f"[dim]  • Total: {len(self._correct_matches)}[/dim]")

    def _clear_correct_matches(self) -> None:
        """Clear all correct matches."""
        self._correct_matches = set()
        if self._get_correct_matches_file().exists():
            self._get_correct_matches_file().unlink()
        self.console.print("[green]Cleared all correct matches[/green]")

    def _clear_correct_matches_by_field(self, field: str) -> None:
        """Clear correct matches for a specific field."""
        field_matches = self._get_correct_matches_by_field(field)
        for match_key in field_matches:
            self._correct_matches.discard(match_key)

        if field_matches:
            self._save_correct_matches()
            self.console.print(
                f"[green]Cleared {len(field_matches)} correct matches for {field}[/green]"
            )
        else:
            self.console.print(f"[yellow]No correct matches found for {field}[/yellow]")

    def _find_multiple_pattern_matches_fast(
        self, original: str, field: str, current_pattern: str, catalog_patterns: List[Dict]
    ) -> List[str]:
        """Fast version of multiple pattern matching using pre-loaded patterns."""
        # Group patterns by product to avoid counting multiple patterns for the same product
        product_matches = {}

        # Check all patterns and group by product
        for pattern_info in catalog_patterns:
            pattern_text = pattern_info.get("pattern", "")
            if not pattern_text:
                continue

            # Use cached compiled pattern
            compiled_pattern = self._get_compiled_pattern(pattern_text)
            if not compiled_pattern:
                continue

            try:
                if compiled_pattern.search(original):
                    # Create a product key based on the field type
                    product_key = self._get_product_key(pattern_info, field)
                    if product_key not in product_matches:
                        product_matches[product_key] = []
                    product_matches[product_key].append(pattern_text)
            except Exception:
                # Skip invalid regex patterns
                continue

        # Only return patterns if we have matches for multiple different products
        if len(product_matches) > 1:
            # Flatten the patterns from all products
            all_patterns = []
            for patterns in product_matches.values():
                all_patterns.extend(patterns)
            return all_patterns

        return []

    def _get_compiled_pattern(self, pattern_text: str):
        """Get or create a compiled regex pattern."""
        if pattern_text not in self._compiled_patterns:
            try:
                self._compiled_patterns[pattern_text] = re.compile(pattern_text, re.IGNORECASE)
            except re.error:
                # Skip invalid patterns
                return None
        return self._compiled_patterns[pattern_text]

    def _get_product_key(self, pattern_info: Dict, field: str) -> str:
        """Create a unique key for a product based on its identifying information."""
        if field == "soap":
            maker = pattern_info.get("maker", "")
            scent = pattern_info.get("scent", "")
            return f"{maker}|{scent}"
        else:
            brand = pattern_info.get("brand", "")
            model = pattern_info.get("model", "")
            return f"{brand}|{model}"

    def _load_catalog_patterns(self, field: str) -> List[Dict]:
        """Load all patterns from the catalog for a given field."""
        # Map field names to catalog files
        field_to_catalog = {
            "razor": "razors.yaml",
            "blade": "blades.yaml",
            "brush": "brushes.yaml",
            "soap": "soaps.yaml",
        }

        catalog_file = field_to_catalog.get(field)
        if not catalog_file:
            self._catalog_patterns[field] = []
            return []

        catalog_path = Path("data") / catalog_file
        if not catalog_path.exists():
            self._catalog_patterns[field] = []
            return []

        # Check if cache is valid
        if self._is_cache_valid(field, catalog_path):
            return self._catalog_patterns[field]

        # Cache is invalid or doesn't exist, reload
        self.console.print(f"[dim]Reloading patterns for {field} (cache invalid)[/dim]")

        try:
            catalog_data = load_yaml_with_nfc(catalog_path)
            patterns = self._extract_patterns_from_catalog(catalog_data, field)
            self._catalog_patterns[field] = patterns

            # Update cache metadata
            self._update_cache_info(field, catalog_path)

            # Pre-compile patterns for this field
            for pattern_info in patterns:
                pattern_text = pattern_info.get("pattern", "")
                if pattern_text:
                    self._get_compiled_pattern(pattern_text)

            return patterns
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not load catalog for {field}: {e}[/yellow]")
            self._catalog_patterns[field] = []
            return []

    def _extract_patterns_from_catalog(self, catalog_data: Dict, field: str) -> List[Dict]:
        """Extract all patterns from catalog data."""
        patterns = []

        if not isinstance(catalog_data, dict):
            return patterns

        # Extract patterns based on field type
        if field == "soap":
            # Soap catalog has maker -> scent -> patterns structure
            for maker, maker_data in catalog_data.items():
                if isinstance(maker_data, dict) and "scents" in maker_data:
                    for scent, scent_data in maker_data["scents"].items():
                        if isinstance(scent_data, dict) and "patterns" in scent_data:
                            for pattern in scent_data["patterns"]:
                                patterns.append(
                                    {
                                        "pattern": pattern,
                                        "maker": maker,
                                        "scent": scent,
                                    }
                                )
        elif field == "blade":
            # New format-first structure: format -> brand -> model -> patterns
            for format_name, brands in catalog_data.items():
                if isinstance(brands, dict):
                    for brand, models in brands.items():
                        if isinstance(models, dict):
                            for model, model_data in models.items():
                                if isinstance(model_data, dict) and "patterns" in model_data:
                                    for pattern in model_data["patterns"]:
                                        patterns.append(
                                            {
                                                "pattern": pattern,
                                                "brand": brand,
                                                "model": model,
                                                "format": format_name,
                                            }
                                        )
        else:
            # Other catalogs have brand -> model -> patterns structure
            for brand, brand_data in catalog_data.items():
                if isinstance(brand_data, dict):
                    for model, model_data in brand_data.items():
                        if isinstance(model_data, dict) and "patterns" in model_data:
                            for pattern in model_data["patterns"]:
                                patterns.append(
                                    {
                                        "pattern": pattern,
                                        "brand": brand,
                                        "model": model,
                                    }
                                )

        return patterns

    def _levenshtein_distance_exceeds_threshold(
        self, original: str, matched: str, threshold: int
    ) -> bool:
        """Check if Levenshtein distance exceeds threshold."""
        distance = self._levenshtein_distance(original.lower(), matched.lower())
        return distance > threshold

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _get_matched_text(self, field: str, matched: Dict) -> str:
        """Extract text representation of matched data."""
        if matched is None:
            return ""

        if field == "soap":
            maker = matched.get("maker", "")
            scent = matched.get("scent", "")
            return f"{maker} {scent}".strip()
        elif field == "razor":
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            format_info = matched.get("format", "")
            if format_info:
                return f"{brand} {model} ({format_info})".strip()
            else:
                return f"{brand} {model}".strip()
        elif field == "blade":
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            format_info = matched.get("format", "")
            if format_info:
                return f"{brand} {model} ({format_info})".strip()
            else:
                return f"{brand} {model}".strip()
        elif field == "brush":
            brand = matched.get("brand", "")
            model = matched.get("model", "")
            return f"{brand} {model}".strip()
        else:
            return str(matched)

    def _group_duplicate_mismatches(
        self, mismatches: Dict[str, List[Dict]], field: str
    ) -> List[Dict]:
        """Group duplicate mismatches and add count information."""
        grouped_mismatches = []

        # Sort mismatch types for deterministic order
        for mismatch_type in sorted(mismatches.keys()):
            if mismatch_type == "exact_matches":
                continue  # Skip exact matches in mismatch display

            items = mismatches[mismatch_type]
            # Group by the key information that makes a mismatch unique
            groups = {}

            for item in items:
                field_data = item["field_data"]
                original = field_data.get("original", "")
                norm_original = normalize_for_matching(original, None, field=field)
                matched = self._get_matched_text(field, field_data.get("matched", {}))
                # Group by the actual match, not by mismatch type, case-insensitive
                group_key = (norm_original.lower(), matched.lower())

                if group_key not in groups:
                    groups[group_key] = {"count": 0, "item": item, "sources": set()}

                groups[group_key]["count"] += 1
                source = item["record"].get("_source_file", "")
                if source:
                    groups[group_key]["sources"].add(source)

            # Convert groups to list format with deterministic sorting
            for group_key in sorted(groups.keys()):
                group_info = groups[group_key]
                norm_original, matched = group_key

                # Create a modified item with count information
                modified_item = group_info["item"].copy()
                modified_item["count"] = group_info["count"]
                # Sort sources for deterministic order
                modified_item["sources"] = sorted(list(group_info["sources"]))
                modified_item["mismatch_type"] = mismatch_type

                grouped_mismatches.append(modified_item)

        return grouped_mismatches

    def display_mismatches(self, mismatches: Dict[str, List[Dict]], field: str, args) -> None:
        """Display identified mismatches in a formatted table, normalized and grouped."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        mismatch_keys = [
            "multiple_patterns",
            "levenshtein_distance",
            "low_confidence",
            "perfect_regex_matches",
        ]
        total_mismatches = sum(len(mismatches[key]) for key in mismatch_keys)
        exact_matches_count = len(mismatches.get("exact_matches", []))

        if total_mismatches == 0:
            if exact_matches_count > 0:
                self.console.print(
                    f"[green]✅ No potential mismatches found for {field} "
                    f"(skipped {exact_matches_count} exact matches from "
                    f"correct_matches.yaml)[/green]"
                )
            else:
                self.console.print(f"[green]✅ No potential mismatches found for {field}[/green]")
            return

        # Group duplicate mismatches by normalized original and matched
        # (not by mismatch type), case-insensitive
        grouped = {}
        for mismatch_type in mismatch_keys:
            for item in mismatches[mismatch_type]:
                field_data = item["field_data"]
                original = field_data.get("original", "")
                norm_original = normalize_for_matching(original, None, field=field)
                matched = self._get_matched_text(field, field_data.get("matched", {}))
                reason = item["reason"]

                # Group by the actual match, not by mismatch type, case-insensitive
                group_key = (norm_original.lower(), matched.lower())
                if group_key not in grouped:
                    grouped[group_key] = {
                        "record_ids": set(),
                        "item": item,
                        "sources": set(),
                        "mismatch_types": set(),
                        "reasons": set(),
                        "comment_ids": set(),
                    }
                record_id = item["record"].get("id", "")
                if record_id:
                    grouped[group_key]["record_ids"].add(record_id)
                grouped[group_key]["mismatch_types"].add(mismatch_type)
                grouped[group_key]["reasons"].add(reason)
                source = item["record"].get("_source_file", "")
                if source:
                    grouped[group_key]["sources"].add(source)
                comment_id = item["record"].get("id", "")
                if comment_id:
                    grouped[group_key]["comment_ids"].add(comment_id)

        # Convert groups to list format with deterministic sorting
        grouped_mismatches = []
        # Define priority order
        priority = [
            "multiple_patterns",
            "levenshtein_distance",
            "low_confidence",
            "perfect_regex_matches",
        ]
        for group_key in sorted(grouped.keys()):
            group_info = grouped[group_key]
            norm_original, matched = group_key
            modified_item = group_info["item"].copy()
            modified_item["count"] = len(group_info["record_ids"])
            modified_item["sources"] = sorted(list(group_info["sources"]))
            modified_item["comment_ids"] = sorted(list(group_info["comment_ids"]))
            # Choose the highest priority mismatch type present
            mismatch_types = sorted(list(group_info["mismatch_types"]))
            for p in priority:
                if p in mismatch_types:
                    modified_item["mismatch_type"] = p
                    break
            else:
                modified_item["mismatch_type"] = mismatch_types[0] if mismatch_types else ""
            modified_item["norm_original"] = norm_original
            # Combine all reasons
            reasons = sorted(list(group_info["reasons"]))
            modified_item["reason"] = "; ".join(reasons)
            grouped_mismatches.append(modified_item)
        unique_count = len(grouped_mismatches)

        # Show info about exact matches being skipped
        if exact_matches_count > 0:
            self.console.print(
                f"[dim]ℹ️  Skipped {exact_matches_count} exact matches from "
                f"correct_matches.yaml[/dim]"
            )

        self.console.print(
            f"\n[bold]Potential Mismatches for {field.capitalize()} "
            f"({total_mismatches} total, {unique_count} unique):[/bold]\n"
        )

        # Create table for mismatches
        table = self._get_table(title=f"Potential Mismatches - {field.capitalize()}", expand=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Count", style="magenta", justify="center")
        table.add_column("Type", style="cyan")
        table.add_column("Original", style="yellow")
        table.add_column("Normalized", style="blue")
        table.add_column("Matched", style="green")
        table.add_column("Pattern", style="blue")
        table.add_column("Reason", style="red")
        table.add_column("Comment IDs", style="dim")
        table.add_column("Sources", style="dim")

        # Get limits and filters with defaults
        limit = getattr(args, "limit", 50)

        displayed_items = []
        row_number = 1

        for item in grouped_mismatches[:limit]:
            field_data = item["field_data"]
            mismatch_type = item["mismatch_type"]
            count = item["count"]
            sources = item["sources"]
            comment_ids = item["comment_ids"]

            norm_original = item["norm_original"]
            matched = self._get_matched_text(field, field_data.get("matched", {}))
            reason = item["reason"]

            # Get the actual regex pattern from field_data
            pattern = field_data.get("pattern", "")
            # Escape pattern for Rich table display
            pattern = self._escape_pattern_for_display(pattern)
            # No truncation, let it wrap

            # Add visual indicator
            indicator = self.mismatch_indicators.get(mismatch_type, "❓")
            type_text = f"{indicator} {mismatch_type.replace('_', ' ').title()}"

            # Format count with multiplier
            count_text = str(count)

            # Format sources
            sources_text = ", ".join(sources) if sources else ""

            # Format comment IDs (show first few, then count)
            if comment_ids:
                if len(comment_ids) <= 3:
                    comment_ids_text = ", ".join(comment_ids)
                else:
                    joined_ids = ", ".join(comment_ids[:3])
                    comment_ids_text = f"{joined_ids}... (+{len(comment_ids) - 3} more)"
                # Debug: Show actual comment IDs for first few items
                if row_number <= 3:
                    debug_msg = (
                        f"[dim]DEBUG: Row {row_number} - Count: {count}, "
                        f"Comment IDs: {comment_ids}[/dim]"
                    )
                    self.console.print(debug_msg)
            else:
                comment_ids_text = ""

            # Create row data based on field type
            table.add_row(
                str(row_number),
                count_text,
                type_text,
                field_data.get("original", ""),  # Original: exact string from matched data
                norm_original,  # Normalized: normalized version
                matched,
                pattern,
                reason,
                comment_ids_text,
                sources_text,
            )
            table.add_row("", "", "", "", "", "", "", "", "", "")  # Blank row for spacing
            displayed_items.append(item)
            row_number += 1

        self.console.print(table)

        # Print total unique records in displayed mismatches
        total_unique_records = sum(item["count"] for item in grouped_mismatches[:limit])
        self.console.print(
            f"[bold]Total unique records in displayed mismatches: {total_unique_records}[/bold]"
        )

        # Handle mark-correct functionality
        if getattr(args, "mark_correct", False) and total_mismatches > 0:
            self._mark_displayed_matches_as_correct(displayed_items, field, args)
        elif getattr(args, "dry_run", False) and total_mismatches > 0:
            self._preview_mark_correct(displayed_items, field, args)

    def display_all_matches(
        self, data: Dict, field: str, mismatches: Dict[str, List[Dict]], args
    ) -> None:
        """Display all matches with mismatch indicators, normalized and grouped."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        self.console.print(
            f"\n[bold]All {field.capitalize()} Matches with Mismatch Indicators:[/bold]\n"
        )

        table = self._get_table(title=f"All Matches - {field.capitalize()}", expand=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Count", style="magenta", justify="center")
        table.add_column("Status", style="cyan")
        table.add_column("Original", style="yellow")
        table.add_column("Matched", style="green")
        table.add_column("Pattern", style="blue")
        table.add_column("Match Type", style="magenta")
        table.add_column("Correct", style="dim")
        table.add_column("Comment IDs", style="dim")
        table.add_column("Source", style="dim")

        # Create lookup for mismatches
        mismatch_lookup = {}
        for mismatch_type, items in mismatches.items():
            for item in items:
                record_id = item["record"].get("id", "")
                mismatch_lookup[record_id] = (mismatch_type, item["reason"])

        # Track displayed matches for mark-correct functionality
        displayed_matches = []

        # Get limit with default
        limit = getattr(args, "limit", 50)
        records = data.get("data", [])

        # Group by normalized original, matched_text, pattern, match_type
        grouped = {}
        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue
            original = field_data.get("original", "")
            norm_original = normalize_for_matching(original, None, field)
            matched = field_data.get("matched", {})
            matched_text = self._get_matched_text(field, matched)
            pattern = field_data.get("pattern", "")
            match_type = field_data.get("match_type", "")
            source = record.get("_source_file", "")
            record_id = record.get("id", "")
            key = (norm_original, matched_text, pattern, match_type)
            if key not in grouped:
                grouped[key] = {
                    "count": 0,
                    "field_data": field_data,
                    "matched_text": matched_text,
                    "pattern": pattern,
                    "match_type": match_type,
                    "source": source,
                    "record_ids": set(),
                    "comment_ids": set(),
                }
            grouped[key]["count"] += 1
            grouped[key]["record_ids"].add(record_id)
            if record_id:
                grouped[key]["comment_ids"].add(record_id)

        # Sort groups for deterministic display order
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: (x[0][0] or "", x[0][1] or "", x[0][2] or "", x[0][3] or ""),
        )

        row_number = 1
        for (norm_original, matched_text, pattern, match_type), group in sorted_groups[:limit]:
            count = group["count"]
            field_data = group["field_data"]
            source = group["source"]
            comment_ids = sorted(list(group["comment_ids"]))
            # Escape pattern for Rich table display
            pattern_disp = self._escape_pattern_for_display(pattern)
            # No truncation, let it wrap
            # Check if this match was previously marked as correct
            match_key = self._create_match_key(field, norm_original, field_data.get("matched", {}))
            is_correct = match_key in self._correct_matches
            correct_indicator = "✅" if is_correct else ""
            # Determine status and indicator
            # Use the first record_id in the group for mismatch lookup
            record_id = next(iter(group["record_ids"])) if group["record_ids"] else ""
            if record_id in mismatch_lookup:
                mismatch_type, reason = mismatch_lookup[record_id]
                indicator = self.mismatch_indicators.get(mismatch_type, "❓")
                status = f"{indicator} {mismatch_type.replace('_', ' ').title()}"
            elif match_type == "exact":
                status = f"{self.mismatch_indicators['regex_match']} Regex Match"
            else:
                status = f"{self.mismatch_indicators['potential_mismatch']} Potential Mismatch"

            # Format comment IDs (show first few, then count)
            if comment_ids:
                if len(comment_ids) <= 3:
                    comment_ids_text = ", ".join(comment_ids)
                else:
                    comment_ids_text = (
                        f"{', '.join(comment_ids[:3])}... (+{len(comment_ids) - 3} more)"
                    )
            else:
                comment_ids_text = ""

            # Create row data based on field type
            table.add_row(
                str(row_number),
                str(count),
                status,
                norm_original,
                matched_text,
                pattern_disp,
                match_type,
                correct_indicator,
                comment_ids_text,
                source,
            )
            displayed_matches.append(
                {
                    "match_key": self._create_match_key(
                        field, norm_original, field_data.get("matched", {})
                    )
                }
            )
            row_number += 1

        self.console.print(table)

        # Handle mark-correct functionality for displayed matches only
        if getattr(args, "mark_correct", False) and displayed_matches:
            self._mark_displayed_matches_as_correct(displayed_matches, field, args)
        elif getattr(args, "dry_run", False) and displayed_matches:
            self._preview_mark_correct(displayed_matches, field, args)

    def display_unconfirmed_matches(self, data: Dict, field: str, args) -> None:
        """Display only unconfirmed matches (not exact or previously confirmed)."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        self.console.print(f"\n[bold]Unconfirmed {field.capitalize()} Matches:[/bold]\n")

        table = self._get_table(title=f"Unconfirmed Matches - {field.capitalize()}", expand=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Count", style="magenta", justify="center")
        table.add_column("Original", style="yellow")
        table.add_column("Matched", style="green")
        table.add_column("Pattern", style="blue")
        table.add_column("Match Type", style="magenta")
        table.add_column("Comment IDs", style="dim")
        table.add_column("Source", style="dim")

        # Track displayed matches for mark-correct functionality
        displayed_matches = []

        # Get limit with default
        limit = getattr(args, "limit", 50)
        records = data.get("data", [])

        # Group by normalized original, matched_text, pattern, match_type
        grouped = {}
        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue
            original = field_data.get("original", "")
            norm_original = normalize_for_matching(original, None, field)
            matched = field_data.get("matched", {})
            matched_text = self._get_matched_text(field, matched)
            pattern = field_data.get("pattern", "")
            match_type = field_data.get("match_type", "")
            source = record.get("_source_file", "")
            record_id = record.get("id", "")

            # Skip exact matches (from correct_matches.yaml)
            if match_type == "exact":
                continue

            # Skip previously confirmed matches
            match_key = self._create_match_key(field, norm_original, matched)
            if match_key in self._correct_matches:
                continue

            # Use format-free text for grouping key
            key = (norm_original, matched_text, pattern, match_type)
            if key not in grouped:
                grouped[key] = {
                    "count": 0,
                    "field_data": field_data,
                    "matched_text": matched_text,
                    "pattern": pattern,
                    "match_type": match_type,
                    "source": source,
                    "record_ids": set(),
                    "comment_ids": set(),
                }
            grouped[key]["count"] += 1
            grouped[key]["record_ids"].add(record_id)
            if record_id:
                grouped[key]["comment_ids"].add(record_id)

        # Sort groups for deterministic display order
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: (x[0][0] or "", x[0][1] or "", x[0][2] or "", x[0][3] or ""),
        )

        row_number = 1
        for (norm_original, matched_text, pattern, match_type), group in sorted_groups[:limit]:
            count = group["count"]
            field_data = group["field_data"]
            source = group["source"]
            comment_ids = sorted(list(group["comment_ids"]))
            # Escape pattern for Rich table display
            pattern_disp = self._escape_pattern_for_display(pattern)

            # Create match key for this group
            match_key = self._create_match_key(field, norm_original, field_data.get("matched", {}))

            # Get format information for razors and blades
            format_info = ""
            if field in ["razor", "blade"]:
                matched_dict = field_data.get("matched", {})
                if matched_dict:  # Add null check
                    format_info = matched_dict.get("format", "")

            # Format comment IDs (show first few, then count)
            if comment_ids:
                if len(comment_ids) <= 3:
                    comment_ids_text = ", ".join(comment_ids)
                else:
                    comment_ids_text = (
                        f"{', '.join(comment_ids[:3])}... (+{len(comment_ids) - 3} more)"
                    )
            else:
                comment_ids_text = ""

            # Create row data based on field type
            table.add_row(
                str(row_number),
                str(count),
                norm_original,
                matched_text,
                format_info,
                pattern_disp,
                match_type,
                comment_ids_text,
                source,
            )
            displayed_matches.append(
                {
                    "match_key": self._create_match_key(
                        field, norm_original, field_data.get("matched", {})
                    )
                }
            )
            row_number += 1

        self.console.print(table)

        # Handle mark-correct functionality for displayed matches only
        if getattr(args, "mark_correct", False) and displayed_matches:
            self._mark_displayed_matches_as_correct(displayed_matches, field, args)
        elif getattr(args, "dry_run", False) and displayed_matches:
            self._preview_mark_correct(displayed_matches, field, args)

    def display_regex_matches(self, data: Dict, field: str, args) -> None:
        """Display only regex matches (not exact or previously confirmed)."""
        from sotd.utils.match_filter_utils import normalize_for_matching

        self.console.print(f"\n[bold]Regex Matches for {field.capitalize()}:[/bold]\n")

        table = self._get_table(title=f"Regex Matches - {field.capitalize()}", expand=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Original", style="yellow")
        table.add_column("Matched", style="green")
        table.add_column("Pattern", style="blue")
        table.add_column("Comment IDs", style="dim")
        table.add_column("Source", style="dim")

        # Track displayed matches for mark-correct functionality
        displayed_matches = []

        # Get limit with default
        limit = getattr(args, "limit", 50)
        records = data.get("data", [])

        # Group by normalized original, matched_text, pattern, match_type
        grouped = {}
        for record in records:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue
            original = field_data.get("original", "")
            norm_original = normalize_for_matching(original, None, field)
            matched = field_data.get("matched", {})
            matched_text = self._get_matched_text(field, matched)
            pattern = field_data.get("pattern", "")
            match_type = field_data.get("match_type", "")
            source = record.get("_source_file", "")
            record_id = record.get("id", "")

            # Skip exact matches (from correct_matches.yaml)
            if match_type == "exact":
                continue

            # Skip previously confirmed matches
            match_key = self._create_match_key(field, norm_original, matched)
            if match_key in self._correct_matches:
                continue

            # Skip unmatched rows (empty matched_text)
            if not matched_text:
                continue

            # Use format-free text for grouping key
            key = (norm_original, matched_text, pattern, match_type)
            if key not in grouped:
                grouped[key] = {
                    "count": 0,
                    "field_data": field_data,
                    "matched_text": matched_text,
                    "pattern": pattern,
                    "match_type": match_type,
                    "source": source,
                    "record_ids": set(),
                    "comment_ids": set(),
                }
            grouped[key]["count"] += 1
            grouped[key]["record_ids"].add(record_id)
            if record_id:
                grouped[key]["comment_ids"].add(record_id)

        # Sort groups for deterministic display order
        sorted_groups = sorted(
            grouped.items(),
            key=lambda x: (x[0][0] or "", x[0][1] or "", x[0][2] or "", x[0][3] or ""),
        )

        row_number = 1
        for (norm_original, matched_text, pattern, match_type), group in sorted_groups[:limit]:
            field_data = group["field_data"]
            source = group["source"]
            comment_ids = sorted(list(group["comment_ids"]))
            # Escape pattern for Rich table display
            pattern_disp = self._escape_pattern_for_display(pattern)
            # No truncation, let it wrap

            # Get format information for razors and blades
            format_info = ""
            if field in ["razor", "blade"]:
                matched_dict = field_data.get("matched", {})
                if matched_dict:  # Add null check
                    format_info = matched_dict.get("format", "")

            # Format comment IDs (show first few, then count)
            if comment_ids:
                if len(comment_ids) <= 3:
                    comment_ids_text = ", ".join(comment_ids)
                else:
                    comment_ids_text = (
                        f"{', '.join(comment_ids[:3])}... (+{len(comment_ids) - 3} more)"
                    )
            else:
                comment_ids_text = ""

            # Create row data based on field type
            table.add_row(
                str(row_number),
                norm_original,
                matched_text,
                format_info,
                pattern_disp,
                comment_ids_text,
                source,
            )
            displayed_matches.append(
                {
                    "match_key": self._create_match_key(
                        field, norm_original, field_data.get("matched", {})
                    )
                }
            )
            row_number += 1

        self.console.print(table)

        # Handle mark-correct functionality for displayed matches only
        if getattr(args, "mark_correct", False) and displayed_matches:
            self._mark_displayed_matches_as_correct(displayed_matches, field, args)
        elif getattr(args, "dry_run", False) and displayed_matches:
            self._preview_mark_correct(displayed_matches, field, args)

    def _count_filtered_matches(self, data: List[Dict], field: str) -> int:
        """Count how many matches were filtered out by correct matches."""
        filtered_count = 0

        for record in data:
            field_data = record.get(field)
            if not isinstance(field_data, dict):
                continue

            original = field_data.get("original", "")
            matched = field_data.get("matched", {})

            if not original or not matched:
                continue

            match_key = self._create_match_key(field, original, matched)
            if match_key in self._correct_matches:
                filtered_count += 1

        return filtered_count

    def _display_summary(
        self, mismatches: Dict[str, List[Dict]], filtered_count: int, args
    ) -> None:
        """Display summary of analysis results."""
        mismatch_keys = ["multiple_patterns", "levenshtein_distance", "low_confidence"]
        total_mismatches = sum(len(mismatches[key]) for key in mismatch_keys)

        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  • Potential mismatches found: {total_mismatches}")
        self.console.print(f"  • Previously marked correct: {len(self._correct_matches)}")
        if filtered_count > 0:
            self.console.print(f"  • Filtered out this run: {filtered_count}")

        if total_mismatches > 0:
            self.console.print(
                "\n[dim]Use --mark-correct to mark displayed matches as correct[/dim]"
            )
            self.console.print(
                "[dim]Use --show-correct to see previously marked correct matches[/dim]"
            )
            self.console.print("[dim]Use --clear-correct to reset all correct matches[/dim]")

    def _mark_displayed_matches_as_correct(
        self, displayed_matches: List[Dict], field: str = "razor", args=None
    ) -> None:
        """Mark only the displayed matches as correct."""
        if not displayed_matches:
            self.console.print("[yellow]No matches to mark as correct[/yellow]")
            return

        # Show confirmation prompt
        self.console.print(
            f"\n[bold red]⚠️  WARNING: About to mark {len(displayed_matches)} "
            f"matches as correct[/bold red]"
        )
        self.console.print("[red]This will modify data/correct_matches.yaml[/red]")
        self.console.print(f"[red]Field: {field}[/red]")

        # Show preview of what will be marked
        self.console.print("\n[bold]Preview of matches to be marked:[/bold]")
        for i, match in enumerate(displayed_matches[:5], 1):  # Show first 5
            if "field_data" in match:
                original = match["field_data"].get("original", "")
                matched = match["field_data"].get("matched", {})
                matched_text = self._get_matched_text(field, matched)
            else:
                original = match.get("original", "")
                matched_text = match.get("matched_text", "")
            self.console.print(f'  {i}. "{original}" → "{matched_text}"')

        if len(displayed_matches) > 5:
            self.console.print(f"  ... and {len(displayed_matches) - 5} more")

        # Confirmation prompt
        if not getattr(args, "no_confirm", False):
            try:
                response = self.console.input(
                    "\n[bold]Are you sure you want to mark these as correct? (yes/no): [/bold]"
                )
                if response.lower() not in ["yes", "y"]:
                    self.console.print("[yellow]Operation cancelled[/yellow]")
                    return
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operation cancelled[/yellow]")
                return
        else:
            self.console.print("[yellow]⚠️  Skipping confirmation prompt (--no-confirm)[/yellow]")

        marked_count = 0

        for match in displayed_matches:
            # Store the full match data for better brand/model extraction
            if "field_data" in match:
                field_data = match["field_data"]
                original = field_data.get("original", "")
                matched_dict = field_data.get("matched", {})

                # Determine field from context or use provided field
                current_field = field or "razor"  # Default fallback

                # Create match key for compatibility
                match_key = self._create_match_key(current_field, original, matched_dict)

                # Store additional data for canonical brand/model extraction
                self._correct_matches.add(match_key)

                # Store the full matched data for later use
                if not hasattr(self, "_correct_matches_data"):
                    self._correct_matches_data = {}
                self._correct_matches_data[match_key] = {
                    "original": original,
                    "matched": matched_dict,
                    "field": current_field,
                }

                marked_count += 1
            else:
                # Fallback for display_all_matches mode
                match_key = match.get("match_key")
                if match_key:
                    self._correct_matches.add(match_key)
                    marked_count += 1

        if marked_count > 0:
            self._save_correct_matches()
            self.console.print(
                f"[green]✅ Marked {marked_count} displayed matches as correct[/green]"
            )
            self.console.print("[green]Updated: data/correct_matches.yaml[/green]")
        else:
            self.console.print("[yellow]No matches to mark as correct[/yellow]")

    def _preview_mark_correct(self, displayed_matches: List[Dict], field: str, args) -> None:
        """Preview marking correct matches without actually marking them."""
        if not displayed_matches:
            self.console.print("[yellow]No matches to preview marking correct[/yellow]")
            return

        self.console.print(
            f"\n[bold red]⚠️  WARNING: Previewing marking {len(displayed_matches)} "
            f"matches as correct for {field}[/bold red]"
        )
        self.console.print("[red]This will not modify data/correct_matches.yaml[/red]")

        # Show preview of what would be marked
        self.console.print("\n[bold]Preview of matches to be marked:[/bold]")
        for i, match in enumerate(displayed_matches[:5], 1):  # Show first 5
            if "field_data" in match:
                original = match["field_data"].get("original", "")
                matched = match["field_data"].get("matched", {})
                matched_text = self._get_matched_text(field, matched)
            else:
                original = match.get("original", "")
                matched_text = match.get("matched_text", "")
            self.console.print(f'  {i}. "{original}" → "{matched_text}"')

        if len(displayed_matches) > 5:
            self.console.print(f"  ... and {len(displayed_matches) - 5} more")

        self.console.print("\n[dim]Use --mark-correct to mark these matches as correct[/dim]")
        self.console.print("[dim]Use --show-correct to see previously marked correct matches[/dim]")
        self.console.print("[dim]Use --clear-correct to reset all correct matches[/dim]")

    def _set_test_correct_matches_file(self, test_file: str) -> None:
        """Set test correct matches file."""
        self._test_correct_matches_file = Path(test_file)

    def _get_correct_matches_file(self) -> Path:
        """Get the correct matches file to use (test or production)."""
        if self._test_correct_matches_file and self._test_correct_matches_file.exists():
            return self._test_correct_matches_file
        return self._correct_matches_file


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the mismatch analysis tool."""
    analyzer = MismatchAnalyzer()
    parser = analyzer.get_parser()
    args = parser.parse_args(argv)
    analyzer.run(args)


if __name__ == "__main__":
    main()
