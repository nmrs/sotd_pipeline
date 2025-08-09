"""
Brush Configuration Updater.

This module provides configuration update workflow capabilities for the brush
learning system, applying ChatGPT suggestions to the brush scoring configuration
with validation, backup, and rollback capabilities.
"""

import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class BrushConfigurationUpdater:
    """
    Configuration updater for brush scoring system.

    This class applies ChatGPT suggestions to the brush scoring configuration,
    providing validation, backup, and rollback capabilities for safe
    configuration management.
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize the configuration updater.

        Args:
            config_path: Path to the brush scoring configuration file

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is corrupted
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Validate that the file can be loaded
        try:
            self.load_configuration()
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Corrupted configuration file: {e}")

    def load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dictionary containing the configuration data

        Raises:
            yaml.YAMLError: If configuration file is corrupted
        """
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def save_configuration(self, config: Dict[str, Any], preserve_formatting: bool = True) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save
            preserve_formatting: Whether to preserve comments and formatting

        Returns:
            True if successful, False otherwise
        """
        try:
            if preserve_formatting:
                # Try to preserve existing comments and structure
                original_content = ""
                if self.config_path.exists():
                    with open(self.config_path, "r") as f:
                        original_content = f.read()

                # Extract comments from original content
                header_comments = self._extract_header_comments(original_content)

                # Generate new YAML content
                new_content = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

                # Prepend header comments if they exist
                if header_comments:
                    new_content = header_comments + "\n" + new_content

                with open(self.config_path, "w") as f:
                    f.write(new_content)
            else:
                with open(self.config_path, "w") as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def _extract_header_comments(self, content: str) -> str:
        """
        Extract header comments from YAML content.

        Args:
            content: Original YAML content

        Returns:
            Header comments as a string
        """
        lines = content.split("\n")
        header_comments = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped == "":
                header_comments.append(line)
            else:
                # Stop at first non-comment, non-empty line
                break

        # Remove trailing empty lines
        while header_comments and header_comments[-1].strip() == "":
            header_comments.pop()

        return "\n".join(header_comments)

    def apply_weight_adjustments(self, adjustments: Dict[str, Any]) -> bool:
        """
        Apply base strategy weight adjustments to configuration.

        Args:
            adjustments: Dictionary containing weight adjustments

        Returns:
            True if successful, False otherwise
        """
        if "weight_adjustments" not in adjustments:
            return True  # No weight adjustments to apply

        try:
            config = self.load_configuration()
            weight_updates = adjustments["weight_adjustments"]

            if "brush_scoring_weights" not in config:
                logger.error("Invalid configuration structure: missing brush_scoring_weights")
                return False

            if "base_strategies" not in config["brush_scoring_weights"]:
                logger.error("Invalid configuration structure: missing base_strategies")
                return False

            base_strategies = config["brush_scoring_weights"]["base_strategies"]

            # Apply weight adjustments
            any_invalid = False
            for strategy, new_weight in weight_updates.items():
                # Validate weight value
                if not self._validate_weight_value(new_weight):
                    logger.warning(f"Invalid weight value for {strategy}: {new_weight}")
                    any_invalid = True
                    continue

                # Only update existing strategies
                if strategy in base_strategies:
                    base_strategies[strategy] = float(new_weight)
                    logger.info(f"Updated {strategy} weight to {new_weight}")
                else:
                    logger.warning(f"Unknown strategy {strategy}, skipping")

            # If there were any invalid weights, don't save the config
            if any_invalid and len(
                [w for w in weight_updates.values() if not self._validate_weight_value(w)]
            ) == len(weight_updates):
                # All weights were invalid
                return False
            elif any_invalid:
                # Some weights were invalid, but we applied the valid ones
                logger.warning("Some weight adjustments were skipped due to invalid values")

            return self.save_configuration(config)

        except Exception as e:
            logger.error(f"Failed to apply weight adjustments: {e}")
            return False

    def apply_modifier_adjustments(self, adjustments: Dict[str, Any]) -> bool:
        """
        Apply modifier weight adjustments to configuration.

        Args:
            adjustments: Dictionary containing modifier adjustments

        Returns:
            True if successful, False otherwise
        """
        if "modifier_adjustments" not in adjustments:
            return True  # No modifier adjustments to apply

        try:
            config = self.load_configuration()
            modifier_updates = adjustments["modifier_adjustments"]

            if (
                "brush_scoring_weights" not in config
                or "strategy_modifiers" not in config["brush_scoring_weights"]
            ):
                logger.error("Invalid configuration structure: missing strategy_modifiers")
                return False

            strategy_modifiers = config["brush_scoring_weights"]["strategy_modifiers"]

            # Apply modifier adjustments to all strategies that have the modifier
            for modifier_name, adjustment_value in modifier_updates.items():
                # Validate adjustment value (can be positive or negative)
                if not isinstance(adjustment_value, (int, float)):
                    logger.warning(
                        f"Invalid modifier adjustment value for {modifier_name}: {adjustment_value}"
                    )
                    continue

                # Update modifier in all strategies that have it
                for strategy_name, modifiers in strategy_modifiers.items():
                    if modifier_name in modifiers:
                        modifiers[modifier_name] = float(adjustment_value)
                        logger.info(
                            f"Updated {strategy_name}.{modifier_name} to {adjustment_value}"
                        )

            return self.save_configuration(config)

        except Exception as e:
            logger.error(f"Failed to apply modifier adjustments: {e}")
            return False

    def apply_new_modifiers(self, adjustments: Dict[str, Any]) -> bool:
        """
        Apply new modifier suggestions to configuration.

        Args:
            adjustments: Dictionary containing new modifier suggestions

        Returns:
            True if successful, False otherwise
        """
        if "suggested_new_modifiers" not in adjustments:
            return True  # No new modifiers to apply

        try:
            config = self.load_configuration()
            new_modifiers = adjustments["suggested_new_modifiers"]

            if (
                "brush_scoring_weights" not in config
                or "strategy_modifiers" not in config["brush_scoring_weights"]
            ):
                logger.error("Invalid configuration structure: missing strategy_modifiers")
                return False

            strategy_modifiers = config["brush_scoring_weights"]["strategy_modifiers"]

            # Apply new modifiers
            for modifier_spec in new_modifiers:
                modifier_name = modifier_spec.get("name")
                suggested_weights = modifier_spec.get("suggested_weights", {})

                if not modifier_name:
                    logger.warning("Modifier specification missing name")
                    continue

                # Add modifier to specified strategies
                for strategy_name, weight in suggested_weights.items():
                    if strategy_name in strategy_modifiers:
                        # Validate weight value
                        if isinstance(weight, (int, float)):
                            strategy_modifiers[strategy_name][modifier_name] = float(weight)
                            logger.info(
                                f"Added new modifier {modifier_name} to {strategy_name} with weight {weight}"
                            )
                        else:
                            logger.warning(
                                f"Invalid weight for {modifier_name} in {strategy_name}: {weight}"
                            )
                    else:
                        logger.warning(
                            f"Unknown strategy {strategy_name} for modifier {modifier_name}"
                        )

            return self.save_configuration(config)

        except Exception as e:
            logger.error(f"Failed to apply new modifiers: {e}")
            return False

    def apply_chatgpt_suggestions(self, suggestions: Dict[str, Any]) -> bool:
        """
        Apply comprehensive ChatGPT suggestions to configuration.

        Args:
            suggestions: Dictionary containing all types of suggestions

        Returns:
            True if all suggestions applied successfully, False otherwise
        """
        try:
            # Create backup before making changes
            backup_path = self.create_backup()
            if not backup_path:
                logger.error("Failed to create backup, aborting configuration update")
                return False

            logger.info(f"Created configuration backup: {backup_path}")

            # Apply all types of adjustments
            success = True

            if not self.apply_weight_adjustments(suggestions):
                logger.error("Failed to apply weight adjustments")
                success = False

            if not self.apply_modifier_adjustments(suggestions):
                logger.error("Failed to apply modifier adjustments")
                success = False

            if not self.apply_new_modifiers(suggestions):
                logger.error("Failed to apply new modifiers")
                success = False

            if success:
                # Validate the final configuration
                updated_config = self.load_configuration()
                if not self.validate_configuration(updated_config):
                    logger.error("Updated configuration failed validation, rolling back")
                    self.rollback_configuration()
                    return False

                logger.info("Successfully applied all ChatGPT suggestions")
                return True
            else:
                logger.error("Some suggestions failed to apply, rolling back")
                self.rollback_configuration()
                return False

        except Exception as e:
            logger.error(f"Failed to apply ChatGPT suggestions: {e}")
            # Attempt rollback
            self.rollback_configuration()
            return False

    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure and values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check basic structure
            if not isinstance(config, dict):
                return False

            if "brush_scoring_weights" not in config:
                return False

            brush_weights = config["brush_scoring_weights"]

            if "base_strategies" not in brush_weights:
                return False

            if "strategy_modifiers" not in brush_weights:
                return False

            # Validate base strategies
            base_strategies = brush_weights["base_strategies"]
            if not isinstance(base_strategies, dict) or len(base_strategies) == 0:
                return False

            # Check that all base strategy weights are valid numbers
            for strategy, weight in base_strategies.items():
                if not self._validate_weight_value(weight):
                    return False

            # Validate strategy modifiers structure
            strategy_modifiers = brush_weights["strategy_modifiers"]
            if not isinstance(strategy_modifiers, dict):
                return False

            # Check modifier values
            for strategy_name, modifiers in strategy_modifiers.items():
                if not isinstance(modifiers, dict):
                    return False

                for modifier_name, value in modifiers.items():
                    if not isinstance(value, (int, float)):
                        return False

            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def create_backup(self) -> Optional[Path]:
        """
        Create backup of current configuration.

        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_suffix(f".yaml.backup.{timestamp}")

            shutil.copy2(self.config_path, backup_path)
            logger.info(f"Created configuration backup: {backup_path}")

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def rollback_configuration(self) -> bool:
        """
        Rollback to most recent backup configuration.

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Find most recent backup
            backup_pattern = f"{self.config_path.stem}.yaml.backup.*"
            backup_files = list(self.config_path.parent.glob(backup_pattern))

            if not backup_files:
                logger.error("No backup files found for rollback")
                return False

            # Get most recent backup (sorted by name which includes timestamp)
            most_recent_backup = sorted(backup_files)[-1]

            # Restore from backup
            shutil.copy2(most_recent_backup, self.config_path)
            logger.info(f"Rolled back configuration from: {most_recent_backup}")

            return True

        except Exception as e:
            logger.error(f"Failed to rollback configuration: {e}")
            return False

    def preview_changes(self, adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview what changes would be made without applying them.

        Args:
            adjustments: Dictionary containing proposed adjustments

        Returns:
            Dictionary showing old vs new values for each change
        """
        changes = {"weight_adjustments": {}, "modifier_adjustments": {}, "new_modifiers": []}

        try:
            config = self.load_configuration()

            # Preview weight adjustments
            if "weight_adjustments" in adjustments:
                base_strategies = config.get("brush_scoring_weights", {}).get("base_strategies", {})
                for strategy, new_weight in adjustments["weight_adjustments"].items():
                    if strategy in base_strategies:
                        changes["weight_adjustments"][strategy] = {
                            "old": base_strategies[strategy],
                            "new": new_weight,
                        }

            # Preview modifier adjustments
            if "modifier_adjustments" in adjustments:
                strategy_modifiers = config.get("brush_scoring_weights", {}).get(
                    "strategy_modifiers", {}
                )
                for modifier_name, adjustment_value in adjustments["modifier_adjustments"].items():
                    for strategy_name, modifiers in strategy_modifiers.items():
                        if modifier_name in modifiers:
                            key = f"{strategy_name}.{modifier_name}"
                            changes["modifier_adjustments"][key] = {
                                "old": modifiers[modifier_name],
                                "new": adjustment_value,
                            }

            # Preview new modifiers
            if "suggested_new_modifiers" in adjustments:
                changes["new_modifiers"] = adjustments["suggested_new_modifiers"]

            return changes

        except Exception as e:
            logger.error(f"Failed to preview changes: {e}")
            return changes

    def _validate_weight_value(self, weight: Any) -> bool:
        """
        Validate that a weight value is acceptable.

        Args:
            weight: Weight value to validate

        Returns:
            True if weight is valid, False otherwise
        """
        # Weight must be a number
        if not isinstance(weight, (int, float)):
            return False

        # Base strategy weights should be non-negative
        # (modifiers can be negative)
        if weight < 0:
            return False

        # Reasonable upper bound
        if weight > 1000:
            return False

        return True
