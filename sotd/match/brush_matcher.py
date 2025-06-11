import re
from pathlib import Path
from typing import Optional

import yaml

from sotd.match.brush_matching_strategies.chisel_and_hound_strategy import (
    ChiselAndHoundBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.declaration_grooming_strategy import (
    DeclarationGroomingBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.known_brush_strategy import (
    KnownBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.omega_semogue_strategy import (
    OmegaSemogueBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.other_brushes_strategy import (
    OtherBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.zenith_strategy import (
    ZenithBrushMatchingStrategy,
)


class BrushMatcher:
    def __init__(self, catalog_path: Path = Path("data/brushes.yaml")):
        self.catalog_path = catalog_path
        self.catalog_data = self._load_catalog(catalog_path)
        self.strategies = [
            KnownBrushMatchingStrategy(self.catalog_data.get("known_brushes", {})),
            DeclarationGroomingBrushMatchingStrategy(
                self.catalog_data.get("declaration_grooming", {})
            ),
            ChiselAndHoundBrushMatchingStrategy(),
            OmegaSemogueBrushMatchingStrategy(),
            ZenithBrushMatchingStrategy(),
            OtherBrushMatchingStrategy(self.catalog_data.get("other_brushes", {})),
        ]

    def _load_catalog(self, catalog_path: Path) -> dict:
        """Load brush catalog from YAML file."""
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}

    def match(self, value: str) -> dict:
        for strategy in self.strategies:
            result = strategy.match(value)

            # Handle different return formats from strategies
            if result:
                # Check if it's already wrapped (new format)
                if "matched" in result and result.get("matched"):
                    result["matched"]["_matched_by_strategy"] = strategy.__class__.__name__
                    result["matched"]["_pattern_used"] = result.get("pattern")
                    enriched = self._post_process_match(result, value)
                    return {
                        "original": value,
                        "matched": enriched["matched"],
                        "match_type": result.get("match_type"),
                        "pattern": result.get("pattern"),
                    }
                # Handle direct result format (ChiselAndHound, OmegaSemogue, Zenith)
                elif "brand" in result:
                    wrapped_result = {
                        "matched": result,
                        "pattern": result.get("_pattern_used", "unknown"),
                        "match_type": result.get("source_type", "exact"),
                    }
                    wrapped_result["matched"]["_matched_by_strategy"] = strategy.__class__.__name__
                    enriched = self._post_process_match(wrapped_result, value)
                    return {
                        "original": value,
                        "matched": enriched["matched"],
                        "match_type": wrapped_result.get("match_type"),
                        "pattern": wrapped_result.get("pattern"),
                    }

        return {"original": value, "matched": None, "match_type": None, "pattern": None}

    def _post_process_match(self, result: dict, value: str) -> dict:
        if not result.get("matched"):
            return result

        updated = result["matched"].copy()

        # Try to parse fiber and knot size from user input
        parsed_fiber = match_fiber(value)
        parsed_knot = None
        knot_match = re.search(r"(\d{2}(\.\d+)?)[\s-]*mm", value, re.IGNORECASE)
        if knot_match:
            parsed_knot = float(knot_match.group(1))

        # Handle fiber resolution priority (only if not already set by strategy)
        if "fiber_strategy" not in updated:
            fiber = updated.get("fiber")
            default_fiber = updated.get("default fiber")
            if fiber:
                updated["fiber_strategy"] = "yaml"
                if parsed_fiber and parsed_fiber.lower() != fiber.lower():
                    updated["fiber_conflict"] = f"user_input: {parsed_fiber}"
            elif parsed_fiber:
                updated["fiber"] = parsed_fiber
                updated["fiber_strategy"] = "user_input"
            elif default_fiber:
                updated["fiber"] = default_fiber
                updated["fiber_strategy"] = "default"
            else:
                updated["fiber_strategy"] = "unset"

        # Handle knot_size_mm resolution priority (only if not already set by strategy)
        if "knot_size_strategy" not in updated:
            knot_size = updated.get("knot_size_mm")
            default_knot_size = updated.get("default_knot_size_mm")
            if knot_size is not None:
                updated["knot_size_strategy"] = "yaml"
            elif parsed_knot is not None:
                updated["knot_size_mm"] = parsed_knot
                updated["knot_size_strategy"] = "user_input"
            elif default_knot_size is not None:
                updated["knot_size_mm"] = default_knot_size
                updated["knot_size_strategy"] = "default"
            else:
                updated["knot_size_strategy"] = "unset"

        # Extract handle_maker and knot_maker if not already set
        if "handle maker" not in updated or updated["handle maker"] is None:
            handle, knot = self._split_handle_and_knot(value)
            if handle:
                updated["handle maker"] = handle
            if knot:
                updated["knot maker"] = knot

        result["matched"] = updated
        return result

    def _split_handle_and_knot(self, text: str) -> tuple[Optional[str], Optional[str]]:
        lowered = text.lower()

        # Strategy 1: " w/ " split
        if " w/ " in lowered:
            parts = lowered.split(" w/ ", 1)
            handle = parts[0].strip().title()
            knot = parts[1].strip().title()
            return handle, knot

        return None, None
