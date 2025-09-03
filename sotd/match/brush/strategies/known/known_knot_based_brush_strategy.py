from .base_known_brush_strategy import BaseKnownBrushMatchingStrategy


class KnownKnotBasedBrushMatchingStrategy(BaseKnownBrushMatchingStrategy):
    """
    Strategy for matching known knot-based brush patterns from YAML catalog.

    This strategy handles brushes where the knot is the primary identifier
    (e.g., "DB B3 Chisel & Hound v23") and loads from the known_knot_based_brushes
    section of the catalog. It inherits all functionality from BaseKnownBrushMatchingStrategy.
    """

    def get_strategy_name(self) -> str:
        """Return the strategy name for scoring purposes."""
        return "known_knot_based_brush"
