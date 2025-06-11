import re

from sotd.match.brush_matching_strategies.utils.fiber_utils import match_fiber
from sotd.match.brush_matching_strategies.utils.knot_size_utils import parse_knot_size
from sotd.match.brush_matching_strategies.yaml_backed_strategy import (
    YamlBackedBrushMatchingStrategy,
)


class OtherBrushMatchingStrategy(YamlBackedBrushMatchingStrategy):
    def match(self, value: str) -> dict:
        # Handle other_brushes format: brand -> {default: fiber, patterns: []}
        for brand, metadata in self.catalog.items():
            if not isinstance(metadata, dict) or "patterns" not in metadata:
                continue

            for pattern in metadata.get("patterns", []):
                if re.search(pattern, value, re.IGNORECASE):
                    # Extract fiber from user input or use default
                    user_fiber = match_fiber(value)
                    default_fiber = metadata.get("default")
                    final_fiber = user_fiber or default_fiber

                    # Extract knot size from user input or use default
                    user_knot_size = parse_knot_size(value)
                    default_knot_size = metadata.get("knot_size_mm")

                    # Construct model from brand + fiber
                    if user_fiber:
                        model = f"{brand} {user_fiber.title()}"
                    else:
                        model = f"{brand} {default_fiber.title()}" if default_fiber else brand

                    result = {
                        "brand": brand,
                        "model": model,
                        "fiber": final_fiber,
                        "_pattern_used": pattern,
                        "fiber_strategy": "user_input" if user_fiber else "default",
                        "_matched_by_strategy": self.__class__.__name__,
                    }

                    # Add knot size - user input takes precedence over YAML
                    if user_knot_size is not None:
                        result["knot_size_mm"] = user_knot_size
                        result["knot_size_strategy"] = "user_input"
                    elif default_knot_size is not None:
                        result["knot_size_mm"] = default_knot_size
                        result["knot_size_strategy"] = "yaml"

                    return {"matched": result, "match_type": "brand_default", "pattern": pattern}

        return {"matched": None, "match_type": None, "pattern": None}
