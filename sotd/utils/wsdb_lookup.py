"""WSDB lookup utility with direct slug support."""

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


class WSDBLookup:
    """Utility for looking up WSDB slugs directly from soaps.yaml."""

    def __init__(self, project_root: Path | None = None):
        """Initialize WSDB lookup utility.

        Args:
            project_root: Optional project root path. If None, will be auto-detected.
        """
        self.project_root = project_root or self._find_project_root()
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

    def _load_pipeline_soaps(self) -> Dict[str, Dict[str, Any]]:
        """Lazily load pipeline soaps from soaps.yaml for slug lookup.

        Returns:
            Dict mapping brand_name -> {scents: {scent_name: {wsdb_slug: ...}}}
        """
        if self._pipeline_soaps is not None:
            return self._pipeline_soaps

        soaps_file = self.project_root / "data" / "soaps.yaml"

        if not soaps_file.exists():
            logger.debug(f"soaps.yaml not found at {soaps_file}, slug lookup disabled")
            self._pipeline_soaps = {}
            return {}

        try:
            with soaps_file.open("r", encoding="utf-8") as f:
                soaps_data = yaml.safe_load(f) or {}

            # Transform to lookup-friendly format
            pipeline_soaps = {}
            for brand, brand_data in soaps_data.items():
                scents = {}

                if isinstance(brand_data, dict) and "scents" in brand_data:
                    # Extract scents with wsdb_slug
                    for scent_name, scent_data in brand_data["scents"].items():
                        wsdb_slug = None
                        if isinstance(scent_data, dict) and "wsdb_slug" in scent_data:
                            wsdb_slug = (
                                scent_data["wsdb_slug"]
                                if isinstance(scent_data["wsdb_slug"], str)
                                else None
                            )

                            scents[scent_name] = {"wsdb_slug": wsdb_slug}

                pipeline_soaps[brand] = {"scents": scents}

            self._pipeline_soaps = pipeline_soaps

            logger.debug(f"Loaded {len(pipeline_soaps)} brands from pipeline for slug lookup")

            return pipeline_soaps
        except Exception as e:
            logger.debug(f"Failed to load pipeline soaps: {e}, slug lookup disabled")
            self._pipeline_soaps = {}
            return {}

    def get_wsdb_slug(self, brand: str, scent: str) -> str | None:
        """Lookup WSDB slug for a given brand and scent from soaps.yaml.

        Checks if the brand and scent exist in soaps.yaml and returns the wsdb_slug
        if present. No matching or lookup is performed - only direct slug retrieval.

        Args:
            brand: Brand name to lookup
            scent: Scent name to lookup

        Returns:
            WSDB slug if found in catalog, None otherwise
        """
        if not brand or not scent:
            return None

        pipeline_soaps = self._load_pipeline_soaps()

        # Check if brand exists
        brand_entry = pipeline_soaps.get(brand)
        if not brand_entry:
            return None

        # Check if scent exists under brand
        scents = brand_entry.get("scents", {})
        scent_info = scents.get(scent)
        if not scent_info:
            return None

        # Return wsdb_slug if present
        wsdb_slug = scent_info.get("wsdb_slug")
        if isinstance(wsdb_slug, str) and wsdb_slug:
            return wsdb_slug

        return None
