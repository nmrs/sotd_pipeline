"""
Brush scoring configuration system.

This module handles loading and validation of brush scoring configuration
from YAML files, providing a centralized configuration system for the
multi-strategy brush scoring system.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from sotd.match.types import ValidationResult


class BrushScoringConfig:
    """
    Configuration loader and validator for brush scoring system.

    Loads configuration from YAML files and provides validated access
    to scoring weights, bonus factors, penalty factors, and routing rules.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration loader.

        Args:
            config_path: Path to configuration YAML file. If None, uses default path.
        """
        if config_path is None:
            config_path = Path("data/brush_scoring_config.yaml")

        self.config_path = config_path
        self._config_data: Optional[Dict[str, Any]] = None
        self._validation_result: Optional[ValidationResult] = None

    def load_config(self) -> ValidationResult:
        """Load and validate configuration from YAML file.

        Returns:
            ValidationResult indicating success/failure and any errors.
        """
        try:
            if not self.config_path.exists():
                return ValidationResult(
                    is_valid=False, errors=[f"Configuration file not found: {self.config_path}"]
                )

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config_data = yaml.safe_load(f)

            # Validate configuration structure
            validation_result = self._validate_config_structure()
            if not validation_result.is_valid:
                return validation_result

            # Validate configuration values
            validation_result = self._validate_config_values()
            if not validation_result.is_valid:
                return validation_result

            self._validation_result = ValidationResult(is_valid=True)
            return self._validation_result

        except yaml.YAMLError as e:
            return ValidationResult(is_valid=False, errors=[f"YAML parsing error: {str(e)}"])
        except Exception as e:
            return ValidationResult(
                is_valid=False, errors=[f"Configuration loading error: {str(e)}"]
            )

    def _validate_config_structure(self) -> ValidationResult:
        """Validate that required configuration sections exist.

        Returns:
            ValidationResult indicating structure validity.
        """
        if not self._config_data:
            return ValidationResult(is_valid=False, errors=["No configuration data loaded"])

        required_sections = [
            "base_strategy_scores",
            "bonus_factors",
            "penalty_factors",
            "routing_rules",
            "performance",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in self._config_data:
                missing_sections.append(section)

        if missing_sections:
            return ValidationResult(
                is_valid=False,
                errors=[f"Missing required configuration sections: {missing_sections}"],
            )

        return ValidationResult(is_valid=True)

    def _validate_config_values(self) -> ValidationResult:
        """Validate configuration values are within expected ranges.

        Returns:
            ValidationResult indicating value validity.
        """
        if not self._config_data:
            return ValidationResult(is_valid=False, errors=["No configuration data loaded"])

        errors = []

        # Validate base strategy scores are positive numbers
        base_scores = self._config_data.get("base_strategy_scores", {})
        for strategy, score in base_scores.items():
            if not isinstance(score, (int, float)) or score < 0:
                errors.append(f"Invalid base strategy score for {strategy}: {score}")

        # Validate bonus factors are non-negative numbers
        bonus_factors = self._config_data.get("bonus_factors", {})
        for factor, value in bonus_factors.items():
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"Invalid bonus factor for {factor}: {value}")

        # Validate penalty factors are non-positive numbers
        penalty_factors = self._config_data.get("penalty_factors", {})
        for factor, value in penalty_factors.items():
            if not isinstance(value, (int, float)) or value > 0:
                errors.append(f"Invalid penalty factor for {factor}: {value}")

        # Validate routing rules
        routing_rules = self._config_data.get("routing_rules", {})
        if not isinstance(routing_rules.get("minimum_score_threshold"), (int, float)):
            errors.append("Invalid minimum_score_threshold in routing_rules")

        if not isinstance(routing_rules.get("max_strategies_to_run"), int):
            errors.append("Invalid max_strategies_to_run in routing_rules")

        # Validate performance settings
        performance = self._config_data.get("performance", {})
        if not isinstance(performance.get("cache_ttl_seconds"), (int, float)):
            errors.append("Invalid cache_ttl_seconds in performance")

        if not isinstance(performance.get("max_cache_size"), int):
            errors.append("Invalid max_cache_size in performance")

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True)

    def get_base_strategy_score(self, strategy_name: str) -> float:
        """Get base score for a strategy.

        Args:
            strategy_name: Name of the strategy.

        Returns:
            Base score for the strategy, or 0.0 if not found.
        """
        if not self._config_data:
            return 0.0

        return self._config_data["base_strategy_scores"].get(strategy_name, 0.0)

    def get_bonus_factor(self, factor_name: str) -> float:
        """Get bonus factor value.

        Args:
            factor_name: Name of the bonus factor.

        Returns:
            Bonus factor value, or 0.0 if not found.
        """
        if not self._config_data:
            return 0.0

        return self._config_data["bonus_factors"].get(factor_name, 0.0)

    def get_penalty_factor(self, factor_name: str) -> float:
        """Get penalty factor value.

        Args:
            factor_name: Name of the penalty factor.

        Returns:
            Penalty factor value, or 0.0 if not found.
        """
        if not self._config_data:
            return 0.0

        return self._config_data["penalty_factors"].get(factor_name, 0.0)

    def get_routing_rule(self, rule_name: str) -> Any:
        """Get routing rule value.

        Args:
            rule_name: Name of the routing rule.

        Returns:
            Routing rule value, or None if not found.
        """
        if not self._config_data:
            return None

        return self._config_data["routing_rules"].get(rule_name)

    def get_performance_setting(self, setting_name: str) -> Any:
        """Get performance setting value.

        Args:
            setting_name: Name of the performance setting.

        Returns:
            Performance setting value, or None if not found.
        """
        if not self._config_data:
            return None

        return self._config_data["performance"].get(setting_name)

    def reload_config(self) -> ValidationResult:
        """Reload configuration from file.

        Returns:
            ValidationResult indicating success/failure.
        """
        self._config_data = None
        self._validation_result = None
        return self.load_config()

    @property
    def is_loaded(self) -> bool:
        """Check if configuration is loaded and valid.

        Returns:
            True if configuration is loaded and valid.
        """
        return (
            self._config_data is not None
            and self._validation_result is not None
            and self._validation_result.is_valid
        )

    @property
    def validation_result(self) -> Optional[ValidationResult]:
        """Get the last validation result.

        Returns:
            ValidationResult from last load/reload operation.
        """
        return self._validation_result
