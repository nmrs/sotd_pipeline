"""
Tests for the brush matcher configuration system.
"""

import pytest
from pathlib import Path

from sotd.match.config import BrushMatcherConfig


class TestBrushMatcherConfig:
    """Test the BrushMatcherConfig class."""

    def test_default_config(self):
        """Test default configuration creation."""
        config = BrushMatcherConfig()

        assert config.catalog_path == Path("data/brushes.yaml")
        assert config.handles_path == Path("data/handles.yaml")
        assert config.knots_path == Path("data/knots.yaml")
        assert config.correct_matches_path == Path("data/correct_matches.yaml")
        assert config.debug is False
        assert config.cache_enabled is True
        assert config.cache_max_size == 1000
        assert config.strict_validation is False

    def test_custom_config(self):
        """Test custom configuration creation."""
        config = BrushMatcherConfig(
            catalog_path=Path("custom/brushes.yaml"),
            handles_path=Path("custom/handles.yaml"),
            knots_path=Path("custom/knots.yaml"),
            correct_matches_path=Path("custom/correct_matches.yaml"),
            debug=True,
            cache_max_size=500,
        )

        assert config.catalog_path == Path("custom/brushes.yaml")
        assert config.handles_path == Path("custom/handles.yaml")
        assert config.knots_path == Path("custom/knots.yaml")
        assert config.correct_matches_path == Path("custom/correct_matches.yaml")
        assert config.debug is True
        assert config.cache_max_size == 500

    def test_create_default_classmethod(self):
        """Test create_default class method."""
        config = BrushMatcherConfig.create_default()

        assert isinstance(config, BrushMatcherConfig)
        assert config.catalog_path == Path("data/brushes.yaml")
        assert config.debug is False

    def test_create_debug_classmethod(self):
        """Test create_debug class method."""
        config = BrushMatcherConfig.create_debug()

        assert isinstance(config, BrushMatcherConfig)
        assert config.debug is True
        assert config.strict_validation is True

    def test_create_custom_classmethod(self):
        """Test create_custom class method."""
        custom_catalog = Path("custom/brushes.yaml")
        config = BrushMatcherConfig.create_custom(
            catalog_path=custom_catalog, debug=True, cache_max_size=2000
        )

        assert config.catalog_path == custom_catalog
        assert config.debug is True
        assert config.cache_max_size == 2000
        # Other paths should use defaults
        assert config.handles_path == Path("data/handles.yaml")

    def test_get_cache_config(self):
        """Test get_cache_config method."""
        config = BrushMatcherConfig(cache_enabled=False, cache_max_size=500)
        cache_config = config.get_cache_config()

        assert cache_config["enabled"] is False
        assert cache_config["max_size"] == 500

    def test_get_catalog_paths(self):
        """Test get_catalog_paths method."""
        config = BrushMatcherConfig()
        paths = config.get_catalog_paths()

        assert paths["catalog"] == Path("data/brushes.yaml")
        assert paths["handles"] == Path("data/handles.yaml")
        assert paths["knots"] == Path("data/knots.yaml")
        assert paths["correct_matches"] == Path("data/correct_matches.yaml")

    def test_get_debug_info(self):
        """Test get_debug_info method."""
        config = BrushMatcherConfig(debug=True, cache_max_size=750)
        debug_info = config.get_debug_info()

        assert debug_info["debug"] is True
        assert debug_info["cache_enabled"] is True
        assert debug_info["cache_max_size"] == 750
        assert debug_info["strict_validation"] is False
        assert "paths" in debug_info

    def test_validation_error_invalid_cache_size(self):
        """Test validation error for invalid cache size."""
        with pytest.raises(ValueError, match="cache_max_size must be at least 1"):
            BrushMatcherConfig(cache_max_size=0)
