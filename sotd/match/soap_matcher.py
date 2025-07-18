import difflib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.table import Table

from .loaders import CatalogLoader
from .types import MatchResult, MatchType, create_match_result


class SoapMatcher:
    def __init__(
        self,
        catalog_path: Path = Path("data/soaps.yaml"),
        correct_matches_path: Optional[Path] = None,
    ):
        self.loader = CatalogLoader()
        catalogs = self.loader.load_matcher_catalogs(
            catalog_path, "soap", correct_matches_path=correct_matches_path
        )
        self.catalog = catalogs["catalog"]
        self.correct_matches = catalogs["correct_matches"]
        self.scent_patterns, self.brand_patterns = self._compile_patterns()
        self._match_cache = {}

    def clear_cache(self):
        """Clear the match cache. Useful for testing to prevent cache pollution."""
        self._match_cache.clear()

    def _is_sample(self, text: str) -> bool:
        text = text.lower()
        return bool(re.search(r"\bsample\b", text)) or bool(
            re.search(r"\(\s*sample\s*\)", text, re.IGNORECASE)
        )

    def _strip_surrounding_punctuation(self, text: str) -> str:
        text = re.sub(r"^[\s\-–—/.,:;]+|[\s\-–—/.,:;]+$", "", text).strip()
        return text

    def _normalize_common_text(self, text: str) -> str:
        """
        Normalize text for brand fields by stripping markdown, punctuation, etc.
        Does NOT remove "soap" suffixes or use counts.
        """
        text = text.strip()
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # strip markdown links
        text = re.sub(r"[*_~`\\]+", "", text).strip()
        text = self._strip_surrounding_punctuation(text)
        return text

    def _normalize_scent_text(self, text: str) -> str:
        """
        Normalize text for scent fields by using _normalize_common_text and
        additionally stripping "soap" suffixes and use counts like (23).
        """
        text = self._normalize_common_text(text)
        text = re.sub(
            r"(soap( sample)?|croap|puck|cream|shav.*soap|shav.*cream).?\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        text = re.sub(r"\(\d*\)$", "", text).strip()  # remove use counts like (23)
        text = self._strip_surrounding_punctuation(text)
        return text

    def _compile_patterns(self):
        scent_compiled = []
        brand_compiled = []
        for maker, entry in self.catalog.items():
            # Scent-level patterns
            scents = entry.get("scents", {})
            for scent, scent_data in scents.items():
                for pattern in scent_data.get("patterns", []):
                    try:
                        scent_compiled.append(
                            {
                                "maker": maker,
                                "scent": scent,
                                "pattern": pattern,
                                "regex": re.compile(pattern, re.IGNORECASE),
                            }
                        )
                    except re.error:
                        continue
            # Brand-level patterns
            for pattern in entry.get("patterns", []):
                try:
                    brand_compiled.append(
                        {
                            "maker": maker,
                            "pattern": pattern,
                            "regex": re.compile(pattern, re.IGNORECASE),
                        }
                    )
                except re.error:
                    continue
        scent_compiled = sorted(scent_compiled, key=lambda x: len(x["pattern"]), reverse=True)
        brand_compiled = sorted(brand_compiled, key=lambda x: len(x["pattern"]), reverse=True)
        return scent_compiled, brand_compiled

    def _match_with_regex(self, value: str) -> MatchResult:
        """Match using regex patterns with REGEX match type."""
        # Check cache first - ensure cache key is always a string
        cache_key = str(value) if not isinstance(value, str) else value
        if cache_key in self._match_cache:
            cached_result = self._match_cache[cache_key]
            # Convert cached dict to MatchResult for backward compatibility
            if isinstance(cached_result, dict):
                return create_match_result(
                    original=cached_result.get("original", value),
                    matched=cached_result.get("matched"),
                    match_type=cached_result.get("match_type"),
                    pattern=cached_result.get("pattern"),
                )
            return cached_result

        original = value
        normalized = re.sub(r"^[*_~]+|[*_~]+$", "", value.strip()) if isinstance(value, str) else ""

        if not isinstance(value, str):
            result = create_match_result(
                original=original,
                matched=None,
                match_type=None,
                pattern=None,
            )
            self._match_cache[cache_key] = result
            return result

        result = self._match_scent_pattern(original, normalized)
        if result:
            result["match_type"] = "regex"
            match_result = create_match_result(
                original=result["original"],
                matched=result["matched"],
                match_type=result["match_type"],
                pattern=result["pattern"],
            )
            self._match_cache[cache_key] = match_result
            return match_result

        result = self._match_brand_pattern(original, normalized)
        if result:
            result["match_type"] = "brand"
            match_result = create_match_result(
                original=result["original"],
                matched=result["matched"],
                match_type=result["match_type"],
                pattern=result["pattern"],
            )
            self._match_cache[cache_key] = match_result
            return match_result

        result = self._match_dash_split(original, normalized)
        if result:
            result["match_type"] = "alias"
            match_result = create_match_result(
                original=result["original"],
                matched=result["matched"],
                match_type=result["match_type"],
                pattern=result["pattern"],
            )
            self._match_cache[cache_key] = match_result
            return match_result

        result = create_match_result(
            original=original,
            matched=None,
            match_type=None,
            pattern=None,
        )
        self._match_cache[cache_key] = result
        return result

    def _match_scent_pattern(self, original: str, normalized: str) -> Optional[dict]:
        for pattern_info in self.scent_patterns:
            if pattern_info["regex"].search(normalized):
                return {
                    "original": original,
                    "matched": {"maker": pattern_info["maker"], "scent": pattern_info["scent"]},
                    "pattern": pattern_info["pattern"],
                    "match_type": MatchType.REGEX,  # Will be overridden by caller
                    "is_sample": self._is_sample(original),
                }
        return None

    def _match_brand_pattern(self, original: str, normalized: str) -> Optional[dict]:
        for pattern_info in self.brand_patterns:
            match = pattern_info["regex"].search(normalized)
            if match:
                start, end = match.span()
                remainder = normalized[:start] + normalized[end:]
                remainder = re.sub(r"^[\s\-:*/_,~`\\]+", "", remainder).strip()
                remainder = self._normalize_scent_text(remainder)
                if self._is_sample(original):
                    remainder = self._remove_sample_marker(remainder)
                return {
                    "original": original,
                    "matched": {"maker": pattern_info["maker"], "scent": remainder},
                    "pattern": pattern_info["pattern"],
                    "match_type": MatchType.BRAND,  # Will be overridden by caller
                    "is_sample": self._is_sample(original),
                }
        return None

    def _match_dash_split(self, original: str, normalized: str) -> Optional[dict]:
        if "-" in normalized:
            parts = normalized.split("-", 1)
            brand_guess = self._normalize_common_text(parts[0].strip())
            scent_guess = self._normalize_scent_text(parts[1].strip())
            if self._is_sample(original):
                scent_guess = self._remove_sample_marker(scent_guess)
            if brand_guess and scent_guess:
                return {
                    "original": original,
                    "matched": {"maker": brand_guess, "scent": scent_guess},
                    "pattern": None,
                    "match_type": MatchType.ALIAS,  # Will be overridden by caller
                    "is_sample": self._is_sample(original),
                }
        return None

    def _remove_sample_marker(self, text: str) -> str:
        return re.sub(r"\(\s*sample\s*\)", "", text, flags=re.IGNORECASE).strip()

    def _no_match_result(self, original: str) -> dict:
        return {
            "original": original,
            "matched": None,
            "pattern": None,
            "match_type": None,  # Keep None for backward compatibility
            "is_sample": self._is_sample(original),
        }

    def match(self, value: str, bypass_correct_matches: bool = False) -> MatchResult:
        """
        Main orchestration method for soap matching.
        Ensures 'maker' and 'scent' are always present in the 'matched' dict for all match types.
        """
        if not isinstance(value, str):
            return create_match_result(
                original=value,
                matched=None,
                match_type=None,
                pattern=None,
            )

        # Check correct matches first (EXACT)
        if not bypass_correct_matches:
            correct = self._check_correct_matches(value)
            if correct:
                result = create_match_result(
                    original=value,
                    matched=correct,
                    match_type=MatchType.EXACT,
                    pattern=None,
                )
                # Ensure required fields are present
                if result and result.matched:
                    if "maker" not in result.matched:
                        result.matched["maker"] = None
                    if "scent" not in result.matched:
                        result.matched["scent"] = None
                return result

        # Fall back to regex/brand/alias matching
        result = self._match_with_regex(value)
        if result and result.matched:
            if "maker" not in result.matched:
                result.matched["maker"] = None
            if "scent" not in result.matched:
                result.matched["scent"] = None
        return result

    def _check_correct_matches(self, value: str) -> Optional[Dict[str, Any]]:
        # All correct match lookups must use normalize_for_matching
        # (see docs/product_matching_validation.md)
        cache_key = f"correct_matches:{str(value)}"
        if hasattr(self, "_match_cache") and cache_key in self._match_cache:
            return self._match_cache[cache_key]
        if not value or not self.correct_matches:
            if hasattr(self, "_match_cache"):
                self._match_cache[cache_key] = None
            return None

        normalized_value = self._normalize_scent_text(value)
        if not normalized_value:
            if hasattr(self, "_match_cache"):
                self._match_cache[cache_key] = None
            return None

        # Search through correct matches structure
        for maker, maker_data in self.correct_matches.items():
            if not isinstance(maker_data, dict):
                continue

            for scent, strings in maker_data.items():
                if not isinstance(strings, list):
                    continue

                # Check if normalized value matches any of the correct strings
                for correct_string in strings:
                    if self._normalize_scent_text(correct_string) == normalized_value:
                        # Return match data in the expected format for soaps
                        result = {"maker": maker, "scent": scent}
                        if hasattr(self, "_match_cache"):
                            self._match_cache[cache_key] = result
                        return result
        if hasattr(self, "_match_cache"):
            self._match_cache[cache_key] = None
        return None


# --- Utility analysis function ---
def analyze_soap_matches(
    matches: list[dict], similarity_threshold: float = 0.9, limit: Optional[int] = None
):
    """
    Analyzes a list of soap match results and identifies likely duplicates due to typos.
    Groups results by maker and scent and flags similar entries.

    Args:
        matches (list): List of dictionaries returned by SoapMatcher.match().
        similarity_threshold (float): Similarity ratio to consider two entries duplicates.
        limit (Optional[int]): Maximum number of duplicate pairs to show.
    """
    grouped = defaultdict(list)
    for match in matches:
        if match.get("match_type") == "exact":
            continue
        m = match.get("matched")
        if not m:
            continue
        key = (m["maker"].strip().lower(), m["scent"].strip().lower())
        grouped[key].append(match)

    keys = list(grouped.keys())
    console = Console()
    table = Table(title="🔍 Potential Duplicate Soap Matches")
    table.add_column("Maker 1", style="cyan")
    table.add_column("Maker 2", style="cyan")
    table.add_column("Scent 1", style="magenta")
    table.add_column("Scent 2", style="magenta")
    table.add_column("Maker Sim", justify="right", style="green")
    table.add_column("Scent Sim", justify="right", style="green")
    table.add_column("Original", style="dim")

    # Fuzzy grouping using union-find style clustering
    clusters = []
    for key in keys:
        added = False
        for cluster in clusters:
            if any(
                difflib.SequenceMatcher(None, key[0], other[0]).ratio() > similarity_threshold
                and difflib.SequenceMatcher(None, key[1], other[1]).ratio() > similarity_threshold
                for other in cluster
            ):
                cluster.append(key)
                added = True
                break
        if not added:
            clusters.append([key])

    shown = 0
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        cluster = sorted(cluster)
        for i, key1 in enumerate(cluster):
            for j in range(i + 1, len(cluster)):
                if limit is not None and shown >= limit:
                    console.print(table)
                    return
                key2 = cluster[j]
                # # Retrieve match_type for each key
                # match_type_1 = grouped[key1][0].get("match_type")
                # match_type_2 = grouped[key2][0].get("match_type")

                # If the brands match exactly,
                # skip calculating maker_sim and set values as specified
                maker_sim = 1.0
                maker_1 = maker_2 = f"{key1[0]}"
                if key1[0] != key2[0]:
                    maker_sim = difflib.SequenceMatcher(None, key1[0], key2[0]).ratio()
                    maker_1 = (
                        f"[yellow]{key1[0]}[/yellow]"
                        if maker_sim < 1.0
                        else f"[dim]{key1[0]}[/dim]"
                    )
                    maker_2 = (
                        f"[yellow]{key2[0]}[/yellow]"
                        if maker_sim < 1.0
                        else f"[dim]{key2[0]}[/dim]"
                    )

                # If the scents match exactly,
                # skip calculating scent_sim and set values as specified
                scent_sim = 1.0
                scent_1 = scent_2 = f"{key1[1]}"
                if key1[1] != key2[1]:
                    scent_sim = difflib.SequenceMatcher(None, key1[1], key2[1]).ratio()
                    scent_1 = (
                        f"[yellow]{key1[1]}[/yellow]"
                        if scent_sim < 1.0
                        else f"[dim]{key1[1]}[/dim]"
                    )
                    scent_2 = (
                        f"[yellow]{key2[1]}[/yellow]"
                        if scent_sim < 1.0
                        else f"[dim]{key2[1]}[/dim]"
                    )

                maker_sim_str = f"{maker_sim:.2f}"
                scent_sim_str = f"{scent_sim:.2f}"

                original_1 = grouped[key1][0]["original"]
                original_2 = grouped[key2][0]["original"]
                table.add_row(
                    maker_1,
                    maker_2,
                    scent_1,
                    scent_2,
                    maker_sim_str,
                    scent_sim_str,
                    f"{original_1} / {original_2}",
                )
                shown += 1
    console.print(table)
