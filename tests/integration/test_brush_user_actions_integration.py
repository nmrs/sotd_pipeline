"""Integration tests for brush user actions with existing workflows."""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import yaml

from sotd.match.brush_user_actions import BrushUserActionsManager
from sotd.utils.file_io import load_yaml_data


class TestBrushUserActionsIntegration:
    """Integration tests for brush user actions."""

    def setup_method(self):
        """Set up test directories."""
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.test_dir) / "data"
        self.test_learning_dir = self.test_data_dir / "learning"
        self.manager = BrushUserActionsManager(base_path=self.test_learning_dir)

    def teardown_method(self):
        """Clean up test directories."""
        shutil.rmtree(self.test_dir)

    def test_integration_with_file_io(self):
        """Test integration with existing FileIO utilities."""
        # Record some actions
        self.manager.record_validation(
            input_text="Test Brush Integration",
            month="2025-08",
            system_used="scoring",
            system_choice={"strategy": "dual_component", "score": 85, "result": {}},
            user_choice={"strategy": "dual_component", "result": {}},
            all_brush_strategies=[],
        )

        # Verify file was created in expected location
        expected_file = self.test_learning_dir / "brush_user_actions" / "2025-08.yaml"
        assert expected_file.exists()

        # Use file_io functions to verify file contents
        data = load_yaml_data(expected_file)

        assert "brush_user_actions" in data
        assert len(data["brush_user_actions"]) == 1
        assert data["brush_user_actions"][0]["input_text"] == "Test Brush Integration"
        assert data["brush_user_actions"][0]["system_used"] == "scoring"

    def test_correct_matches_migration_integration(self):
        """Test integration with existing correct_matches.yaml workflow."""
        # Create a mock correct_matches.yaml file
        correct_matches_data = {
            "brush": {
                "Chisel & Hound / Omega 10098": {
                    "brand": "Chisel & Hound",
                    "model": "The Duke",
                    "handle": {"brand": "Chisel & Hound", "model": "The Duke"},
                    "knot": {"brand": "Omega", "model": "10098"},
                },
                "Summer Break Soaps Maize": {"brand": "Summer Break Soaps", "model": "Maize"},
            },
            "razor": {"Some Razor": {"brand": "Test", "model": "Razor"}},
            "soap": {"Some Soap": {"brand": "Test", "model": "Soap"}},
        }

        # Save to data directory
        correct_matches_path = self.test_data_dir / "correct_matches.yaml"
        with open(correct_matches_path, "w") as f:
            yaml.dump(correct_matches_data, f)

        # Test migration
        migrated_count = self.manager.migrate_from_correct_matches(correct_matches_path, "2025-08")

        # Should only migrate brush entries, not razor/soap
        assert migrated_count == 2

        # Verify migrated actions
        actions = self.manager.get_monthly_actions("2025-08")
        assert len(actions) == 2

        # Check that both brush entries were migrated
        input_texts = [action.input_text for action in actions]
        assert "Chisel & Hound / Omega 10098" in input_texts
        assert "Summer Break Soaps Maize" in input_texts

        # All actions should be marked as migrated and validated
        for action in actions:
            assert action.system_used == "migrated"
            assert action.action == "validated"

    def test_monthly_file_structure_compatibility(self):
        """Test compatibility with expected monthly file structure."""
        # Record actions in multiple months
        months = ["2025-06", "2025-07", "2025-08"]
        for i, month in enumerate(months):
            self.manager.record_validation(
                input_text=f"Test Brush {i}",
                month=month,
                system_used="scoring",
                system_choice={"strategy": "test", "score": 50, "result": {}},
                user_choice={"strategy": "test", "result": {}},
                all_brush_strategies=[],
            )

        # Verify files follow expected naming pattern
        for month in months:
            expected_file = self.test_learning_dir / "brush_user_actions" / f"{month}.yaml"
            assert expected_file.exists()

        # Test cross-month retrieval
        all_actions = self.manager.get_all_actions()
        assert len(all_actions) == 3

        # Verify timestamps are in order
        timestamps = [action.timestamp for action in all_actions]
        assert timestamps == sorted(timestamps)

    def test_statistics_integration(self):
        """Test statistics integration with real data patterns."""
        # Create mix of scoring and legacy system data
        # Scoring system validations
        for i in range(3):
            self.manager.record_validation(
                input_text=f"Scoring Brush {i}",
                month="2025-08",
                system_used="scoring",
                system_choice={"strategy": "dual_component", "score": 85, "result": {}},
                user_choice={"strategy": "dual_component", "result": {}},
                all_brush_strategies=[],
            )

        # Scoring system overrides
        for i in range(2):
            self.manager.record_override(
                input_text=f"Override Brush {i}",
                month="2025-08",
                system_used="scoring",
                system_choice={"strategy": "complete_brush", "score": 60, "result": {}},
                user_choice={"strategy": "dual_component", "result": {}},
                all_brush_strategies=[],
            )

        # Legacy system validation (from migration)
        self.manager.record_validation(
            input_text="Legacy Brush",
            month="2025-08",
            system_used="legacy",
            system_choice={"strategy": "legacy", "score": None, "result": {}},
            user_choice={"strategy": "legacy", "result": {}},
            all_brush_strategies=[],
        )

        # Test comprehensive statistics
        stats = self.manager.get_statistics("2025-08")

        assert stats["total_actions"] == 6
        assert stats["validated_count"] == 4  # 3 scoring + 1 legacy
        assert stats["overridden_count"] == 2  # 2 scoring overrides
        assert stats["validation_rate"] == 4 / 6  # 66.7%
        assert stats["scoring_system_count"] == 5  # 3 validated + 2 overridden
        assert stats["legacy_system_count"] == 1

    def test_yaml_format_compatibility(self):
        """Test YAML format matches expected structure for downstream tools."""
        self.manager.record_validation(
            input_text="Format Test Brush",
            month="2025-08",
            system_used="scoring",
            system_choice={
                "strategy": "dual_component",
                "score": 85,
                "result": {
                    "brand": "Test",
                    "model": "Brush",
                    "handle": {"brand": "Test", "model": "Handle"},
                    "knot": {"brand": "Test", "model": "Knot"},
                },
            },
            user_choice={
                "strategy": "dual_component",
                "result": {
                    "brand": "Test",
                    "model": "Brush",
                    "handle": {"brand": "Test", "model": "Handle"},
                    "knot": {"brand": "Test", "model": "Knot"},
                },
            },
            all_brush_strategies=[
                {"strategy": "complete_brush", "score": 45, "result": {}},
                {"strategy": "dual_component", "score": 85, "result": {}},
            ],
        )

        # Load raw YAML to verify format
        file_path = self.test_learning_dir / "brush_user_actions_2025-08.yaml"
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        # Verify top-level structure
        assert "brush_user_actions" in data
        assert isinstance(data["brush_user_actions"], list)

        # Verify action structure
        action = data["brush_user_actions"][0]
        required_fields = [
            "input_text",
            "timestamp",
            "system_used",
            "action",
            "system_choice",
            "user_choice",
            "all_brush_strategies",
        ]
        for field in required_fields:
            assert field in action

        # Verify nested structure
        assert "strategy" in action["system_choice"]
        assert "score" in action["system_choice"]
        assert "result" in action["system_choice"]
        assert "strategy" in action["user_choice"]
        assert "result" in action["user_choice"]

        # Verify timestamp format (ISO 8601)
        timestamp_str = action["timestamp"]
        assert timestamp_str.endswith("Z")
        # Should be parseable back to datetime
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
