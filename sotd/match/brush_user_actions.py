"""Brush user actions data model and storage for validation tracking."""

import re
import yaml
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


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
        data = {"brush_user_actions": [action.to_dict() for action in actions]}

        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def load_monthly_actions(self, month: str) -> List[BrushUserAction]:
        """Load actions for a specific month from YAML file."""
        self._validate_month_format(month)

        file_path = self._get_file_path(month)
        if not file_path.exists():
            return []

        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "brush_user_actions" not in data:
            return []

        return [
            BrushUserAction.from_dict(action_data) for action_data in data["brush_user_actions"]
        ]

    def append_action(self, month: str, action: BrushUserAction) -> None:
        """Append a single action to monthly file."""
        existing_actions = self.load_monthly_actions(month)
        existing_actions.append(action)
        self.save_monthly_actions(month, existing_actions)

    def _get_file_path(self, month: str) -> Path:
        """Get file path for monthly actions file."""
        return self.base_path / f"brush_user_actions_{month}.yaml"

    def _validate_month_format(self, month: str) -> None:
        """Validate month format (YYYY-MM)."""
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError(f"Invalid month format: {month}. Expected YYYY-MM format.")


class BrushUserActionsManager:
    """High-level manager for brush user actions operations."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize manager with storage."""
        if base_path is None:
            base_path = Path("data/learning")

        self.storage = BrushUserActionsStorage(base_path)

    def record_validation(
        self,
        input_text: str,
        month: str,
        system_used: str,
        system_choice: Dict[str, Any],
        user_choice: Dict[str, Any],
        all_brush_strategies: List[Dict[str, Any]],
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
        )

        self.storage.append_action(month, action)

    def record_override(
        self,
        input_text: str,
        month: str,
        system_used: str,
        system_choice: Dict[str, Any],
        user_choice: Dict[str, Any],
        all_brush_strategies: List[Dict[str, Any]],
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
        )

        self.storage.append_action(month, action)

    def get_monthly_actions(self, month: str) -> List[BrushUserAction]:
        """Get all actions for a specific month."""
        return self.storage.load_monthly_actions(month)

    def get_all_actions(self) -> List[BrushUserAction]:
        """Get all actions across all months, sorted by timestamp."""
        all_actions = []

        # Find all monthly files
        for file_path in self.storage.base_path.glob("brush_user_actions_*.yaml"):
            # Extract month from filename
            filename = file_path.stem
            month_match = re.search(r"brush_user_actions_(\d{4}-\d{2})", filename)
            if month_match:
                month = month_match.group(1)
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

        for input_text, result in brush_data.items():
            # Create action for migrated data
            action = BrushUserAction(
                input_text=input_text,
                timestamp=datetime.now(),
                system_used="migrated",  # Special marker for migrated data
                action="validated",  # Assume migrated data was validated
                system_choice={"strategy": "migrated", "score": None, "result": result},
                user_choice={"strategy": "migrated", "result": result},
                all_brush_strategies=[],  # No strategy data available for migrated entries
            )
            migrated_actions.append(action)

        # Save all migrated actions
        if migrated_actions:
            existing_actions = self.storage.load_monthly_actions(target_month)
            existing_actions.extend(migrated_actions)
            self.storage.save_monthly_actions(target_month, existing_actions)

        return len(migrated_actions)

    def get_statistics(self, month: str) -> Dict[str, Union[int, float]]:
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

        validated_count = sum(1 for action in actions if action.action == "validated")
        overridden_count = sum(1 for action in actions if action.action == "overridden")
        scoring_count = sum(1 for action in actions if action.system_used == "scoring")
        legacy_count = sum(1 for action in actions if action.system_used == "legacy")

        return {
            "total_actions": len(actions),
            "validated_count": validated_count,
            "overridden_count": overridden_count,
            "validation_rate": validated_count / len(actions) if actions else 0.0,
            "scoring_system_count": scoring_count,
            "legacy_system_count": legacy_count,
        }
