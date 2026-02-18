import re
from typing import Optional

from .text_splitter import normalize_text, split_on_delimiters


class BrushSplitter:
    """Brush splitting functionality — thin wrapper around text_splitter.

    Production code should use AutomatedSplitStrategy (which also delegates
    to text_splitter). This class exists for backward compatibility with tests
    and for the known-brush check that requires strategy instances.
    """

    # Class-level cache for brands with slashes to avoid repeated YAML loading
    _brands_with_slash_cache = None

    @classmethod
    def clear_brands_cache(cls):
        """Clear the brands with slash cache."""
        cls._brands_with_slash_cache = None

    def __init__(self, handle_matcher=None, strategies=None):
        self.handle_matcher = handle_matcher
        self.strategies = strategies or []
        # Pre-load brands with slash to avoid repeated YAML loading during matching
        self._brands_with_slash = self._get_brands_with_slash()

    @classmethod
    def _get_brands_with_slash(cls) -> set:
        """Get cached set of brand and model names that contain '/'."""
        if cls._brands_with_slash_cache is None:
            cls._brands_with_slash_cache = cls._load_brands_with_slash()
        return cls._brands_with_slash_cache

    @classmethod
    def _load_brands_with_slash(cls) -> set:
        """Load brands and models with '/' from brushes.yaml."""
        try:
            from pathlib import Path

            import yaml

            brushes_path = Path("data/brushes.yaml")
            if not brushes_path.exists():
                return set()

            with open(brushes_path, "r", encoding="utf-8") as f:
                brushes_data = yaml.safe_load(f)

            brands_with_slash = set()
            sections_to_check = ["known_brushes", "other_brushes"]

            for section_name in sections_to_check:
                section_data = brushes_data.get(section_name, {})
                if not isinstance(section_data, dict):
                    continue

                for brand_name in section_data.keys():
                    if "/" in brand_name:
                        brands_with_slash.add(brand_name.lower())

                    brand_data = section_data[brand_name]
                    if isinstance(brand_data, dict):
                        for model_name in brand_data.keys():
                            if "/" in model_name:
                                brands_with_slash.add(model_name.lower())

            return brands_with_slash

        except Exception:
            return set()

    # ------------------------------------------------------------------
    # Delimiter-type mapping: translate text_splitter priorities/delimiters
    # into the legacy delimiter_type strings that existing tests expect.
    # ------------------------------------------------------------------

    _DELIMITER_TYPE_MAP = {
        # high-priority smart delimiters → "high_reliability"
        " w/ ": "high_reliability",
        " w/": "high_reliability",
        " W/ ": "high_reliability",
        " W/": "high_reliability",
        " with ": "high_reliability",
        # positional delimiter → "handle_primary"
        " in ": "handle_primary",
    }

    @staticmethod
    def _classify_delimiter(candidate) -> str:
        """Map a SplitCandidate to the legacy delimiter_type string."""
        dt = BrushSplitter._DELIMITER_TYPE_MAP.get(candidate.delimiter)
        if dt:
            return dt
        # ' x ' / ' X ' collaboration → "smart_analysis"
        if candidate.delimiter.strip().lower() == "x":
            return "smart_analysis"
        if candidate.priority == "medium":
            if candidate.delimiter in ("/", " ("):
                return "medium_reliability"
            return "smart_analysis"
        return "high_reliability"

    def split_handle_and_knot(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split handle and knot using various delimiters.

        Delegates ALL splitting logic to text_splitter.split_on_delimiters.
        The known-brush guard (Step 2) is the only thing that still lives here
        because it needs the strategy instances.
        """
        if not text:
            return None, None, None

        text = normalize_text(text)

        # Step 1: Try high-priority delimiters
        candidates = split_on_delimiters(text, self._brands_with_slash)
        high = [c for c in candidates if c.priority == "high"]
        if high:
            c = high[0]
            return c.handle_text, c.knot_text, self._classify_delimiter(c)

        # Step 2: Known-brush check (requires strategy instances)
        if self._is_known_brush(text):
            return None, None, None

        # Step 3: Try medium-priority delimiters
        medium = [c for c in candidates if c.priority == "medium"]
        if medium:
            c = medium[0]
            return c.handle_text, c.knot_text, self._classify_delimiter(c)

        # No split found
        if not candidates:
            return None, None, "not_known_brush"

        return None, None, None

    def _is_known_brush(self, text: str) -> bool:
        """Check if the text matches a known brush in the catalog."""
        if not self.strategies:
            return False

        for strategy in self.strategies:
            try:
                result = strategy.match(text)
                if result and (
                    (isinstance(result, dict) and result.get("matched"))
                    or (isinstance(result, dict) and result.get("brand"))
                    or (hasattr(result, "matched") and getattr(result, "matched", None))
                ):
                    return True
            except (AttributeError, KeyError, TypeError, re.error):
                continue
        return False
