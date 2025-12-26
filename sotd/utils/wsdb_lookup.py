"""WSDB lookup utility with alias support."""

import json
import logging
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class WSDBLookup:
    """Utility for looking up WSDB slugs with alias support from soaps.yaml."""

    def __init__(self, project_root: Path | None = None):
        """Initialize WSDB lookup utility.

        Args:
            project_root: Optional project root path. If None, will be auto-detected.
        """
        self.project_root = project_root or self._find_project_root()
        self._wsdb_soaps: List[Dict[str, Any]] | None = None
        self._pipeline_soaps: Dict[str, Dict[str, Any]] | None = None

    def _find_project_root(self) -> Path:
        """Find project root by looking for data/ directory.

        Returns:
            Path to project root
        """
        current_file = Path(__file__)
        # This file is at: sotd/utils/wsdb_lookup.py
        # Project root is 2 levels up
        return current_file.parent.parent.parent

    def _normalize_string(self, text: str) -> str:
        """Normalize a string to Unicode NFC (Normalization Form Canonical Composed).

        This ensures that visually identical characters are treated the same regardless
        of their Unicode encoding.

        Args:
            text: The string to normalize

        Returns:
            The normalized string in NFC form
        """
        if not text:
            return text
        return unicodedata.normalize("NFC", text)

    def _normalize_accents(self, text: str) -> str:
        """Remove accents from characters (e.g., 'Café' → 'Cafe').

        Uses Unicode decomposition to separate base characters from combining marks.

        Args:
            text: The string to normalize

        Returns:
            String with accents removed
        """
        if not text:
            return text
        # Decompose to NFD (base + combining marks), then remove combining marks
        nfd = unicodedata.normalize("NFD", text)
        return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

    def _normalize_and_ampersand(self, text: str) -> str:
        """Normalize 'and' and '&' to a consistent form.

        Converts both 'and' and '&' (with or without spaces) to 'and'.

        Args:
            text: The string to normalize

        Returns:
            String with 'and' and '&' normalized to 'and'
        """
        if not text:
            return text
        import re

        # Replace '&' (with optional spaces) with 'and'
        text = re.sub(r"\s*&\s*", " and ", text)
        # Normalize multiple spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_for_matching(self, text: str) -> str:
        """Apply all virtual pattern normalizations for matching.

        This is the main normalization function that should be used for all
        WSDB matching operations. It applies:
        - Lowercase and trim
        - Unicode NFC normalization
        - Accent removal
        - "and"/"&" normalization

        Args:
            text: The string to normalize

        Returns:
            Fully normalized string for matching
        """
        if not text:
            return text
        # Apply all normalizations
        normalized = text.lower().strip()
        normalized = self._normalize_string(normalized)  # Unicode NFC
        normalized = self._normalize_accents(normalized)  # Remove accents
        normalized = self._normalize_and_ampersand(normalized)  # Normalize and/&
        return normalized

    def _strip_trailing_soap(self, text: str) -> str | None:
        """Strip trailing 'soap' (case-insensitive) from text.

        This is a virtual alias helper that computes a stripped version on-the-fly.
        The result is NOT saved to soaps.yaml.

        Args:
            text: The string to process

        Returns:
            Stripped version if 'soap' found at end, None otherwise
        """
        if not text:
            return None
        text_lower = text.lower().rstrip()
        if text_lower.endswith("soap"):
            stripped = text[:-4].rstrip()  # Remove 'soap' and trailing whitespace
            return stripped if stripped else None
        return None

    def _load_wsdb_data(self) -> List[Dict[str, Any]]:
        """Lazily load WSDB soap data from software.json.

        Returns:
            List of WSDB soap entries (filtered for type="Soap")
        """
        if self._wsdb_soaps is not None:
            return self._wsdb_soaps

        wsdb_file = self.project_root / "data" / "wsdb" / "software.json"

        if not wsdb_file.exists():
            logger.debug(f"WSDB file not found at {wsdb_file}, skipping link generation")
            self._wsdb_soaps = []
            return []

        try:
            with wsdb_file.open("r", encoding="utf-8") as f:
                all_software = json.load(f)

            # Filter for soaps only
            soaps = [item for item in all_software if item.get("type") == "Soap"]
            self._wsdb_soaps = soaps

            logger.debug(f"Loaded {len(soaps)} soaps from WSDB")

            return soaps
        except Exception as e:
            logger.debug(f"Failed to load WSDB data: {e}, skipping link generation")
            self._wsdb_soaps = []
            return []

    def _load_pipeline_soaps(self) -> Dict[str, Dict[str, Any]]:
        """Lazily load pipeline soaps from soaps.yaml for alias lookup.

        Returns:
            Dict mapping brand_name -> {aliases: [...], scents: {scent_name: {alias: ...}}}
        """
        if self._pipeline_soaps is not None:
            return self._pipeline_soaps

        soaps_file = self.project_root / "data" / "soaps.yaml"

        if not soaps_file.exists():
            logger.debug(f"soaps.yaml not found at {soaps_file}, alias lookup disabled")
            self._pipeline_soaps = {}
            return {}

        try:
            with soaps_file.open("r", encoding="utf-8") as f:
                soaps_data = yaml.safe_load(f) or {}

            # Transform to lookup-friendly format
            pipeline_soaps = {}
            for brand, brand_data in soaps_data.items():
                aliases = []
                scents = {}

                if isinstance(brand_data, dict):
                    # Extract aliases if present
                    if "aliases" in brand_data:
                        aliases = (
                            brand_data["aliases"] if isinstance(brand_data["aliases"], list) else []
                        )

                    # Extract scents with aliases
                    if "scents" in brand_data:
                        for scent_name, scent_data in brand_data["scents"].items():
                            scent_alias = None
                            if isinstance(scent_data, dict) and "alias" in scent_data:
                                scent_alias = (
                                    scent_data["alias"]
                                    if isinstance(scent_data["alias"], str)
                                    else None
                                )

                            scents[scent_name] = {"alias": scent_alias}

                pipeline_soaps[brand] = {"aliases": aliases, "scents": scents}

            self._pipeline_soaps = pipeline_soaps

            logger.debug(f"Loaded {len(pipeline_soaps)} brands from pipeline for alias lookup")

            return pipeline_soaps
        except Exception as e:
            logger.debug(f"Failed to load pipeline soaps: {e}, alias lookup disabled")
            self._pipeline_soaps = {}
            return {}

    def get_wsdb_slug(self, brand: str, scent: str) -> str | None:
        """Lookup WSDB slug for a given brand and scent, respecting aliases.

        Checks canonical brand/scent first, then tries all aliases from soaps.yaml.

        Args:
            brand: Brand name to match
            scent: Scent name to match

        Returns:
            WSDB slug if found, None otherwise
        """
        if not brand or not scent:
            return None

        wsdb_soaps = self._load_wsdb_data()
        if not wsdb_soaps:
            return None

        pipeline_soaps = self._load_pipeline_soaps()

        # Normalize input using full normalization (includes accents, and/&)
        normalized_brand = self._normalize_for_matching(brand)
        normalized_scent = self._normalize_for_matching(scent)

        # Get brand entry from pipeline soaps for alias lookup
        brand_entry = pipeline_soaps.get(brand, {"aliases": [], "scents": {}})

        # Get all brand names to try: canonical + aliases + virtual alias (stripped "soap")
        brand_names_to_try = [normalized_brand]
        if brand_entry.get("aliases"):
            brand_names_to_try.extend(
                [self._normalize_for_matching(alias) for alias in brand_entry["aliases"]]
            )
        # Add virtual alias: strip trailing "soap" if present
        brand_virtual_alias = self._strip_trailing_soap(normalized_brand)
        if brand_virtual_alias:
            brand_virtual_alias_normalized = self._normalize_for_matching(brand_virtual_alias)
            if brand_virtual_alias_normalized not in brand_names_to_try:
                brand_names_to_try.append(brand_virtual_alias_normalized)

        # Get scent names to try: canonical + alias + virtual alias (stripped "soap")
        scent_names_to_try = [normalized_scent]
        scent_info = brand_entry.get("scents", {}).get(scent, {})
        if scent_info.get("alias"):
            scent_alias = self._normalize_for_matching(scent_info["alias"])
            scent_names_to_try.append(scent_alias)
        # Add virtual alias: strip trailing "soap" if present
        scent_virtual_alias = self._strip_trailing_soap(normalized_scent)
        if scent_virtual_alias:
            scent_virtual_alias_normalized = self._normalize_for_matching(scent_virtual_alias)
            if scent_virtual_alias_normalized not in scent_names_to_try:
                scent_names_to_try.append(scent_virtual_alias_normalized)

        # Try all combinations: brand names × scent names
        for brand_name in brand_names_to_try:
            for scent_name in scent_names_to_try:
                for soap in wsdb_soaps:
                    # Normalize WSDB entries using full normalization
                    wsdb_brand = self._normalize_for_matching(soap.get("brand") or "")
                    wsdb_name = self._normalize_for_matching(soap.get("name") or "")

                    # Also try matching against WSDB entries with stripped "soap" (virtual alias)
                    wsdb_brand_virtual = self._strip_trailing_soap(wsdb_brand)
                    if wsdb_brand_virtual:
                        wsdb_brand_virtual = self._normalize_for_matching(wsdb_brand_virtual)
                    wsdb_name_virtual = self._strip_trailing_soap(wsdb_name)
                    if wsdb_name_virtual:
                        wsdb_name_virtual = self._normalize_for_matching(wsdb_name_virtual)

                    # Match against original or virtual alias versions
                    brand_matches = wsdb_brand == brand_name or (
                        wsdb_brand_virtual and wsdb_brand_virtual == brand_name
                    )
                    name_matches = wsdb_name == scent_name or (
                        wsdb_name_virtual and wsdb_name_virtual == scent_name
                    )

                    if brand_matches and name_matches:
                        return soap.get("slug")

        return None
