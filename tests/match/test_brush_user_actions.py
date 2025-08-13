"""Test brush user actions data model."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from sotd.match.brush_user_actions import (
    BrushUserAction,
    BrushUserActionsManager,
    BrushUserActionsStorage,
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
            comment_ids=["comment1", "comment2"],
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
            comment_ids=["comment3"],
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
                comment_ids=["comment4"],
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
                comment_ids=["comment5"],
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
            comment_ids=["comment7"],
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
        self.test_dir = Path(tempfile.mkdtemp())
        self.learning_dir = self.test_dir / "learning"
        self.learning_dir.mkdir()
        # Create brush_user_actions subdirectory
        self.brush_user_actions_dir = self.learning_dir / "brush_user_actions"
        self.brush_user_actions_dir.mkdir()

        self.storage = BrushUserActionsStorage(self.learning_dir)

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
                comment_ids=["comment8"],
            ),
            BrushUserAction(
                input_text="Test Brush 2",
                timestamp=datetime(2025, 8, 6, 15, 30, 0),
                system_used="legacy",
                action="overridden",
                system_choice={"strategy": "test", "score": None, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment9"],
            ),
        ]

        # Save actions for August 2025
        self.storage.save_monthly_actions("2025-08", actions)

        # Verify file was created
        file_path = self.brush_user_actions_dir / "2025-08.yaml"
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
            comment_ids=["comment10"],
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
            comment_ids=["comment11"],
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
        expected = self.brush_user_actions_dir / "2025-08.yaml"
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
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.learning_dir = self.test_dir / "learning"
        self.learning_dir.mkdir()
        # Create brush_user_actions subdirectory
        self.brush_user_actions_dir = self.learning_dir / "brush_user_actions"
        self.brush_user_actions_dir.mkdir()

        # Create a temporary correct_matches.yaml for testing
        self.correct_matches_path = self.test_dir / "correct_matches.yaml"

        self.manager = BrushUserActionsManager(
            base_path=self.learning_dir, correct_matches_path=self.correct_matches_path
        )

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
            comment_ids=["comment14"],
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
            comment_ids=["comment15"],
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
            comment_ids=["comment12"],
        )

        action2 = BrushUserAction(
            input_text="Test Brush 2",
            timestamp=datetime(2025, 8, 1, 12, 0, 0),
            system_used="legacy",
            action="validated",
            system_choice={"strategy": "test", "score": None, "result": {}},
            user_choice={"strategy": "test", "result": {}},
            all_brush_strategies=[],
            comment_ids=["comment13"],
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
        # Create a temporary correct_matches.yaml file
        correct_matches_file = Path(self.test_dir) / "correct_matches.yaml"
        correct_matches_data = {"brush": {"Test Brand": {"Test Model": ["test brush input"]}}}

        with open(correct_matches_file, "w") as f:
            yaml.dump(correct_matches_data, f)

        # Test migration
        migrated_count = self.manager.migrate_from_correct_matches(correct_matches_file, "2025-08")
        assert migrated_count == 1

        # Verify action was created
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 1
        assert actions[0].input_text == "test brush input"
        assert actions[0].system_used == "migrated"

    def test_dual_update_validation(self):
        """Test that validation actions update both learning files and correct_matches.yaml."""
        # Mock the correct matches updater
        with patch.object(self.manager, "_update_correct_matches") as mock_updater:
            system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
            user_choice = {"strategy": "dual_component", "result": {}}
            all_strategies = [
                {"strategy": "complete_brush", "score": 45, "result": {}},
                {"strategy": "dual_component", "score": 85, "result": {}},
            ]

            self.manager.record_validation(
                input_text="Test Brush Dual Update",
                month="2025-08",
                system_used="scoring",
                system_choice=system_choice,
                user_choice=user_choice,
                all_brush_strategies=all_strategies,
                comment_ids=["comment1", "comment2"],
            )

            # Verify learning file was updated
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 1
            assert actions[0].input_text == "Test Brush Dual Update"

            # Verify correct_matches.yaml was updated
            mock_updater.assert_called_once_with("Test Brush Dual Update", user_choice, "validated")

    def test_dual_update_override(self):
        """Test that override actions update both learning files and correct_matches.yaml."""
        # Mock the correct matches updater
        with patch.object(self.manager, "_update_correct_matches") as mock_updater:
            system_choice = {"strategy": "complete_brush", "score": 60, "result": {}}
            user_choice = {"strategy": "dual_component", "result": {}}
            all_strategies = []

            self.manager.record_override(
                input_text="Test Brush Override Dual Update",
                month="2025-08",
                system_used="scoring",
                system_choice=system_choice,
                user_choice=user_choice,
                all_brush_strategies=all_strategies,
                comment_ids=["comment3"],
            )

            # Verify learning file was updated
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 1
            expected_text = "Test Brush Override Dual Update"
            assert actions[0].input_text == expected_text

            # Verify correct_matches.yaml was updated
            mock_updater.assert_called_once_with(
                "Test Brush Override Dual Update", user_choice, "overridden"
            )

    def test_dual_update_error_handling(self):
        """Test that validation workflow fails fast if correct_matches.yaml update fails."""
        # Mock the correct matches updater to fail
        with patch.object(
            self.manager, "_update_correct_matches", side_effect=Exception("Update failed")
        ):
            system_choice = {"strategy": "test", "score": 50, "result": {}}
            user_choice = {"strategy": "test", "result": {}}
            all_strategies = []

            # Should raise exception - fail fast approach
            with pytest.raises(Exception, match="Update failed"):
                self.manager.record_validation(
                    input_text="Test Brush Error Handling",
                    month="2025-08",
                    system_used="scoring",
                    system_choice=system_choice,
                    user_choice=user_choice,
                    all_brush_strategies=all_strategies,
                    comment_ids=["comment4"],
                )

            # Verify learning file was NOT updated due to failure
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 0

    def test_normalized_text_usage(self):
        """Test that normalized text is used for correct_matches.yaml keys."""
        # Mock the correct matches updater
        with patch.object(self.manager, "_update_correct_matches") as mock_updater:
            system_choice = {"strategy": "test", "score": 50, "result": {}}
            user_choice = {"strategy": "test", "result": {}}
            all_strategies = []

            # Test with mixed case input
            self.manager.record_validation(
                input_text="Test Brush Mixed Case",
                month="2025-08",
                system_used="scoring",
                system_choice=system_choice,
                user_choice=user_choice,
                all_brush_strategies=all_strategies,
                comment_ids=["comment5"],
            )

            # Verify correct_matches.yaml was updated with normalized text
            mock_updater.assert_called_once_with("Test Brush Mixed Case", user_choice, "validated")

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
                comment_ids=[f"comment{i+16}"],
            )

        for i in range(2):
            self.manager.record_override(
                input_text=f"Overridden Brush {i}",
                month="2025-08",
                system_used="scoring",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
                comment_ids=[f"comment{i+19}"],
            )

        stats = self.manager.get_statistics("2025-08")
        assert stats["total_actions"] == 5
        assert stats["validated_count"] == 3
        assert stats["overridden_count"] == 2
        assert stats["validation_rate"] == 0.6  # 3/5
        assert stats["scoring_system_count"] == 5
        assert stats["legacy_system_count"] == 0

    def test_real_dual_update_validation(self):
        """Test that validation actions actually write to both learning files and correct_matches.yaml."""
        # Create a temporary correct_matches.yaml for testing
        import tempfile
        import shutil
        from pathlib import Path

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_learning_dir = Path(temp_dir) / "learning"
        temp_learning_dir.mkdir()
        temp_correct_matches = Path(temp_dir) / "correct_matches.yaml"

        try:
            # Initialize manager with temporary paths
            temp_manager = BrushUserActionsManager(
                base_path=temp_learning_dir, correct_matches_path=temp_correct_matches
            )

            # Test data that should result in a brush field type
            system_choice = {"strategy": "known_brush", "score": 80, "result": {}}
            user_choice = {
                "strategy": "known_brush",
                "score": 80,
                "result": {
                    "brand": "Test Brand",
                    "model": "Test Model",
                    "source_text": "Test Brush Real Dual Update",
                },
            }
            all_strategies = []

            # Record validation action
            temp_manager.record_validation(
                input_text="Test Brush Real Dual Update",
                month="2025-08",
                system_used="scoring",
                system_choice=system_choice,
                user_choice=user_choice,
                all_brush_strategies=all_strategies,
                comment_ids=["comment1"],
            )

            # Verify learning file was created and updated
            expected_learning_file = temp_learning_dir / "brush_user_actions" / "2025-08.yaml"
            assert expected_learning_file.exists(), "Learning file should exist"

            # Load and verify learning file contents
            with open(expected_learning_file, "r") as f:
                learning_data = yaml.safe_load(f)

            # New format: actions stored directly without wrapper
            assert isinstance(learning_data, dict), "Learning file should be a dictionary"
            assert len(learning_data) == 1, "Learning file should have one action"
            # Check that the input_text is a key in the dictionary
            assert (
                "Test Brush Real Dual Update" in learning_data
            ), "Learning file should have input_text as key"

            # Verify correct_matches.yaml was created and updated
            assert temp_correct_matches.exists(), "correct_matches.yaml should exist"

            # Load and verify correct_matches.yaml contents
            with open(temp_correct_matches, "r") as f:
                correct_matches_data = yaml.safe_load(f)

            assert "brush" in correct_matches_data, "correct_matches.yaml should have brush section"
            assert (
                "Test Brand" in correct_matches_data["brush"]
            ), "correct_matches.yaml should have Test Brand"
            assert (
                "Test Model" in correct_matches_data["brush"]["Test Brand"]
            ), "correct_matches.yaml should have Test Model"

            # Check that the normalized pattern was added
            patterns = correct_matches_data["brush"]["Test Brand"]["Test Model"]
            assert (
                "test brush real dual update" in patterns
            ), "Normalized pattern should be in correct_matches.yaml"

        finally:
            # Clean up
            shutil.rmtree(temp_dir)

    def test_undo_last_action_success(self):
        """Test successfully undoing the last action."""
        # Record some actions first
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        # Record first action
        self.manager.record_validation(
            input_text="Test Brush 1",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment1"],
        )

        # Add a small delay to ensure different timestamps
        import time

        time.sleep(0.1)

        # Record second action
        self.manager.record_validation(
            input_text="Test Brush 2",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment2"],
        )

        # Verify we have 2 actions
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 2

        # Debug: Print action details
        print("Actions before undo:")
        for i, action in enumerate(actions):
            print(f"  {i}: {action.input_text} at {action.timestamp}")

        # Mock the CLI for correct_matches removal
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method
            mock_updater.remove_entry.return_value = True

            # Undo last action
            undone_action = self.manager.undo_last_action("2025-08")

            # Debug: Print what was undone
            if undone_action:
                print(f"Undone action: {undone_action.input_text} at {undone_action.timestamp}")
            else:
                print("No action was undone")

            # Verify undone action
            assert undone_action is not None
            assert undone_action.input_text == "Test Brush 2"
            assert undone_action.action == "validated"

            # Verify action was removed from storage
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 1
            assert actions[0].input_text == "Test Brush 1"

            # Verify correct_matches_updater was called to remove entry
            mock_updater.remove_entry.assert_called_once_with("Test Brush 2", "brush")

    def test_undo_last_action_no_actions(self):
        """Test undoing last action when no actions exist."""
        # Try to undo from month with no actions
        undone_action = self.manager.undo_last_action("2025-08")

        assert undone_action is None

    def test_undo_last_action_single_action(self):
        """Test undoing last action when only one action exists."""
        # Record single action
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        self.manager.record_validation(
            input_text="Test Brush Single",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment1"],
        )

        # Mock the correct_matches_updater for removal
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method
            mock_updater.remove_entry.return_value = True

            # Undo last action
            undone_action = self.manager.undo_last_action("2025-08")

            # Verify undone action
            assert undone_action is not None
            assert undone_action.input_text == "Test Brush Single"

            # Verify action was removed from storage
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 0

    def test_undo_last_action_cli_error_handling(self):
        """Test handling of CLI errors during undo operation."""
        # Record test action
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        self.manager.record_validation(
            input_text="Test Brush CLI Error",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment1"],
        )

        # Mock the correct_matches_updater to raise an error
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method to raise an error
            mock_updater.remove_entry.side_effect = Exception("Updater Error")

            # Undo should still work even if updater fails
            undone_action = self.manager.undo_last_action("2025-08")

            # Verify undone action
            assert undone_action is not None
            assert undone_action.input_text == "Test Brush CLI Error"

            # Verify action was removed from storage
            actions = self.manager.get_monthly_actions("2025-08")
            assert len(actions) == 0

    def test_undo_last_action_different_months(self):
        """Test that undo operations are isolated to specific months."""
        # Record actions for different months
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        # Record action for 2025-07
        self.manager.record_validation(
            input_text="Test Brush July",
            month="2025-07",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment1"],
        )

        # Record action for 2025-08
        self.manager.record_validation(
            input_text="Test Brush August",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment2"],
        )

        # Mock the correct_matches_updater for removal
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method
            mock_updater.remove_entry.return_value = True

            # Undo from 2025-07
            undone_action_07 = self.manager.undo_last_action("2025-07")

            # Verify action was undone from 2025-07
            assert undone_action_07 is not None
            assert undone_action_07.input_text == "Test Brush July"

            # Verify 2025-08 actions are unchanged
            actions_08 = self.manager.get_monthly_actions("2025-08")
            assert len(actions_08) == 1
            assert actions_08[0].input_text == "Test Brush August"

    def test_undo_last_action_preserves_order(self):
        """Test that undo operations preserve the order of remaining actions."""
        # Record multiple actions
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        # Record actions in order
        for i in range(3):
            self.manager.record_validation(
                input_text=f"Test Brush {i+1}",
                month="2025-08",
                system_used="scoring",
                system_choice=system_choice,
                user_choice=user_choice,
                all_brush_strategies=all_strategies,
                comment_ids=[f"comment{i+1}"],
            )

        # Verify we have 3 actions
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 3

        # Mock the correct_matches_updater for removal
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method
            mock_updater.remove_entry.return_value = True

            # Undo last action
            undone_action = self.manager.undo_last_action("2025-08")

            # Verify undone action
            assert undone_action is not None
            assert undone_action.input_text == "Test Brush 3"

            # Verify remaining actions preserve order
            remaining_actions = self.manager.get_monthly_actions("2025-08")
            assert len(remaining_actions) == 2
            assert remaining_actions[0].input_text == "Test Brush 1"
            assert remaining_actions[1].input_text == "Test Brush 2"

    def test_undo_last_action_with_override_actions(self):
        """Test undoing override actions."""
        # Record mix of validation and override actions
        system_choice = {"strategy": "dual_component", "score": 85, "result": {}}
        user_choice = {"strategy": "dual_component", "result": {}}
        all_strategies = [
            {"strategy": "complete_brush", "score": 45, "result": {}},
            {"strategy": "dual_component", "score": 85, "result": {}},
        ]

        # Record validation action
        self.manager.record_validation(
            input_text="Test Brush Validated",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment1"],
        )

        # Record override action
        self.manager.record_override(
            input_text="Test Brush Overridden",
            month="2025-08",
            system_used="scoring",
            system_choice=system_choice,
            user_choice=user_choice,
            all_brush_strategies=all_strategies,
            comment_ids=["comment2"],
        )

        # Verify we have 2 actions
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 2

        # Mock the correct_matches_updater for removal
        with patch.object(self.manager, "correct_matches_updater") as mock_updater:
            # Mock the remove_entry method
            mock_updater.remove_entry.return_value = True

            # Undo last action (should be the override)
            undone_action = self.manager.undo_last_action("2025-08")

            # Verify undone action
            assert undone_action is not None
            assert undone_action.input_text == "Test Brush Overridden"
            assert undone_action.action == "overridden"

            # Verify remaining action is the validation
            remaining_actions = self.manager.get_monthly_actions("2025-08")
            assert len(remaining_actions) == 1
            assert remaining_actions[0].input_text == "Test Brush Validated"
            assert remaining_actions[0].action == "validated"


class TestBrushUserActionsStorageUndo:
    """Test undo functionality in BrushUserActionsStorage."""

    def setup_method(self):
        """Set up test directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.learning_dir = self.test_dir / "learning"
        self.learning_dir.mkdir()
        # Create brush_user_actions subdirectory
        self.brush_user_actions_dir = self.learning_dir / "brush_user_actions"
        self.brush_user_actions_dir.mkdir()

        self.storage = BrushUserActionsStorage(self.learning_dir)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_remove_last_action_success(self):
        """Test successfully removing the last action."""
        # Create test actions
        actions = [
            BrushUserAction(
                input_text="Test Brush 1",
                timestamp=datetime(2025, 8, 6, 14, 30, 0),
                system_used="scoring",
                action="validated",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment1"],
            ),
            BrushUserAction(
                input_text="Test Brush 2",
                timestamp=datetime(2025, 8, 6, 15, 30, 0),
                system_used="legacy",
                action="overridden",
                system_choice={"strategy": "test", "score": None, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment2"],
            ),
        ]

        # Save actions
        self.storage.save_monthly_actions("2025-08", actions)

        # Remove last action
        removed_action = self.storage.remove_last_action("2025-08")

        # Verify removed action
        assert removed_action is not None
        assert removed_action.input_text == "Test Brush 2"
        assert removed_action.action == "overridden"

        # Verify file was updated
        loaded_actions = self.storage.load_monthly_actions("2025-08")
        assert len(loaded_actions) == 1
        assert loaded_actions[0].input_text == "Test Brush 1"

    def test_remove_last_action_empty_file(self):
        """Test removing last action from empty file."""
        # Try to remove from empty month
        removed_action = self.storage.remove_last_action("2025-08")

        assert removed_action is None

    def test_remove_last_action_single_action(self):
        """Test removing last action when only one action exists."""
        # Create single action
        actions = [
            BrushUserAction(
                input_text="Test Brush 1",
                timestamp=datetime(2025, 8, 6, 14, 30, 0),
                system_used="scoring",
                action="validated",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment1"],
            )
        ]

        # Save action
        self.storage.save_monthly_actions("2025-08", actions)

        # Remove last action
        removed_action = self.storage.remove_last_action("2025-08")

        # Verify removed action
        assert removed_action is not None
        assert removed_action.input_text == "Test Brush 1"

        # Verify file is now empty
        loaded_actions = self.storage.load_monthly_actions("2025-08")
        assert len(loaded_actions) == 0

    def test_remove_last_action_preserves_order(self):
        """Test that removing last action preserves order of remaining actions."""
        # Create test actions
        actions = [
            BrushUserAction(
                input_text="Test Brush 1",
                timestamp=datetime(2025, 8, 6, 14, 30, 0),
                system_used="scoring",
                action="validated",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment1"],
            ),
            BrushUserAction(
                input_text="Test Brush 2",
                timestamp=datetime(2025, 8, 6, 15, 30, 0),
                system_used="legacy",
                action="overridden",
                system_choice={"strategy": "test", "score": None, "result": {}},
                user_choice={"strategy": "other", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment2"],
            ),
            BrushUserAction(
                input_text="Test Brush 3",
                timestamp=datetime(2025, 8, 6, 16, 30, 0),
                system_used="scoring",
                action="validated",
                system_choice={"strategy": "test", "score": 75, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
                comment_ids=["comment3"],
            ),
        ]

        # Save actions
        self.storage.save_monthly_actions("2025-08", actions)

        # Remove last action
        removed_action = self.storage.remove_last_action("2025-08")

        # Verify removed action
        assert removed_action is not None
        assert removed_action.input_text == "Test Brush 3"

        # Verify remaining actions preserve order
        loaded_actions = self.storage.load_monthly_actions("2025-08")
        assert len(loaded_actions) == 2
        assert loaded_actions[0].input_text == "Test Brush 1"
        assert loaded_actions[1].input_text == "Test Brush 2"

    def test_remove_last_action_nonexistent_month(self):
        """Test removing last action from nonexistent month."""
        # Try to remove from nonexistent month
        removed_action = self.storage.remove_last_action("2025-99")

        assert removed_action is None

    def test_remove_last_action_corrupted_file(self):
        """Test handling of corrupted YAML file during undo operation."""
        # Create a corrupted YAML file
        corrupted_file = self.brush_user_actions_dir / "2025-08.yaml"
        corrupted_file.parent.mkdir(parents=True, exist_ok=True)

        with open(corrupted_file, "w") as f:
            f.write("invalid: yaml: content: [\n  - invalid\n")

        # Try to remove last action from corrupted file
        # Should handle gracefully and return None
        removed_action = self.storage.remove_last_action("2025-08")

        assert removed_action is None
