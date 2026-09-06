"""Write catalog changes (new scents, patterns, products) to YAML catalog files.

When a proposal from the match validation agent is accepted in the WebUI,
CatalogUpdater applies the change to the appropriate YAML catalog file
(soaps.yaml, razors.yaml, blades.yaml, or brushes.yaml).

All writes are atomic: data is written to a .tmp file first, then moved into
place, so a crash mid-write cannot corrupt the catalog.
"""

from pathlib import Path
from typing import Optional

import yaml


class CatalogUpdater:
    """Applies accepted proposals to catalog YAML files."""

    CATALOG_FILES = {
        "soap": "soaps.yaml",
        "razor": "razors.yaml",
        "blade": "blades.yaml",
        "brush": "brushes.yaml",
    }

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_catalog(self, field: str) -> dict:
        path = self.data_dir / self.CATALOG_FILES[field]
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_catalog(self, field: str, data: dict) -> None:
        """Atomic write: dump to .tmp then replace the original."""
        path = self.data_dir / self.CATALOG_FILES[field]
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            tmp_path.replace(path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    # ------------------------------------------------------------------
    # Soap operations
    # ------------------------------------------------------------------

    def add_soap_scent(self, brand: str, scent: str, patterns: list[str]) -> None:
        """Add a new scent to an existing soap brand.

        Raises:
            KeyError: if brand is not in the catalog.
            ValueError: if scent already exists for the brand.
        """
        catalog = self._load_catalog("soap")
        if brand not in catalog:
            raise KeyError(f"Brand '{brand}' not found in soaps catalog")
        if scent in catalog[brand].get("scents", {}):
            raise ValueError(f"Scent '{scent}' already exists for brand '{brand}'")
        if "scents" not in catalog[brand]:
            catalog[brand]["scents"] = {}
        catalog[brand]["scents"][scent] = {"patterns": patterns}
        catalog[brand]["scents"] = dict(sorted(catalog[brand]["scents"].items()))
        self._save_catalog("soap", catalog)

    def add_soap_pattern(self, brand: str, scent: str, pattern: str) -> None:
        """Add a regex pattern to an existing soap scent.

        Raises:
            KeyError: if brand or scent is not found.
        """
        catalog = self._load_catalog("soap")
        if brand not in catalog:
            raise KeyError(f"Brand '{brand}' not found in soaps catalog")
        if scent not in catalog[brand].get("scents", {}):
            raise KeyError(f"Scent '{scent}' not found for brand '{brand}'")
        catalog[brand]["scents"][scent]["patterns"].append(pattern)
        self._save_catalog("soap", catalog)

    # ------------------------------------------------------------------
    # Razor operations
    # ------------------------------------------------------------------

    def add_razor_model(
        self, brand: str, model: str, patterns: list[str], format: str = "DE"
    ) -> None:
        """Add a new razor model. Creates brand if it doesn't exist.

        The ``format`` key is omitted when DE (the default).
        """
        catalog = self._load_catalog("razor")
        if brand not in catalog:
            catalog[brand] = {}
        entry: dict = {"patterns": patterns}
        if format != "DE":
            entry["format"] = format
        catalog[brand][model] = entry
        self._save_catalog("razor", catalog)

    def add_razor_pattern(self, brand: str, model: str, pattern: str) -> None:
        """Add a regex pattern to an existing razor model.

        Raises:
            KeyError: if brand/model not found.
        """
        catalog = self._load_catalog("razor")
        if brand not in catalog or model not in catalog[brand]:
            raise KeyError(f"Razor '{brand} / {model}' not found in catalog")
        catalog[brand][model]["patterns"].append(pattern)
        self._save_catalog("razor", catalog)

    # ------------------------------------------------------------------
    # Blade operations
    # ------------------------------------------------------------------

    def add_blade_model(self, format: str, brand: str, model: str, patterns: list[str]) -> None:
        """Add a new blade model. Creates format and brand levels if needed."""
        catalog = self._load_catalog("blade")
        if format not in catalog:
            catalog[format] = {}
        if brand not in catalog[format]:
            catalog[format][brand] = {}
        catalog[format][brand][model] = {"patterns": patterns}
        self._save_catalog("blade", catalog)

    def add_blade_pattern(self, format: str, brand: str, model: str, pattern: str) -> None:
        """Add a regex pattern to an existing blade model.

        Raises:
            KeyError: if format/brand/model not found.
        """
        catalog = self._load_catalog("blade")
        if (
            format not in catalog
            or brand not in catalog[format]
            or model not in catalog[format][brand]
        ):
            raise KeyError(f"Blade '{format} / {brand} / {model}' not found in catalog")
        catalog[format][brand][model]["patterns"].append(pattern)
        self._save_catalog("blade", catalog)

    # ------------------------------------------------------------------
    # Brush operations
    # ------------------------------------------------------------------

    def add_brush_model(
        self,
        brand: str,
        model: str,
        patterns: list[str],
        fiber: Optional[str] = None,
        knot_size_mm: Optional[int] = None,
    ) -> None:
        """Add a new brush model under ``known_brushes``. Creates brand if needed."""
        catalog = self._load_catalog("brush")
        if "known_brushes" not in catalog:
            catalog["known_brushes"] = {}
        if brand not in catalog["known_brushes"]:
            catalog["known_brushes"][brand] = {}
        entry: dict = {"patterns": patterns}
        if fiber is not None:
            entry["fiber"] = fiber
        if knot_size_mm is not None:
            entry["knot_size_mm"] = knot_size_mm
        catalog["known_brushes"][brand][model] = entry
        self._save_catalog("brush", catalog)

    def add_brush_pattern(self, brand: str, model: str, pattern: str) -> None:
        """Add a regex pattern to an existing brush model.

        Raises:
            KeyError: if brand/model not found under known_brushes.
        """
        catalog = self._load_catalog("brush")
        if (
            brand not in catalog.get("known_brushes", {})
            or model not in catalog["known_brushes"][brand]
        ):
            raise KeyError(f"Brush '{brand} / {model}' not found in catalog")
        catalog["known_brushes"][brand][model]["patterns"].append(pattern)
        self._save_catalog("brush", catalog)

    # ------------------------------------------------------------------
    # Proposal dispatch
    # ------------------------------------------------------------------

    def apply_proposal(self, proposal: dict) -> None:
        """Apply a single proposal from agent output.

        Dispatches to the appropriate method based on ``type`` and ``field``.

        Raises:
            ValueError: if proposal type/field combination is not recognized.
        """
        ptype = proposal["type"]
        field = proposal["field"]

        if ptype == "new_scent":
            if field != "soap":
                raise ValueError(f"new_scent is only valid for soap, got field: {field}")
            self.add_soap_scent(
                proposal["brand"],
                proposal["model"],
                [proposal["suggested_pattern"]],
            )
        elif ptype == "new_pattern":
            self._apply_new_pattern(proposal, field)
        elif ptype == "new_product":
            self._apply_new_product(proposal, field)
        else:
            raise ValueError(f"Unknown proposal type: {ptype} for field: {field}")

    def _apply_new_pattern(self, proposal: dict, field: str) -> None:
        """Dispatch a new_pattern proposal to the right field handler."""
        if field == "soap":
            # If the scent doesn't exist yet, create it instead of failing
            catalog = self._load_catalog("soap")
            brand_entry = catalog.get(proposal["brand"], {})
            if proposal["model"] not in brand_entry.get("scents", {}):
                self.add_soap_scent(
                    proposal["brand"],
                    proposal["model"],
                    [proposal["suggested_pattern"]],
                )
            else:
                self.add_soap_pattern(
                    proposal["brand"], proposal["model"], proposal["suggested_pattern"]
                )
        elif field == "razor":
            self.add_razor_pattern(
                proposal["brand"], proposal["model"], proposal["suggested_pattern"]
            )
        elif field == "blade":
            entry = proposal.get("suggested_entry", {})
            fmt = entry.get("format", "DE")
            self.add_blade_pattern(
                fmt,
                proposal["brand"],
                proposal["model"],
                proposal["suggested_pattern"],
            )
        elif field == "brush":
            self.add_brush_pattern(
                proposal["brand"], proposal["model"], proposal["suggested_pattern"]
            )
        else:
            raise ValueError(f"Unknown proposal type: new_pattern for field: {field}")

    def _apply_new_product(self, proposal: dict, field: str) -> None:
        """Dispatch a new_product proposal to the right field handler."""
        entry = proposal.get("suggested_entry", {})

        if field == "razor":
            self.add_razor_model(
                proposal["brand"],
                proposal["model"],
                entry.get("patterns", [proposal["suggested_pattern"]]),
                format=entry.get("format", "DE"),
            )
        elif field == "blade":
            self.add_blade_model(
                entry.get("format", "DE"),
                proposal["brand"],
                proposal["model"],
                entry.get("patterns", [proposal["suggested_pattern"]]),
            )
        elif field == "brush":
            self.add_brush_model(
                proposal["brand"],
                proposal["model"],
                entry.get("patterns", [proposal["suggested_pattern"]]),
                fiber=entry.get("fiber"),
                knot_size_mm=entry.get("knot_size_mm"),
            )
        elif field == "soap":
            catalog = self._load_catalog("soap")
            brand = proposal["brand"]
            scent = proposal["model"]
            scent_patterns = entry.get("patterns", [proposal["suggested_pattern"]])
            if brand not in catalog:
                # New brand entirely — create brand entry with patterns and scent
                brand_patterns = entry.get("patterns", [proposal["suggested_pattern"]])
                scents_entry = entry.get("scents", {scent: {"patterns": scent_patterns}})
                catalog[brand] = {"patterns": brand_patterns, "scents": scents_entry}
                catalog = dict(sorted(catalog.items()))
                self._save_catalog("soap", catalog)
            else:
                # Brand exists — just add the scent
                self.add_soap_scent(brand, scent, scent_patterns)
        else:
            raise ValueError(f"Unknown proposal type: new_product for field: {field}")
