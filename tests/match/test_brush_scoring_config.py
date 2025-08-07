"""
Unit tests for BrushScoringConfig.

Tests the YAML-based configuration system for brush scoring weights and criteria.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from sotd.match.brush_scoring_config import BrushScoringConfig


class TestBrushScoringConfig:
    """Test the BrushScoringConfig class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        config = BrushScoringConfig()
        assert config.config_path is not None
        assert config.weights is not None
        assert "base_strategies" in config.weights
        assert "strategy_modifiers" in config.weights

    def test_init_with_custom_config_path(self):
        """Test initialization with custom config path."""
        custom_path = Path("/test/config.yaml")
        config = BrushScoringConfig(config_path=custom_path)
        assert config.config_path == custom_path

    def test_load_config_from_file(self):
        """Test loading configuration from YAML file."""
        test_config = {
            "brush_scoring_weights": {
                "base_strategies": {
                    "correct_complete_brush": 90.0,
                    "correct_split_brush": 85.0,
                    "known_split": 80.0,
                },
                "strategy_modifiers": {
                    "high_priority_automated_split": {"multiple_brands": 0.0, "fiber_words": 0.0}
                },
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(test_config))):
            config = BrushScoringConfig()
            config.load_config()

            assert config.weights["base_strategies"]["correct_complete_brush"] == 90.0
            assert config.weights["base_strategies"]["correct_split_brush"] == 85.0
            assert (
                config.weights["strategy_modifiers"]["high_priority_automated_split"][
                    "multiple_brands"
                ]
                == 0.0
            )

    def test_get_base_strategy_score(self):
        """Test getting base strategy score."""
        config = BrushScoringConfig()
        score = config.get_base_strategy_score("correct_complete_brush")
        assert isinstance(score, float)
        assert score > 0

    def test_get_strategy_modifier(self):
        """Test getting strategy modifier value."""
        config = BrushScoringConfig()
        modifier = config.get_strategy_modifier("high_priority_automated_split", "multiple_brands")
        assert isinstance(modifier, float)

    def test_get_strategy_modifier_nonexistent(self):
        """Test getting non-existent strategy modifier."""
        config = BrushScoringConfig()
        modifier = config.get_strategy_modifier("nonexistent_strategy", "nonexistent_modifier")
        assert modifier == 0.0  # Default value

    def test_validate_config_structure(self):
        """Test configuration structure validation."""
        config = BrushScoringConfig()

        # Valid config should not raise
        config.validate_config_structure()

        # Invalid config should raise
        config.weights = {"invalid": "structure"}
        with pytest.raises(ValueError, match="Invalid configuration structure"):
            config.validate_config_structure()

    def test_validate_config_values(self):
        """Test configuration values validation."""
        config = BrushScoringConfig()

        # Valid values should not raise
        config.validate_config_values()

        # Invalid values should raise
        config.weights["base_strategies"]["correct_complete_brush"] = "invalid"
        with pytest.raises(ValueError, match="Invalid score value"):
            config.validate_config_values()

    def test_hot_reload_config(self):
        """Test hot-reloading configuration."""
        config = BrushScoringConfig()
        original_score = config.get_base_strategy_score("correct_complete_brush")

        # Simulate config change
        new_config = {
            "brush_scoring_weights": {
                "base_strategies": {"correct_complete_brush": original_score + 10.0},
                "strategy_modifiers": config.weights["strategy_modifiers"],
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(new_config))):
            config.load_config()
            new_score = config.get_base_strategy_score("correct_complete_brush")
            assert new_score == original_score + 10.0

    def test_initial_weights_mimic_current_behavior(self):
        """Test that initial weights mimic current behavior exactly."""
        config = BrushScoringConfig()

        # Check that base strategy scores are in expected order
        scores = [
            config.get_base_strategy_score("correct_complete_brush"),
            config.get_base_strategy_score("correct_split_brush"),
            config.get_base_strategy_score("known_split"),
            config.get_base_strategy_score("high_priority_automated_split"),
            config.get_base_strategy_score("complete_brush"),
            config.get_base_strategy_score("dual_component"),
            config.get_base_strategy_score("medium_priority_automated_split"),
            config.get_base_strategy_score("single_component_fallback"),
        ]

        # Verify descending order (highest priority first)
        assert scores == sorted(scores, reverse=True)

    def test_error_handling_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(yaml.YAMLError):
                BrushScoringConfig()

    def test_error_handling_missing_file(self):
        """Test error handling for missing config file."""
        config = BrushScoringConfig(config_path=Path("/nonexistent/config.yaml"))
        with pytest.raises(FileNotFoundError):
            config.load_config()

    def test_get_all_strategy_names(self):
        """Test getting all strategy names from configuration."""
        config = BrushScoringConfig()
        strategy_names = config.get_all_strategy_names()

        expected_strategies = [
            "correct_complete_brush",
            "correct_split_brush",
            "known_split",
            "high_priority_automated_split",
            "complete_brush",
            "dual_component",
            "medium_priority_automated_split",
            "single_component_fallback",
        ]

        for strategy in expected_strategies:
            assert strategy in strategy_names

    def test_get_all_modifier_names(self):
        """Test getting all modifier names for a strategy."""
        config = BrushScoringConfig()
        modifier_names = config.get_all_modifier_names("high_priority_automated_split")

        expected_modifiers = ["multiple_brands", "fiber_words", "size_specification"]

        for modifier in expected_modifiers:
            assert modifier in modifier_names

    def test_config_persistence(self):
        """Test that configuration changes persist."""
        config = BrushScoringConfig()
        original_score = config.get_base_strategy_score("correct_complete_brush")

        # Change the score
        config.weights["base_strategies"]["correct_complete_brush"] = original_score + 5.0

        # Verify the change persists
        new_score = config.get_base_strategy_score("correct_complete_brush")
        assert new_score == original_score + 5.0
