"""
Brush Scoring Configuration System.

This module provides YAML-based configuration management for brush scoring
weights and criteria, supporting hot-reloading and validation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List


class BrushScoringConfig:
    """
    Configuration manager for brush scoring weights and criteria.

    This class manages YAML-based configuration for brush scoring system,
    including base strategy scores and strategy-specific modifiers.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        if config_path is None:
            config_path = Path("data/brush_scoring_config.yaml")

        self.config_path = config_path
        self.weights = self._get_default_weights()

        # Load configuration if file exists
        if self.config_path.exists():
            self.load_config()

    def _get_default_weights(self) -> Dict[str, Any]:
        """
        Get default weights that mimic current behavior exactly.

        Returns:
            Dictionary containing default weights structure.
        """
        return {
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
                    "handle_confidence": 0.0,
                    "knot_confidence": 0.0,
                    "word_count_balance": 0.0,
                },
                "medium_priority_automated_split": {
                    "multiple_brands": 0.0,
                    "fiber_words": 0.0,
                    "size_specification": 0.0,
                    "handle_confidence": 0.0,
                    "knot_confidence": 0.0,
                    "word_count_balance": 0.0,
                },
                "dual_component": {
                    "multiple_brands": 0.0,
                    "fiber_words": 0.0,
                    "size_specification": 0.0,
                },
                "complete_brush": {
                    "multiple_brands": 0.0,
                    "fiber_words": 0.0,
                    "size_specification": 0.0,
                },
                "single_component_fallback": {
                    "multiple_brands": 0.0,
                    "fiber_words": 0.0,
                    "size_specification": 0.0,
                },
            },
        }

    def load_config(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If configuration structure is invalid
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if "brush_scoring_weights" not in config_data:
            raise ValueError("Configuration must contain 'brush_scoring_weights' section")

        self.weights = config_data["brush_scoring_weights"]
        self.validate_config_structure()
        self.validate_config_values()

    def get_base_strategy_score(self, strategy_name: str) -> float:
        """
        Get base score for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Base score for the strategy, or 0.0 if not found
        """
        return self.weights.get("base_strategies", {}).get(strategy_name, 0.0)

    def get_strategy_modifier(self, strategy_name: str, modifier_name: str) -> float:
        """
        Get modifier value for a strategy.

        Args:
            strategy_name: Name of the strategy
            modifier_name: Name of the modifier

        Returns:
            Modifier value, or 0.0 if not found
        """
        strategy_modifiers = self.weights.get("strategy_modifiers", {}).get(strategy_name, {})
        return strategy_modifiers.get(modifier_name, 0.0)

    def validate_config_structure(self) -> None:
        """
        Validate configuration structure.

        Raises:
            ValueError: If configuration structure is invalid
        """
        if not isinstance(self.weights, dict):
            raise ValueError("Invalid configuration structure: weights must be a dictionary")

        if "base_strategies" not in self.weights:
            raise ValueError("Invalid configuration structure: missing 'base_strategies' section")

        if "strategy_modifiers" not in self.weights:
            raise ValueError(
                "Invalid configuration structure: missing 'strategy_modifiers' section"
            )

        if not isinstance(self.weights["base_strategies"], dict):
            raise ValueError(
                "Invalid configuration structure: 'base_strategies' must be a dictionary"
            )

        if not isinstance(self.weights["strategy_modifiers"], dict):
            raise ValueError(
                "Invalid configuration structure: 'strategy_modifiers' must be a dictionary"
            )

    def validate_config_values(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid
        """
        # Validate base strategy scores
        for strategy_name, score in self.weights["base_strategies"].items():
            if not isinstance(score, (int, float)):
                raise ValueError(f"Invalid score value for strategy '{strategy_name}': {score}")
            if score < 0:
                raise ValueError(
                    f"Score for strategy '{strategy_name}' must be non-negative: {score}"
                )

        # Validate strategy modifiers
        for strategy_name, modifiers in self.weights["strategy_modifiers"].items():
            if not isinstance(modifiers, dict):
                raise ValueError(f"Invalid modifiers for strategy '{strategy_name}': {modifiers}")

            for modifier_name, value in modifiers.items():
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Invalid modifier value '{modifier_name}' for strategy '{strategy_name}': {value}"
                    )

    def get_all_strategy_names(self) -> List[str]:
        """
        Get all strategy names from configuration.

        Returns:
            List of strategy names
        """
        return list(self.weights.get("base_strategies", {}).keys())

    def get_all_modifier_names(self, strategy_name: str) -> List[str]:
        """
        Get all modifier names for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            List of modifier names for the strategy
        """
        strategy_modifiers = self.weights.get("strategy_modifiers", {}).get(strategy_name, {})
        return list(strategy_modifiers.keys())

    def reload_config(self) -> None:
        """
        Reload configuration from file (hot-reload).

        This method allows for runtime configuration updates without
        restarting the application.
        """
        self.load_config()
