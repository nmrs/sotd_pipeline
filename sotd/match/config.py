"""
Configuration management for brush matching system.

This module provides a centralized configuration system for the brush matcher,
replacing hard-coded paths and settings with a flexible, type-safe configuration.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BrushMatcherConfig:
    """
    Configuration for the brush matcher system.

    This dataclass provides type-safe configuration with automatic validation
    and support for both default and custom configurations.
    """

    # Catalog file paths
    catalog_path: Path = field(default_factory=lambda: Path("data/brushes.yaml"))
    handles_path: Path = field(default_factory=lambda: Path("data/handles.yaml"))
    knots_path: Path = field(default_factory=lambda: Path("data/knots.yaml"))
    correct_matches_path: Path = field(default_factory=lambda: Path("data/correct_matches.yaml"))

    # Debug and performance settings
    debug: bool = False
    cache_enabled: bool = True
    cache_max_size: int = 1000

    # Validation settings
    strict_validation: bool = False

    # Testing and validation settings
    bypass_correct_matches: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_paths()
        self._validate_settings()

    def _validate_paths(self) -> None:
        """Validate that all required paths are provided."""
        if not self.catalog_path:
            raise ValueError("catalog_path is required")
        if not self.handles_path:
            raise ValueError("handles_path is required")
        if not self.knots_path:
            raise ValueError("knots_path is required")
        if not self.correct_matches_path:
            raise ValueError("correct_matches_path is required")

    def _validate_settings(self) -> None:
        """Validate configuration settings."""
        if self.cache_max_size < 1:
            raise ValueError("cache_max_size must be at least 1")

    def get_cache_config(self) -> dict:
        """Get cache configuration as a dictionary."""
        return {
            "enabled": self.cache_enabled,
            "max_size": self.cache_max_size,
        }

    def get_catalog_paths(self) -> dict[str, Path]:
        """Get all catalog paths as a dictionary."""
        return {
            "catalog": self.catalog_path,
            "handles": self.handles_path,
            "knots": self.knots_path,
            "correct_matches": self.correct_matches_path,
        }

    def validate_paths_exist(self) -> None:
        """Validate that all catalog files exist."""
        missing_paths = []

        for name, path in self.get_catalog_paths().items():
            if not path.exists():
                missing_paths.append(f"{name}: {path}")

        if missing_paths:
            raise FileNotFoundError("Missing required catalog files:\n" + "\n".join(missing_paths))

    def get_debug_info(self) -> dict:
        """Get debug information about the configuration."""
        return {
            "debug": self.debug,
            "strict_validation": self.strict_validation,
            "cache_enabled": self.cache_enabled,
            "cache_max_size": self.cache_max_size,
            "paths": {name: str(path) for name, path in self.get_catalog_paths().items()},
        }

    @classmethod
    def create_default(cls) -> "BrushMatcherConfig":
        """Create a default configuration."""
        return cls()

    @classmethod
    def create_debug(cls) -> "BrushMatcherConfig":
        """Create a debug configuration."""
        return cls(debug=True, strict_validation=True)

    @classmethod
    def create_custom(
        cls,
        catalog_path: Optional[Path] = None,
        handles_path: Optional[Path] = None,
        knots_path: Optional[Path] = None,
        correct_matches_path: Optional[Path] = None,
        debug: bool = False,
        cache_enabled: bool = True,
        cache_max_size: int = 1000,
        strict_validation: bool = False,
    ) -> "BrushMatcherConfig":
        """Create a custom configuration with optional overrides."""
        return cls(
            catalog_path=catalog_path or Path("data/brushes.yaml"),
            handles_path=handles_path or Path("data/handles.yaml"),
            knots_path=knots_path or Path("data/knots.yaml"),
            correct_matches_path=correct_matches_path or Path("data/correct_matches.yaml"),
            debug=debug,
            cache_enabled=cache_enabled,
            cache_max_size=cache_max_size,
            strict_validation=strict_validation,
        )
