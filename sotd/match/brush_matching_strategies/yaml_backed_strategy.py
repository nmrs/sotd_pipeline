import re
from pathlib import Path

from sotd.match.brush_matching_strategies.base_brush_matching_strategy import (
    BaseBrushMatchingStrategy,
)
from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.knot_size_utils import parse_knot_size
from sotd.match.types import MatchResult, create_match_result
from sotd.utils.yaml_loader import UniqueKeyLoader, load_yaml_with_nfc


class YamlBackedBrushMatchingStrategy(BaseBrushMatchingStrategy):
    def __init__(self, catalog_data: dict | Path):
        if isinstance(catalog_data, Path):
            self.catalog = load_yaml_with_nfc(catalog_data, loader_cls=UniqueKeyLoader)
        else:
            self.catalog = catalog_data or {}

    def match(self, value: str) -> MatchResult:
        # Collect all patterns with their metadata
        all_patterns = []
        for brand, brushes in self.catalog.items():
            for model, metadata in brushes.items():
                for pattern in metadata.get("patterns", []):
                    all_patterns.append((pattern, brand, model, metadata))
        # Sort all patterns by length descending
        all_patterns = sorted(all_patterns, key=lambda x: len(x[0]), reverse=True)
        for pattern, brand, model, metadata in all_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                result = {"brand": brand, "model": model, "_pattern_used": pattern}
                # Priority 1: Exact field in YAML
                if "fiber" in metadata:
                    result["fiber"] = metadata["fiber"]
                    result["fiber_strategy"] = "yaml"
                else:
                    # Priority 2: Parsed from user input
                    fiber = match_fiber(value)
                    if fiber:
                        result["fiber"] = fiber
                        result["fiber_strategy"] = "parsed"
                    else:
                        # Priority 3: Default field in YAML
                        if "default fiber" in metadata:
                            result["fiber"] = metadata["default fiber"]
                            result["fiber_strategy"] = "yaml_default"

                # Priority 1: Exact field in YAML
                if "knot_size_mm" in metadata:
                    result["knot_size_mm"] = metadata["knot_size_mm"]
                    result["knot_size_strategy"] = "yaml"
                else:
                    # Priority 2: Parsed from user input
                    size = parse_knot_size(value)
                    if size is not None:
                        result["knot_size_mm"] = size
                        result["knot_size_strategy"] = "parsed"
                    else:
                        # Priority 3: Default field in YAML
                        if "default_knot_size_mm" in metadata:
                            result["knot_size_mm"] = metadata["default_knot_size_mm"]
                            result["knot_size_strategy"] = "yaml_default"

                result["_matched_by_strategy"] = self.__class__.__name__
                return create_match_result(
                    original=value,
                    matched=result,
                    pattern=pattern,
                    match_type="exact",
                )
        return create_match_result(
            original=value,
            matched=None,
            pattern=None,
            match_type=None,
        )
