"""
Compatibility module for legacy BrushMatcherConfig.

This module provides backward compatibility for tests and tools that expect
the old BrushMatcherConfig interface.
"""

from pathlib import Path
from typing import Optional


class BrushMatcherConfig:
    """Compatibility class for legacy BrushMatcherConfig interface."""

    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        handles_path: Optional[Path] = None,
        knots_path: Optional[Path] = None,
        bypass_correct_matches: bool = False,
        brush_scoring_config_path: Optional[Path] = None,
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.knots_path = knots_path
        self.bypass_correct_matches = bypass_correct_matches
        self.brush_scoring_config_path = brush_scoring_config_path

    @classmethod
    def create_default(cls) -> "BrushMatcherConfig":
        """Create a default configuration for backward compatibility."""
        return cls(
            catalog_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            bypass_correct_matches=False,
            brush_scoring_config_path=Path("data/brush_scoring_config.yaml"),
        )

    @classmethod
    def create_custom(
        cls,
        catalog_path: Path,
        handles_path: Path,
        knots_path: Path,
        correct_matches_path: Path,
        debug: bool = False,
    ) -> "BrushMatcherConfig":
        """Create a custom configuration with specific paths."""
        return cls(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            bypass_correct_matches=False,
            brush_scoring_config_path=Path("data/brush_scoring_config.yaml"),
        )

    @classmethod
    def create_debug(cls) -> "BrushMatcherConfig":
        """Create a debug configuration for development and testing."""
        return cls(
            catalog_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            bypass_correct_matches=False,
            brush_scoring_config_path=Path("data/brush_scoring_config.yaml"),
        )
