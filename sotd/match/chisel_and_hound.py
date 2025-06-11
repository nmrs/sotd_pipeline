"""Matchers for Chisel & Hound shaving brushes,
including pattern definitions and matching logic."""

import re


class ChiselAndHoundBrushMatcher:
    """Matches brush names to Chisel & Hound V9–V25 models using regex patterns."""

    def __init__(self):
        self.patterns = self._build_patterns()

    def _build_patterns(self):
        patterns = []
        # Build patterns for Chisel & Hound V25 down to V10
        for v in range(25, 9, -1):
            for pattern in [
                r"chis.*hou",
                r"chis.*fou",
                r"\bc(?:\&|and|\+)h\b",
            ]:
                regex = f"{pattern}.*v{v}"
                compiled = re.compile(regex, re.IGNORECASE)
                patterns.append(
                    {
                        "compiled": compiled,
                        "pattern": regex,
                        "brand": "Chisel & Hound",
                        "model": f"V{v}",
                        "fiber": "badger",
                        "knot_size_mm": 26.0,
                    }
                )
        return patterns

    def match(self, value):
        """Match the provided value against known Chisel & Hound patterns.

        Args:
            value (str): Input brush description.

        Returns:
            dict: Match result and extracted metadata if matched, else None.
        """
        if not isinstance(value, str):
            return {
                "original": value,
                "matched": None,
                "pattern": None,
                "strategy": "ChiselAndHound",
            }
        normalized = value.strip().lower()
        for entry in self.patterns:
            if entry["compiled"].search(normalized):
                return {
                    "original": value,
                    "matched": {
                        "brand": entry["brand"],
                        "model": entry["model"],
                        "fiber": entry["fiber"],
                        "knot_size_mm": entry["knot_size_mm"],
                        "handle_maker": None,
                        "knot_maker": None,
                        "source_text": value,
                        "source_type": "exact",
                    },
                    "pattern": entry["pattern"],
                    "strategy": "ChiselAndHound",
                }
        return {"original": value, "matched": None, "pattern": None, "strategy": "ChiselAndHound"}
