"""Brush user actions data model and storage for validation tracking."""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .correct_matches_updater import CorrectMatchesUpdater


class ValidationError(Exception):
    """Exception raised for validation errors in brush user actions."""

    pass


@dataclass
class BrushUserAction:
    """Data model for brush user validation actions."""

    input_text: str
    timestamp: datetime
    system_used: str  # "scoring" or "legacy" or "migrated"
    action: str  # "validated" or "overridden"
    system_choice: Dict[str, Any]  # Strategy choice made by system
    user_choice: Dict[str, Any]  # Strategy choice made by user
    all_brush_strategies: List[Dict[str, Any]]  # All strategy results (scoring system only)
    comment_ids: List[str]  # List of comment IDs where this input text was found

    def __post_init__(self):
        """Validate the data after initialization."""
        self._validate()

    def _validate(self):
        """Validate the action data."""
        if self.system_used not in ["scoring", "legacy", "migrated"]:
            raise ValidationError("system_used must be either 'scoring', 'legacy', or 'migrated'")

        if self.action not in ["validated", "overridden"]:
            raise ValidationError("action must be either 'validated' or 'overridden'")

        if not self.input_text.strip():
            raise ValidationError("input_text cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary format for YAML serialization."""
        return {
            "input_text": self.input_text,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "system_used": self.system_used,
            "action": self.action,
            "system_choice": self.system_choice,
            "user_choice": self.user_choice,
            "all_brush_strategies": self.all_brush_strategies,
            "comment_ids": self.comment_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrushUserAction":
        """Create action from dictionary format."""
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)  # Remove timezone for simplicity

        return cls(
            input_text=data["input_text"],
            timestamp=timestamp,
            system_used=data["system_used"],
            action=data["action"],
            system_choice=data["system_choice"],
            user_choice=data["user_choice"],
            all_brush_strategies=data["all_brush_strategies"],
            comment_ids=data.get("comment_ids", []),  # Handle missing field for
            # backward compatibility
        )


class BrushUserActionsStorage:
    """Storage manager for brush user actions in monthly YAML files."""

    def __init__(self, base_path: Path):
        """Initialize storage with base directory path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_monthly_actions(self, month: str, actions: List[BrushUserAction]) -> None:
        """Save actions for a specific month to YAML file."""
        self._validate_month_format(month)

        file_path = self._get_file_path(month)
        # Ensure directory exists before saving
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create dictionary with input_text as keys for better readability
        # Store actions directly without wrapper
        data = {}
        for action in actions:
            # Use input_text as the key, with all other fields as nested data
            action_dict = action.to_dict()
            input_text = action_dict.pop("input_text")  # Remove input_text from nested data
            data[input_text] = action_dict

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

    def load_monthly_actions(self, month: str) -> List[BrushUserAction]:
        """Load actions for a specific month from YAML file."""
        self._validate_month_format(month)

        file_path = self._get_file_path(month)
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return []

        # New format: dictionary with input_text as keys
        brush_actions = data
        if not isinstance(brush_actions, dict):
            raise ValueError(
                f"Expected dictionary format in {file_path}, got {type(brush_actions)}"
            )

        # Convert dictionary format to list of actions
        actions = []
        for input_text, action_data in brush_actions.items():
            # Add input_text back to the action data
            action_data["input_text"] = input_text
            actions.append(BrushUserAction.from_dict(action_data))

        return actions

    def append_action(self, month: str, action: BrushUserAction) -> None:
        """Append a new action to the monthly actions file."""
        # Ensure directory exists before saving
        self._ensure_directory_exists(month)

        # Load existing actions
        existing_actions = self.load_monthly_actions(month)

        # Check if an action with the same input_text already exists
        existing_action = None
        for existing in existing_actions:
            if existing.input_text == action.input_text:
                existing_action = existing
                break

        if existing_action:
            # Update existing action (replace with new one)
            existing_actions.remove(existing_action)
            existing_actions.append(action)
        else:
            # Add new action
            existing_actions.append(action)

        # Save updated actions
        self.save_monthly_actions(month, existing_actions)

    def _get_file_path(self, month: str) -> Path:
        """Get file path for monthly actions."""
        self._validate_month_format(month)

        # Handle both test and production directory structures
        if (self.base_path / "learning" / "brush_user_actions").exists():
            # Production structure: data/learning/brush_user_actions/YYYY-MM.yaml
            return self.base_path / "learning" / "brush_user_actions" / f"{month}.yaml"
        else:
            # Test structure: learning/brush_user_actions/YYYY-MM.yaml
            return self.base_path / "brush_user_actions" / f"{month}.yaml"

    def _validate_month_format(self, month: str) -> None:
        """Validate month format (YYYY-MM)."""
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError(f"Invalid month format: {month}. Expected YYYY-MM format.")

    def _ensure_directory_exists(self, month: str) -> None:
        """Ensure the directory for monthly actions exists."""
        file_path = self._get_file_path(month)
        file_path.parent.mkdir(parents=True, exist_ok=True)

    def remove_specific_action(
        self, month: str, action_to_remove: BrushUserAction
    ) -> Optional[BrushUserAction]:
        """
        Remove a specific action from the monthly actions file.

        Args:
            month: Month in YYYY-MM format
            action_to_remove: The specific action to remove

        Returns:
            The removed action if successful, None if no actions found
        """
        try:
            # Load existing actions
            actions = self.load_monthly_actions(month)
            if not actions:
                return None

            # Find and remove the specific action
            for action in actions:
                if (
                    action.input_text == action_to_remove.input_text
                    and action.timestamp == action_to_remove.timestamp
                    and action.action == action_to_remove.action
                ):
                    actions.remove(action)

                    # Save updated actions
                    self.save_monthly_actions(month, actions)
                    return action

            # Action not found
            return None

        except Exception as e:
            # Log the error but don't fail - this is a user-facing operation
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error removing specific action for {month}: {e}")
            return None


class BrushUserActionsManager:
    """High-level manager for brush user actions operations."""

    def __init__(
        self, base_path: Optional[Path] = None, correct_matches_path: Optional[Path] = None
    ):
        """Initialize manager with storage and correct matches updater."""
        if base_path is None:
            base_path = Path("data/learning")

        self.storage = BrushUserActionsStorage(base_path)
        self.correct_matches_updater = CorrectMatchesUpdater(correct_matches_path)

    def _update_correct_matches(
        self, input_text: str, result_data: Dict[str, Any], action_type: str
    ) -> None:
        """
        Update correct_matches.yaml with validation decision.

        Args:
            input_text: The input text that was validated
            result_data: The user's choice result data
            action_type: Type of action ("validated" or "overridden")
        """
        import logging

        logger = logging.getLogger(__name__)

        # Extract the actual result data from the user choice structure
        # The brush data is nested under result_data.result for scoring system
        if "result" in result_data:
            actual_result_data = result_data["result"]
        else:
            # Fallback for legacy system or direct result data
            actual_result_data = result_data

        logger.info(
            f"Updating correct_matches.yaml for '{input_text}' with action type '{action_type}'"
        )
        logger.debug(f"Data structure: {actual_result_data}")

        # Determine the field type based on the actual result data structure
        field_type = self._determine_field_type(actual_result_data)
        logger.info(f"Determined field type: {field_type}")

        # Update correct_matches.yaml - fail fast if this fails
        self.correct_matches_updater.add_or_update_entry(
            input_text=input_text,
            result_data=actual_result_data,
            action_type=action_type,
            field_type=field_type,
        )

        logger.info(f"Successfully updated correct_matches.yaml with field type: {field_type}")

        # FAIL-FAST VALIDATION: Immediately verify the entry was actually added
        if not self.correct_matches_updater.has_entry(input_text, field_type):
            raise RuntimeError(
                f"CRITICAL: Failed to add entry '{input_text}' to correct_matches.yaml "
                f"with field type '{field_type}'. This indicates a silent failure in the "
                f"update process that must be investigated immediately."
            )

        logger.info("Entry validation successful - entry confirmed in correct_matches.yaml")

        # No try/except wrapper - let any exceptions bubble up immediately
        # This ensures failures are visible and stop execution

    def _determine_field_type(self, result_data: Dict[str, Any]) -> str:
        """
        Determine the field type for correct_matches.yaml based on result data structure.

        Args:
            result_data: The user's choice result data

        Returns:
            Field type string ("brush", "handle", "knot", "split_brush")
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"Determining field type for result_data with keys: {list(result_data.keys())}")

        # Check if this is a complete brush result (has brand and model, both non-null)
        if "brand" in result_data and "model" in result_data:
            brand = result_data.get("brand")
            model = result_data.get("model")

            logger.info(f"Brand: {brand}, Model: {model}")

            # Both brand and model must exist and be non-null for a complete brush
            if brand and model:
                logger.info("Returning 'brush' - complete brush with brand and model")
                # This is a complete brush match - store in brush section
                return "brush"
            elif (brand is None or brand) and model is None:
                logger.info("Checking for dual-component brush (brand may be null, model is null)")
                # This is a dual-component brush (brand may be null, model is intentionally null)
                # Check if it has both handle and knot components
                if "handle" in result_data and "knot" in result_data:
                    logger.info(
                        "Returning 'split_brush' - dual-component brush with handle and knot"
                    )
                    # This is a dual-component brush - should be split into handle and knot sections
                    return "split_brush"
                else:
                    logger.info("Returning 'brush' - partial brush result")
                    # This is a partial brush result - store in brush section
                    return "brush"

        # Check if this is a handle-only result
        if "handle_maker" in result_data or "handle_model" in result_data:
            logger.info("Returning 'handle' - handle-only result")
            return "handle"

        # Check if this is a knot-only result
        if "fiber" in result_data or "knot_size_mm" in result_data:
            logger.info("Returning 'knot' - knot-only result")
            return "knot"

        # Check if this is explicitly a split brush result (user chose to split)
        # This should only happen when the user explicitly overrides with a split strategy
        if (
            "handle" in result_data
            and "knot" in result_data
            and result_data.get("_matched_from") == "split"
        ):
            logger.info("Returning 'split_brush' - explicit split brush result")
            return "split_brush"

        # Default to brush for complete brush results
        logger.info("Returning 'brush' - default case")
        return "brush"

    def record_validation(
        self,
        input_text: str,
        month: str,
        system_used: str,
        system_choice: Dict[str, Any],
        user_choice: Dict[str, Any],
        all_brush_strategies: List[Dict[str, Any]],
        comment_ids: List[str],
    ) -> None:
        """Record a user validation action."""
        action = BrushUserAction(
            input_text=input_text,
            timestamp=datetime.now(),
            system_used=system_used,
            action="validated",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_brush_strategies,
            comment_ids=comment_ids,
        )

        # Update correct_matches.yaml first - fail fast if this fails
        self._update_correct_matches(input_text, user_choice, "validated")

        # Only update learning file if correct_matches.yaml update succeeds
        self.storage.append_action(month, action)

    def record_override(
        self,
        input_text: str,
        month: str,
        system_used: str,
        system_choice: Dict[str, Any],
        user_choice: Dict[str, Any],
        all_brush_strategies: List[Dict[str, Any]],
        comment_ids: List[str],
    ) -> None:
        """Record a user override action."""
        action = BrushUserAction(
            input_text=input_text,
            timestamp=datetime.now(),
            system_used=system_used,
            action="overridden",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_brush_strategies,
            comment_ids=comment_ids,
        )

        # Update correct_matches.yaml first - fail fast if this fails
        self._update_correct_matches(input_text, user_choice, "overridden")

        # Only update learning file if correct_matches.yaml update succeeds
        self.storage.append_action(month, action)

    def record_validation_with_data(
        self,
        input_text: str,
        month: str,
        system_used: str,
        brush_data: Dict[str, Any],
        comment_ids: List[str],
    ) -> None:
        """Record a user validation action with brush data - backend handles all business logic."""
        # Extract the matched data and all strategies from brush_data
        matched = brush_data.get("matched", {})
        all_strategies = brush_data.get("all_strategies", [])

        # Create system choice from matched data
        system_choice = {
            "strategy": brush_data.get("strategy", ""),
            "score": matched.get("score", 0),
            "result": matched,
        }

        # For validation, user choice is the same as system choice
        user_choice = system_choice

        # Create the action
        action = BrushUserAction(
            input_text=input_text,
            timestamp=datetime.now(),
            system_used=system_used,
            action="validated",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=comment_ids,
        )

        # Update correct_matches.yaml first - fail fast if this fails
        self._update_correct_matches(input_text, user_choice, "validated")

        # Only update learning file if correct_matches.yaml update succeeds
        self.storage.append_action(month, action)

    def record_override_with_data(
        self,
        input_text: str,
        month: str,
        system_used: str,
        brush_data: Dict[str, Any],
        strategy_index: int,
        comment_ids: List[str],
    ) -> None:
        """Record a user override action with brush data - backend handles all business logic."""
        # Extract the matched data and all strategies from brush_data
        matched = brush_data.get("matched", {})
        all_strategies = brush_data.get("all_strategies", [])

        # Create system choice from matched data
        system_choice = {
            "strategy": brush_data.get("strategy", ""),
            "score": matched.get("score", 0),
            "result": matched,
        }

        # Create user choice from selected strategy
        if strategy_index >= 0 and strategy_index < len(all_strategies):
            selected_strategy = all_strategies[strategy_index]
            user_choice = {
                "strategy": selected_strategy.get("strategy", ""),
                "score": selected_strategy.get("score", 0),
                "result": selected_strategy.get("result", {}),
            }
        else:
            # Fallback to system choice if strategy index is invalid
            user_choice = system_choice

        # Create the action
        action = BrushUserAction(
            input_text=input_text,
            timestamp=datetime.now(),
            system_used=system_used,
            action="overridden",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=comment_ids,
        )

        # Update correct_matches.yaml first - fail fast if this fails
        self._update_correct_matches(input_text, user_choice, "overridden")

        # Only update learning file if correct_matches.yaml update succeeds
        self.storage.append_action(month, action)

    def get_monthly_actions(self, month: str) -> List[BrushUserAction]:
        """Get all actions for a specific month."""
        return self.storage.load_monthly_actions(month)

    def _is_valid_month_format(self, month: str) -> bool:
        """Check if month string is in valid YYYY-MM format."""
        import re

        return bool(re.match(r"^\d{4}-\d{2}$", month))

    def get_all_actions(self) -> List[BrushUserAction]:
        """Get all actions across all months, sorted by timestamp."""
        all_actions = []

        # Find all monthly files in the new directory structure
        brush_user_actions_dir = self.storage.base_path / "brush_user_actions"
        if brush_user_actions_dir.exists():
            for file_path in brush_user_actions_dir.glob("*.yaml"):
                # Extract month from filename (YYYY-MM.yaml)
                month = file_path.stem
                if self._is_valid_month_format(month):
                    actions = self.storage.load_monthly_actions(month)
                    all_actions.extend(actions)

        # Sort by timestamp
        all_actions.sort(key=lambda x: x.timestamp)
        return all_actions

    def migrate_from_correct_matches(self, correct_matches_path: Path, target_month: str) -> int:
        """Migrate brush data from existing correct_matches.yaml."""
        if not correct_matches_path.exists():
            return 0

        with open(correct_matches_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "brush" not in data:
            return 0

        migrated_actions = []
        brush_data = data["brush"]

        for key, value in brush_data.items():
            if isinstance(value, dict) and "brand" in value and "model" in value:
                # Handle flat structure: {"input_text": {"brand": "...", "model": "..."}}
                input_text = key
                brand = value["brand"]
                model = value["model"]

                action = BrushUserAction(
                    input_text=input_text,
                    timestamp=datetime.now(),
                    system_used="migrated",  # Special marker for migrated data
                    action="validated",  # Assume migrated data was validated
                    system_choice={
                        "strategy": "migrated",
                        "score": None,
                        "result": {"brand": brand, "model": model},
                    },
                    user_choice={
                        "strategy": "migrated",
                        "result": {"brand": brand, "model": model},
                    },
                    comment_ids=[],  # Migrated data doesn't have comment IDs
                    all_brush_strategies=[],  # No strategy data for migrated entries
                )
                migrated_actions.append(action)
            else:
                # Handle nested structure: {"brand": {"model": ["input_text1", "input_text2"]}}
                brand = key
                for model, input_texts in value.items():
                    if isinstance(input_texts, list):
                        # Handle list of input texts
                        for input_text in input_texts:
                            action = BrushUserAction(
                                input_text=input_text,
                                timestamp=datetime.now(),
                                system_used="migrated",  # Special marker for migrated data
                                action="validated",  # Assume migrated data was validated
                                system_choice={
                                    "strategy": "migrated",
                                    "score": None,
                                    "result": {"brand": brand, "model": model},
                                },
                                user_choice={
                                    "strategy": "migrated",
                                    "result": {"brand": brand, "model": model},
                                },
                                comment_ids=[],  # Migrated data doesn't have comment IDs
                                all_brush_strategies=[],  # No strategy data for migrated entries
                            )
                            migrated_actions.append(action)
                    else:
                        # Handle single input text (string)
                        input_text = input_texts
                        action = BrushUserAction(
                            input_text=input_text,
                            timestamp=datetime.now(),
                            system_used="migrated",  # Special marker for migrated data
                            action="validated",  # Assume migrated data was validated
                            system_choice={
                                "strategy": "migrated",
                                "score": None,
                                "result": {"brand": brand, "model": model},
                            },
                            user_choice={
                                "strategy": "migrated",
                                "result": {"brand": brand, "model": model},
                            },
                            comment_ids=[],  # Migrated data doesn't have comment IDs
                            all_brush_strategies=[],  # No strategy data for migrated entries
                        )
                        migrated_actions.append(action)

        # Save migrated actions
        for action in migrated_actions:
            self.storage.append_action(target_month, action)

        return len(migrated_actions)

    def get_statistics(self, month: str) -> Dict[str, Any]:
        """Get validation statistics for a specific month."""
        actions = self.get_monthly_actions(month)

        if not actions:
            return {
                "total_actions": 0,
                "validated_count": 0,
                "overridden_count": 0,
                "validation_rate": 0.0,
                "scoring_system_count": 0,
                "legacy_system_count": 0,
            }

        total_actions = len(actions)
        validated_count = sum(1 for action in actions if action.action == "validated")
        overridden_count = sum(1 for action in actions if action.action == "overridden")
        validation_rate = validated_count / total_actions if total_actions > 0 else 0.0

        scoring_system_count = sum(1 for action in actions if action.system_used == "scoring")
        legacy_system_count = sum(1 for action in actions if action.system_used == "legacy")

        return {
            "total_actions": total_actions,
            "validated_count": validated_count,
            "overridden_count": overridden_count,
            "validation_rate": validation_rate,
            "scoring_system_count": scoring_system_count,
            "legacy_system_count": legacy_system_count,
        }
