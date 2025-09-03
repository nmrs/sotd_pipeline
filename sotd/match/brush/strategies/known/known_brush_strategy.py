from .base_known_brush_strategy import BaseKnownBrushMatchingStrategy


class KnownBrushMatchingStrategy(BaseKnownBrushMatchingStrategy):
    """
    Strategy for matching known brush patterns from YAML catalog.

    This strategy handles complete known brushes and loads from the known_brushes
    section of the catalog. It inherits all functionality from BaseKnownBrushMatchingStrategy.
    """

    def get_strategy_name(self) -> str:
        """Return the strategy name for scoring purposes."""
        return "known_brush"