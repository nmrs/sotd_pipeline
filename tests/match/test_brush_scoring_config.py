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
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 90.0,
                    "correct_split_brush": 85.0,
                    "known_split": 80.0,
                    "high_priority_automated_split": 75.0,
                    "complete_brush": 70.0,
                    "dual_component": 65.0,
                    "medium_priority_automated_split": 60.0,
                    "single_component_fallback": 55.0,
                },
                "strategy_modifiers": {
                    "high_priority_automated_split": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "medium_priority_automated_split": {
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                    },
                    "dual_component": {
                        "high_priority_delimiter": 0.0,
                        "medium_priority_delimiter": 0.0,
                        "multiple_brands": 0.0,
                        "fiber_words": 0.0,
                        "size_specification": 0.0,
                        "handle_knot_words": 0.0,
                    },
                    "complete_brush": {
                        "high_priority_delimiter": 0.0,
                        "medium_priority_delimiter": 0.0,
                        "multiple_brands": 0.0,
                        "handle_knot_words": 0.0,
                        "fiber_words": 0.0,
                    },
                },
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
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
            "brush_scoring_weights": {
                "base_strategies": {"correct_complete_brush": 90.0},
                "strategy_modifiers": {},
            }
            # Missing brush_routing_rules and performance sections
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
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": -90.0,  # Invalid: negative score
                    "correct_split_brush": "invalid",  # Invalid: string instead of number
                },
                "strategy_modifiers": {
                    "high_priority_automated_split": {
                        "multiple_brands": "invalid",  # Invalid: string instead of number
                    },
                },
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": "invalid",  # Invalid: string
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            config_path = Path(f.name)

        try:
            config = BrushScoringConfig(config_path)
            result = config.load_config()

            assert not result.is_valid
            assert len(result.errors) >= 4  # Multiple validation errors
            assert not config.is_loaded
        finally:
            config_path.unlink()

    def test_get_base_strategy_score(self):
        """Test getting base strategy scores."""
        config_data = {
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 90.0,
                    "correct_split_brush": 85.0,
                },
                "strategy_modifiers": {},
            },
            "brush_routing_rules": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_base_strategy_score("correct_complete_brush") == 90.0
        assert config.get_base_strategy_score("correct_split_brush") == 85.0
        assert config.get_base_strategy_score("unknown_strategy") == 0.0

    def test_get_strategy_modifier(self):
        """Test getting strategy modifiers."""
        config_data = {
            "brush_scoring_weights": {
                "base_strategies": {},
                "strategy_modifiers": {
                    "high_priority_automated_split": {
                        "multiple_brands": 10.0,
                        "fiber_words": 15.0,
                    },
                    "dual_component": {
                        "high_priority_delimiter": 20.0,
                    },
                },
            },
            "brush_routing_rules": {},
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert (
            config.get_strategy_modifier("high_priority_automated_split", "multiple_brands") == 10.0
        )
        assert config.get_strategy_modifier("high_priority_automated_split", "fiber_words") == 15.0
        assert config.get_strategy_modifier("dual_component", "high_priority_delimiter") == 20.0
        assert config.get_strategy_modifier("unknown_strategy", "unknown_modifier") == 0.0

    def test_get_brush_routing_rule(self):
        """Test getting brush routing rules."""
        config_data = {
            "brush_scoring_weights": {
                "base_strategies": {},
                "strategy_modifiers": {},
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
            },
        }

        config = BrushScoringConfig()
        config._config_data = config_data
        config._validation_result = ValidationResult(is_valid=True)

        assert config.get_brush_routing_rule("exact_match_bypass") is True
        assert config.get_brush_routing_rule("minimum_score_threshold") == 30.0
        assert config.get_brush_routing_rule("max_strategies_to_run") == 10
        assert config.get_brush_routing_rule("unknown_rule") is None

    def test_get_methods_without_config_loaded(self):
        """Test get methods when configuration is not loaded."""
        config = BrushScoringConfig()

        # All get methods should return safe defaults when config not loaded
        assert config.get_base_strategy_score("any_strategy") == 0.0
        assert config.get_strategy_modifier("any_strategy", "any_modifier") == 0.0
        assert config.get_brush_routing_rule("any_rule") is None

    def test_reload_config(self):
        """Test configuration reloading."""
        initial_config = {
            "brush_scoring_weights": {
                "base_strategies": {"correct_complete_brush": 90.0},
                "strategy_modifiers": {},
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
            },
        }

        updated_config = {
            "brush_scoring_weights": {
                "base_strategies": {"correct_complete_brush": 200.0},  # Changed value
                "strategy_modifiers": {},
            },
            "brush_routing_rules": {
                "exact_match_bypass": True,
                "minimum_score_threshold": 30.0,
                "max_strategies_to_run": 10,
                "stop_on_good_match": False,
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
            assert config.get_base_strategy_score("correct_complete_brush") == 90.0

            # Update file content
            with open(config_path, "w") as f:
                yaml.dump(updated_config, f)

            # Reload config
            result = config.reload_config()
            assert result.is_valid
            assert config.get_base_strategy_score("correct_complete_brush") == 200.0
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
