"""Test brush user actions data model."""

import pytest
from datetime import datetime
from pathlib import Path
import yaml
import tempfile
import shutil

from sotd.match.brush_user_actions import (
    BrushUserAction,
    BrushUserActionsStorage,
    BrushUserActionsManager,
    ValidationError,
)


class TestBrushUserAction:
    """Test BrushUserAction data model."""

    def test_create_valid_action(self):
        """Test creating a valid brush user action."""
        action = BrushUserAction(
            input_text="Chisel & Hound 'The Duke' / Omega 10098 Boar",
            timestamp=datetime.now(),
            system_used="scoring",
            action="validated",
            system_choice={
                "strategy": "dual_component",
                "score": 85,
                "result": {"brand": "Chisel & Hound", "model": "The Duke"},
            },
            user_choice={
                "strategy": "dual_component",
                "result": {"brand": "Chisel & Hound", "model": "The Duke"},
            },
            all_brush_strategies=[
                {"strategy": "complete_brush", "score": 45, "result": {}},
                {"strategy": "dual_component", "score": 85, "result": {"brand": "Chisel & Hound"}},
                {"strategy": "single_component", "score": 30, "result": {}},
            ],
        )

        assert action.input_text == "Chisel & Hound 'The Duke' / Omega 10098 Boar"
        assert action.system_used == "scoring"
        assert action.action == "validated"
        assert action.system_choice["strategy"] == "dual_component"
        assert action.system_choice["score"] == 85
        assert action.user_choice["strategy"] == "dual_component"
        assert len(action.all_brush_strategies) == 3

    def test_create_action_with_legacy_system(self):
        """Test creating action with legacy system identification."""
        action = BrushUserAction(
            input_text="Summer Break Soaps Maize 26mm Timberwolf",
            timestamp=datetime.now(),
            system_used="legacy",
            action="overridden",
            system_choice={
                "strategy": "dual_component",
                "score": None,  # Legacy system doesn't have scores
                "result": {"brand": "Summer Break", "model": "Maize"},
            },
            user_choice={
                "strategy": "complete_brush",
                "result": {"brand": "Summer Break Soaps", "model": "Maize"},
            },
            all_brush_strategies=[],  # Legacy system doesn't track all strategies
        )

        assert action.system_used == "legacy"
        assert action.action == "overridden"
        assert action.system_choice["score"] is None
        assert action.all_brush_strategies == []

    def test_invalid_system_used(self):
        """Test validation of system_used field."""
        with pytest.raises(
            ValidationError, match="system_used must be either 'scoring', 'legacy', or 'migrated'"
        ):
            BrushUserAction(
                input_text="Test brush",
                timestamp=datetime.now(),
                system_used="invalid_system",
                action="validated",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
            )

    def test_invalid_action_type(self):
        """Test validation of action field."""
        with pytest.raises(
            ValidationError, match="action must be either 'validated' or 'overridden'"
        ):
            BrushUserAction(
                input_text="Test brush",
                timestamp=datetime.now(),
                system_used="scoring",
                action="invalid_action",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
            )

    def test_to_dict(self):
        """Test conversion to dictionary format."""
        timestamp = datetime(2025, 8, 6, 14, 30, 0)
        action = BrushUserAction(
            input_text="Test Brush",
            timestamp=timestamp,
            system_used="scoring",
            action="validated",
            system_choice={"strategy": "test", "score": 50, "result": {}},
            user_choice={"strategy": "test", "result": {}},
            all_brush_strategies=[],
        )

        result = action.to_dict()
        assert result["input_text"] == "Test Brush"
        assert result["timestamp"] == "2025-08-06T14:30:00Z"
        assert result["system_used"] == "scoring"
        assert result["action"] == "validated"

    def test_from_dict(self):
        """Test creation from dictionary format."""
        data = {
            "input_text": "Test Brush",
            "timestamp": "2025-08-06T14:30:00Z",
            "system_used": "scoring",
            "action": "validated",
            "system_choice": {"strategy": "test", "score": 50, "result": {}},
            "user_choice": {"strategy": "test", "result": {}},
            "all_brush_strategies": [],
        }

        action = BrushUserAction.from_dict(data)
        assert action.input_text == "Test Brush"
        assert action.timestamp == datetime(2025, 8, 6, 14, 30, 0)
        assert action.system_used == "scoring"
        assert action.action == "validated"


