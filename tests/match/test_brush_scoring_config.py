"""
Unit tests for brush scoring configuration system.

Tests the BrushScoringConfig class for loading, validation, and access
to brush scoring configuration from YAML files.
"""

import tempfile
import yaml
from pathlib import Path

from sotd.match.brush_scoring_config import BrushScoringConfig
from sotd.match.types import ValidationResult


class TestBrushScoringConfig:
    """Test cases for BrushScoringConfig class."""

    def test_init_with_default_path(self):
        """Test initialization with default config path."""
        config = BrushScoringConfig()
        assert config.config_path == Path("data/brush_scoring_config.yaml")
        assert config._config_data is None
        assert config._validation_result is None

    def test_init_with_custom_path(self):
        """Test initialization with custom config path."""
        custom_path = Path("/custom/path/config.yaml")
        config = BrushScoringConfig(custom_path)
        assert config.config_path == custom_path

    def test_load_config_success(self):
        """Test successful configuration loading."""
        valid_config = {
            "base_strategy_scores": {"complete_brush": 100.0, "dual_component": 90.0},
            "bonus_factors": {"delimiters_present": 10.0, "brand_match": 15.0},
            "penalty_factors": {"single_brand_only": -15.0, "no_fiber_detected": -10.0},
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "max_cache_size": 10000,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(valid_config, f)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)
            result = config.load_config()

            assert result.is_valid
            assert not result.errors
            assert config.is_loaded
            assert config._config_data == valid_config
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test configuration loading when file doesn't exist."""
        non_existent_path = Path("/non/existent/config.yaml")
        config = BrushScoringConfig(non_existent_path)
        result = config.load_config()

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert not config.is_loaded

    def test_load_config_invalid_yaml(self):
        """Test configuration loading with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)
            result = config.load_config()

            assert not result.is_valid
            assert len(result.errors) == 1
            assert "YAML parsing error" in result.errors[0]
            assert not config.is_loaded
        finally:
            config_path.unlink()

    def test_load_config_missing_sections(self):
        """Test configuration loading with missing required sections."""
        incomplete_config = {
            "base_strategy_scores": {"complete_brush": 100.0}
            # Missing other required sections
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(incomplete_config, f)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)
            result = config.load_config()

            assert not result.is_valid
            assert len(result.errors) == 1
            assert "Missing required configuration sections" in result.errors[0]
            assert not config.is_loaded
        finally:
            config_path.unlink()

    def test_load_config_invalid_values(self):
        """Test configuration loading with invalid values."""
        invalid_config = {
            "base_strategy_scores": {
                "complete_brush": -100.0,  # Invalid: negative score
                "dual_component": "invalid",  # Invalid: string instead of number
            },
            "bonus_factors": {"delimiters_present": -10.0},  # Invalid: negative bonus
            "penalty_factors": {"single_brand_only": 15.0},  # Invalid: positive penalty
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": "invalid",  # Invalid: string
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": "invalid",  # Invalid: string
                "max_cache_size": 10000,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)
            result = config.load_config()

            assert not result.is_valid
            assert len(result.errors) >= 5  # Multiple validation errors
            assert not config.is_loaded
        finally:
            config_path.unlink()

    def test_get_base_strategy_score(self):
        """Test getting base strategy scores."""
        config_data = {
            "base_strategy_scores": {"complete_brush": 100.0, "dual_component": 90.0},
            "bonus_factors": {},
            "penalty_factors": {},
            "routing_rules": {},
            "performance": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_base_strategy_score("complete_brush") == 100.0
        assert config.get_base_strategy_score("dual_component") == 90.0
        assert config.get_base_strategy_score("unknown_strategy") == 0.0

    def test_get_bonus_factor(self):
        """Test getting bonus factors."""
        config_data = {
            "base_strategy_scores": {},
            "bonus_factors": {"delimiters_present": 10.0, "brand_match": 15.0},
            "penalty_factors": {},
            "routing_rules": {},
            "performance": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_bonus_factor("delimiters_present") == 10.0
        assert config.get_bonus_factor("brand_match") == 15.0
        assert config.get_bonus_factor("unknown_factor") == 0.0

    def test_get_penalty_factor(self):
        """Test getting penalty factors."""
        config_data = {
            "base_strategy_scores": {},
            "bonus_factors": {},
            "penalty_factors": {"single_brand_only": -15.0, "no_fiber_detected": -10.0},
            "routing_rules": {},
            "performance": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_penalty_factor("single_brand_only") == -15.0
        assert config.get_penalty_factor("no_fiber_detected") == -10.0
        assert config.get_penalty_factor("unknown_factor") == 0.0

    def test_get_routing_rule(self):
        """Test getting routing rules."""
        config_data = {
            "base_strategy_scores": {},
            "bonus_factors": {},
            "penalty_factors": {},
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
            },
            "performance": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_routing_rule("exact_match_bypass") is True
        assert config.get_routing_rule("minimum_score_threshold") == 30.0
        assert config.get_routing_rule("max_strategies_to_run") == 10
        assert config.get_routing_rule("unknown_rule") is None

    def test_get_performance_setting(self):
        """Test getting performance settings."""
        config_data = {
            "base_strategy_scores": {},
            "bonus_factors": {},
            "penalty_factors": {},
            "routing_rules": {},
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "max_cache_size": 10000,
            },
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_performance_setting("enable_caching") is True
        assert config.get_performance_setting("cache_ttl_seconds") == 3600
        assert config.get_performance_setting("max_cache_size") == 10000
        assert config.get_performance_setting("unknown_setting") is None

    def test_get_methods_without_config_loaded(self):
        """Test get methods when configuration is not loaded."""
        config = BrushScoringConfig()

        # All get methods should return safe defaults when config not loaded
        assert config.get_base_strategy_score("any_strategy") == 0.0
        assert config.get_bonus_factor("any_factor") == 0.0
        assert config.get_penalty_factor("any_factor") == 0.0
        assert config.get_routing_rule("any_rule") is None
        assert config.get_performance_setting("any_setting") is None

    def test_reload_config(self):
        """Test configuration reloading."""
        initial_config = {
            "base_strategy_scores": {"complete_brush": 100.0},
            "bonus_factors": {},
            "penalty_factors": {},
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "max_cache_size": 10000,
            },
        }

        updated_config = {
            "base_strategy_scores": {"complete_brush": 200.0},  # Changed value
            "bonus_factors": {},
            "penalty_factors": {},
            "routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "max_cache_size": 10000,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(initial_config, f)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)

            # Load initial config
            result = config.load_config()
            assert result.is_valid
            assert config.get_base_strategy_score("complete_brush") == 100.0

            # Update file content
            with open(config_path, "w") as f:
                yaml.dump(updated_config, f)

            # Reload config
            result = config.reload_config()
            assert result.is_valid
            assert config.get_base_strategy_score("complete_brush") == 200.0
        finally:
            config_path.unlink()

    def test_is_loaded_property(self):
        """Test is_loaded property behavior."""
        config = BrushScoringConfig()

        # Initially not loaded
        assert not config.is_loaded

        # With config data but no validation result
        config._config_data = {"test": "data"}
        assert not config.is_loaded  # Requires both data and valid validation result

        # With invalid validation result
        config._validation_result = ValidationResult(is_valid=False, errors=["test"])
        assert not config.is_loaded

        # With valid validation result
        config._validation_result = ValidationResult(is_valid=True)
        assert config.is_loaded

    def test_validation_result_property(self):
        """Test validation_result property."""
        config = BrushScoringConfig()

        # Initially None
        assert config.validation_result is None

        # After setting validation result
        test_result = ValidationResult(is_valid=True)
        config._validation_result = test_result
        assert config.validation_result == test_result