class TestBrushUserActionsStorage:
    """Test BrushUserActionsStorage for monthly file operations."""

    def setup_method(self):
        """Set up test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.storage = BrushUserActionsStorage(base_path=Path(self.test_dir))

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_save_and_load_monthly_actions(self):
        """Test saving and loading monthly brush user actions."""
        actions = [
            BrushUserAction(
                input_text="Test Brush 1",
                timestamp=datetime(2025, 8, 6, 14, 30, 0),
                system_used="scoring",
                action="validated",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
            ),
            BrushUserAction(
                input_text="Test Brush 2",
                timestamp=datetime(2025, 8, 6, 15, 30, 0),
                system_used="legacy",
                action="overridden",
                system_choice={"strategy": "test", "score": None, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
            ),
        ]

        # Save actions for August 2025
        self.storage.save_monthly_actions("2025-08", actions)

        # Verify file was created
        file_path = Path(self.test_dir) / "brush_user_actions_2025-08.yaml"
        assert file_path.exists()

        # Load and verify
        loaded_actions = self.storage.load_monthly_actions("2025-08")
        assert len(loaded_actions) == 2
        assert loaded_actions[0].input_text == "Test Brush 1"
        assert loaded_actions[1].input_text == "Test Brush 2"
        assert loaded_actions[0].system_used == "scoring"
        assert loaded_actions[1].system_used == "legacy"

    def test_load_nonexistent_file(self):
        """Test loading actions from nonexistent file."""
        actions = self.storage.load_monthly_actions("2025-12")
        assert actions == []

    def test_append_action(self):
        """Test appending single action to monthly file."""
        # Create initial action
        action1 = BrushUserAction(
            input_text="Test Brush 1",
            timestamp=datetime(2025, 8, 6, 14, 30, 0),
            system_used="scoring",
            action="validated",
            system_choice={"strategy": "test", "score": 50, "result": {}},
            user_choice={"strategy": "test", "result": {}},
            all_brush_strategies=[],
        )

        # Save initial action
        self.storage.save_monthly_actions("2025-08", [action1])

        # Append second action
        action2 = BrushUserAction(
            input_text="Test Brush 2",
            timestamp=datetime(2025, 8, 6, 15, 30, 0),
            system_used="legacy",
            action="overridden",
            system_choice={"strategy": "test", "score": None, "result": {}},
            user_choice={"strategy": "other", "result": {}},
            all_brush_strategies=[],
        )

        self.storage.append_action("2025-08", action2)

        # Verify both actions are present
        loaded_actions = self.storage.load_monthly_actions("2025-08")
        assert len(loaded_actions) == 2
        assert loaded_actions[0].input_text == "Test Brush 1"
        assert loaded_actions[1].input_text == "Test Brush 2"

    def test_get_file_path(self):
        """Test file path generation."""
        path = self.storage._get_file_path("2025-08")
        expected = Path(self.test_dir) / "brush_user_actions_2025-08.yaml"
        assert path == expected

    def test_invalid_month_format(self):
        """Test validation of month format."""
        with pytest.raises(ValidationError, match="Invalid month format"):
            self.storage.save_monthly_actions("2025-8", [])  # Should be 2025-08

        with pytest.raises(ValidationError, match="Invalid month format"):
            self.storage.load_monthly_actions("25-08")  # Should be 2025-08


class TestBrushUserActionsManager:
    """Test BrushUserActionsManager for high-level operations."""

    def setup_method(self):
        """Set up test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = BrushUserActionsManager(base_path=Path(self.test_dir))

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_record_validation(self):
        """Test recording a validation action."""
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        self.manager.record_validation(
            input_text="Test Brush",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
        )

        # Verify action was recorded
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 1
        assert actions[0].input_text == "Test Brush"
        assert actions[0].action == "validated"
        assert actions[0].system_used == "scoring"

    def test_record_override(self):
        """Test recording an override action."""
        system_choice = {"strategy": "complete_brush", "score": 60, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = []

        self.manager.record_override(
            input_text="Test Brush",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
        )

        # Verify action was recorded
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 1
        assert actions[0].input_text == "Test Brush"
        assert actions[0].action == "overridden"

    def test_get_all_actions(self):
        """Test getting actions across multiple months."""
        # Create actions with specific timestamps to ensure ordering
        action1 = BrushUserAction(
            input_text="Test Brush 1",
            timestamp=datetime(2025, 7, 1, 12, 0, 0),
            system_used="scoring",
            action="validated",
            system_choice={"strategy": "test", "score": 50, "result": {}},
            user_choice={"strategy": "test", "result": {}},
            all_brush_strategies=[],
        )

        action2 = BrushUserAction(
            input_text="Test Brush 2",
            timestamp=datetime(2025, 8, 1, 12, 0, 0),
            system_used="legacy",
            action="validated",
            system_choice={"strategy": "test", "score": None, "result": {}},
            user_choice={"strategy": "test", "result": {}},
            all_brush_strategies=[],
        )

        # Save actions directly to ensure specific timestamps
        self.manager.storage.append_action("2025-07", action1)
        self.manager.storage.append_action("2025-08", action2)

        # Get all actions
        all_actions = self.manager.get_all_actions()
        assert len(all_actions) == 2

        # Actions should be sorted by timestamp
        assert all_actions[0].input_text == "Test Brush 1"
        assert all_actions[1].input_text == "Test Brush 2"

    def test_migrate_from_correct_matches(self):
        """Test migration from existing correct_matches.yaml."""
        # Create mock correct_matches.yaml content with brush data
        correct_matches_data = {
            "brush": {
                "Chisel & Hound / Omega 10098": {
                    "brand": "Chisel & Hound",
                    "model": "The Duke",
                    "handle": {"brand": "Chisel & Hound", "model": "The Duke"},
                    "knot": {"brand": "Omega", "model": "10098"},
                },
                "Summer Break Soaps Maize": {"brand": "Summer Break Soaps", "model": "Maize"},
            }
        }

        # Save mock file
        correct_matches_path = Path(self.test_dir) / "correct_matches.yaml"
        with open(correct_matches_path, "w") as f:
            yaml.dump(correct_matches_data, f)

        # Test migration
        migrated_count = self.manager.migrate_from_correct_matches(correct_matches_path, "2025-08")

        # Verify migration results
        assert migrated_count == 2
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 2

        # Check migrated actions
        action_texts = [action.input_text for action in actions]
        assert "Chisel & Hound / Omega 10098" in action_texts
        assert "Summer Break Soaps Maize" in action_texts

        # All migrated actions should be validated (user approved them)
        for action in actions:
            assert action.action == "validated"
            assert action.system_used == "migrated"  # Special marker for migrated data

    def test_get_statistics(self):
        """Test getting validation statistics."""
        # Record mix of validations and overrides
        for i in range(3):
            self.manager.record_validation(
                input_text=f"Validated Brush {i}",
                month="2025-08",
                system_used="scoring",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
            )

        for i in range(2):
            self.manager.record_override(
                input_text=f"Overridden Brush {i}",
                month="2025-08",
                system_used="scoring",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
            )

        stats = self.manager.get_statistics("2025-08")
        assert stats["total_actions"] == 5
        assert stats["validated_count"] == 3
        assert stats["overridden_count"] == 2
        assert stats["validation_rate"] == 0.6  # 3/5
        assert stats["scoring_system_count"] == 5
        assert stats["legacy_system_count"] == 0
