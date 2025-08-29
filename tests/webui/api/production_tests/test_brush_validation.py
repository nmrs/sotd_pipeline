"""Tests for brush validation API endpoints."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add the webui directory to the Python path
webui_dir = Path(__file__).parent.parent
if str(webui_dir) not in sys.path:
    sys.path.insert(0, str(webui_dir))

from api.main import app


class TestBrushValidationAPI:
    """Test brush validation API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_dir = Path(tempfile.mkdtemp())

    def test_get_brush_validation_data_legacy_system(self):
        """Test getting brush validation data for legacy system."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_data = [
                {
                    "input_text": "Simpson Chubby 2",
                    "system_used": "legacy",
                    "matched": {"brand": "Simpson", "model": "Chubby 2"},
                    "match_type": "regex",
                    "all_strategies": [],
                }
            ]
            mock_cli.load_month_data.return_value = mock_data
            mock_cli.sort_entries.return_value = mock_data

            response = self.client.get("/api/brush-validation/data/2025-08/legacy")

            assert response.status_code == 200
            data = response.json()
            assert "entries" in data
            assert len(data["entries"]) == 1
            assert data["entries"][0]["input_text"] == "Simpson Chubby 2"
            assert data["entries"][0]["system_used"] == "legacy"

    def test_get_brush_validation_data_scoring_system(self):
        """Test getting brush validation data for scoring system."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_data = [
                {
                    "input_text": "Declaration B2",
                    "system_used": "scoring",
                    "best_result": {
                        "strategy": "known_brush",
                        "score": 95,
                        "result": {"brand": "Declaration Grooming", "model": "B2"},
                    },
                    "all_strategies": [
                        {"strategy": "known_brush", "score": 95, "result": {}},
                        {"strategy": "dual_component", "score": 60, "result": {}},
                    ],
                }
            ]
            mock_cli.load_month_data.return_value = mock_data
            mock_cli.sort_entries.return_value = mock_data

            response = self.client.get("/api/brush-validation/data/2025-08/scoring")

            assert response.status_code == 200
            data = response.json()
            assert "entries" in data
            assert len(data["entries"]) == 1
            assert data["entries"][0]["input_text"] == "Declaration B2"
            assert data["entries"][0]["system_used"] == "scoring"
            assert data["entries"][0]["best_result"]["score"] == 95

    def test_get_validation_statistics(self):
        """Test getting validation statistics for a month."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.get_validation_statistics.return_value = {
                "total_entries": 100,
                "validated_count": 25,
                "overridden_count": 10,
                "unvalidated_count": 65,
                "validation_rate": 0.35,
            }

            response = self.client.get("/api/brush-validation/statistics/2025-08")

            assert response.status_code == 200
            data = response.json()
            assert data["total_entries"] == 100
            assert data["validated_count"] == 25
            assert data["overridden_count"] == 10
            assert data["unvalidated_count"] == 65
            assert data["validation_rate"] == 0.35

    def test_record_validation_action(self):
        """Test recording user validation action."""
        validation_data = {
            "input_text": "Simpson Chubby 2",
            "month": "2025-08",
            "system_used": "legacy",
            "action": "validate",
            "system_choice": {
                "strategy": "legacy",
                "score": None,
                "result": {"brand": "Simpson", "model": "Chubby 2"},
            },
            "user_choice": {
                "strategy": "legacy",
                "score": None,
                "result": {"brand": "Simpson", "model": "Chubby 2"},
            },
            "all_brush_strategies": [],
        }

        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.user_actions_manager.record_validation = Mock()

            response = self.client.post("/api/brush-validation/action", json=validation_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data

            mock_cli.user_actions_manager.record_validation.assert_called_once()

    def test_record_override_action(self):
        """Test recording user override action."""
        override_data = {
            "input_text": "Declaration B2",
            "month": "2025-08",
            "system_used": "scoring",
            "action": "override",
            "system_choice": {
                "strategy": "known_brush",
                "score": 95,
                "result": {"brand": "Declaration Grooming", "model": "B2"},
            },
            "user_choice": {
                "strategy": "dual_component",
                "score": 60,
                "result": {"brand": "Declaration Grooming", "model": "B2"},
            },
            "all_brush_strategies": [
                {"strategy": "known_brush", "score": 95, "result": {}},
                {"strategy": "dual_component", "score": 60, "result": {}},
            ],
        }

        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.user_actions_manager.record_override = Mock()

            response = self.client.post("/api/brush-validation/action", json=override_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data

            mock_cli.user_actions_manager.record_override.assert_called_once()

    def test_invalid_system_name(self):
        """Test error handling for invalid system name."""
        response = self.client.get("/api/brush-validation/data/2025-08/invalid")

        assert response.status_code == 422  # Validation error

    def test_invalid_month_format(self):
        """Test error handling for invalid month format."""
        response = self.client.get("/api/brush-validation/data/2025-8/legacy")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_missing_month_data(self):
        """Test handling missing month data gracefully."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.load_month_data.return_value = []
            mock_cli.sort_entries.return_value = []

            response = self.client.get("/api/brush-validation/data/2025-12/legacy")

            assert response.status_code == 200
            data = response.json()
            assert data["entries"] == []

    def test_sort_entries_by_criteria(self):
        """Test sorting entries by different criteria."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.load_month_data.return_value = [
                {"input_text": "Entry 1", "system_used": "legacy"},
                {"input_text": "Entry 2", "system_used": "scoring"},
            ]
            mock_cli.sort_entries.return_value = [
                {"input_text": "Entry 2", "system_used": "scoring"},
                {"input_text": "Entry 1", "system_used": "legacy"},
            ]

            response = self.client.get(
                "/api/brush-validation/data/2025-08/legacy?sort_by=ambiguity"
            )

            assert response.status_code == 200
            mock_cli.sort_entries.assert_called_once()

    def test_pagination_support(self):
        """Test pagination support for large datasets."""
        entries = [{"input_text": f"Entry {i}", "system_used": "legacy"} for i in range(50)]

        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            mock_cli.load_month_data.return_value = entries
            mock_cli.sort_entries.return_value = entries

            response = self.client.get(
                "/api/brush-validation/data/2025-08/legacy?page=1&page_size=20"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["entries"]) == 20
            assert "pagination" in data
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["page_size"] == 20
            assert data["pagination"]["total"] == 50
            assert data["pagination"]["pages"] == 3

    def test_error_handling_invalid_action_data(self):
        """Test error handling for invalid action data."""
        invalid_data = {
            "input_text": "Test",
            # Missing required fields
        }

        response = self.client.post("/api/brush-validation/action", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_get_available_months_for_validation(self):
        """Test getting available months for validation."""
        with patch("api.brush_validation.get_available_months") as mock_months:
            mock_months.return_value = ["2025-07", "2025-08", "2025-09"]

            response = self.client.get("/api/brush-validation/months")

            assert response.status_code == 200
            data = response.json()
            assert "months" in data
            assert len(data["months"]) == 3
            assert "2025-08" in data["months"]

    def test_dual_component_brush_saves_to_handle_and_knot_sections(self):
        """Test that dual-component brushes are saved to handle and knot sections, not brush section."""
        with patch("api.brush_validation.BrushValidationCLI") as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli

            # Mock the user actions manager to capture what's being saved
            mock_user_actions_manager = Mock()
            mock_cli.user_actions_manager = mock_user_actions_manager

            # Mock getting comment IDs
            mock_cli.get_comment_ids_for_input_text.return_value = ["test_comment_id"]

            # Mock loading brush data
            mock_brush_data = {
                "matched": {
                    "strategy": "unified",
                    "score": 65,
                    "brand": "Alpha",
                    "model": None,  # Dual-component brush has null model
                    "handle": {
                        "brand": "Alpha",
                        "model": "Outlaw",
                        "source_text": "Alpha Shaving Works Outlaw 28mm G5",
                    },
                    "knot": {
                        "brand": "Alpha",
                        "model": "G5",
                        "fiber": "Synthetic",
                        "knot_size_mm": 28,
                        "source_text": "Alpha Shaving Works Outlaw 28mm G5",
                    },
                    "user_intent": "dual_component",
                },
                "all_strategies": [
                    {
                        "strategy": "unified",
                        "score": 65,
                        "brand": "Alpha",
                        "model": None,
                        "handle": {"brand": "Alpha", "model": "Outlaw"},
                        "knot": {
                            "brand": "Alpha",
                            "model": "G5",
                            "fiber": "Synthetic",
                            "knot_size_mm": 28,
                        },
                    }
                ],
                "input_text": "Alpha Shaving Works Outlaw 28mm G5",
                "normalized_text": "alpha shaving works outlaw 28mm g5",
            }
            mock_cli.load_brush_data_for_input_text.return_value = mock_brush_data

            # Test data for a dual-component brush - simplified API
            dual_component_validation_data = {
                "input_text": "Alpha Shaving Works Outlaw 28mm G5",
                "month": "2025-06",
                "system_used": "scoring",
                "action": "validate",
            }

            # Make the API call
            response = self.client.post(
                "/api/brush-validation/action", json=dual_component_validation_data
            )

            # Log the response for debugging
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

            # Verify the API call succeeded
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify that the validation was recorded using the new method
            mock_user_actions_manager.record_validation_with_data.assert_called_once()

            # Get the actual call arguments to verify what was passed
            call_args = mock_user_actions_manager.record_validation_with_data.call_args
            brush_data = call_args[1]["brush_data"]

            # Verify the structure shows this is a dual-component brush
            assert brush_data["matched"]["brand"] == "Alpha"
            # Dual-component indicator
            assert brush_data["matched"]["model"] is None
            assert "handle" in brush_data["matched"]
            assert "knot" in brush_data["matched"]
            assert brush_data["matched"]["handle"]["brand"] == "Alpha"
            assert brush_data["matched"]["handle"]["model"] == "Outlaw"
            assert brush_data["matched"]["knot"]["brand"] == "Alpha"
            assert brush_data["matched"]["knot"]["model"] == "G5"

            # This test now verifies that the backend handles all the business logic
            # and the frontend only sends minimal data

    def test_dual_component_brush_field_type_determination_bug(self):
        """Test that exposes the bug in field type determination for dual-component brushes."""
        # Import the actual class to test the logic directly
        # manager = BrushUserActionsManager() # This line is removed as per the new_code

        # Test data representing a dual-component brush result
        dual_component_result = {
            "brand": "Alpha",
            "model": None,  # Dual-component brush has null model
            "handle": {
                "brand": "Alpha",
                "model": "Outlaw",
                "source_text": "Alpha Shaving Works Outlaw 28mm G5",
            },
            "knot": {
                "brand": "Alpha",
                "model": "G5",
                "fiber": "Synthetic",
                "knot_size_mm": 28,
                "source_text": "Alpha Shaving Works Outlaw 28mm G5",
            },
            "user_intent": "dual_component",
        }

        # Test the field type determination logic
        field_type = BrushUserActionsManager._determine_field_type(dual_component_result)

        # This exposes the bug: dual-component brushes should be saved to handle and knot sections,
        # but the current logic incorrectly returns "brush" because it sees brand exists but model is None
        print(f"Field type determined: {field_type}")
        print("Expected: handle and knot sections (split_brush)")
        print(f"Actual: {field_type}")

        # The bug: this should return "split_brush" but it returns "brush"
        # because the logic sees brand exists but model is None and defaults to "brush"
        assert field_type == "split_brush", (
            f"Expected dual-component brush to be saved as 'split_brush' "
            f"(which would split into handle and knot sections), "
            f"but got '{field_type}' instead. "
            f"This means dual-component brushes are being saved to the brush section "
            f"instead of being properly split into handle and knot sections."
        )

    def test_dual_component_brush_stored_in_correct_sections(self):
        """Test that dual-component brushes are stored in handle and knot sections, not split_brush."""
        # Import the actual classes to test the real logic
        from sotd.match.brush_user_actions import BrushUserActionsManager
        from sotd.match.correct_matches_updater import CorrectMatchesUpdater

        # Create a temporary manager instance
        manager = BrushUserActionsManager()

        # Test data representing a dual-component brush result
        dual_component_result = {
            "brand": "Alpha",
            "model": None,  # Dual-component brush has null model
            "handle": {
                "brand": "Alpha",
                "model": "Outlaw",
                "source_text": "Alpha Shaving Works Outlaw 28mm G5",
            },
            "knot": {
                "brand": "Alpha",
                "model": "G5",
                "fiber": "Synthetic",
                "knot_size_mm": 28,
                "source_text": "Alpha Shaving Works Outlaw 28mm G5",
            },
            "user_intent": "dual_component",
        }

        # Test the field type determination logic
        field_type = manager._determine_field_type(dual_component_result)

        # This should return "split_brush" to indicate it needs special handling
        assert (
            field_type == "split_brush"
        ), f"Expected dual-component brush to return 'split_brush', but got '{field_type}'"

        # Now test that the CorrectMatchesUpdater properly handles split_brush
        # by storing components in the correct sections
        updater = CorrectMatchesUpdater()

        # Mock the save method to capture what's being written
        original_save = updater.save_correct_matches
        saved_data = None

        def mock_save(data):
            nonlocal saved_data
            saved_data = data
            # Don't actually save to file during test

        updater.save_correct_matches = mock_save

        # Test the update method with our dual-component brush
        updater.add_or_update_entry(
            "alpha shaving works outlaw 28mm g5",
            dual_component_result,
            "validated",
            "split_brush",  # This should trigger special handling
        )

        # Verify the data structure
        assert saved_data is not None, "No data was saved"

        # The bug: this should NOT have a split_brush section
        assert "split_brush" not in saved_data, (
            "Dual-component brush incorrectly created 'split_brush' section. "
            "It should be split into separate handle and knot entries."
        )

        # Instead, it should have the handle component stored under handle section
        assert "handle" in saved_data, "Handle section should exist"
        assert "Alpha" in saved_data["handle"], "Alpha brand should exist in handle section"
        assert (
            "Outlaw" in saved_data["handle"]["Alpha"]
        ), "Outlaw model should exist under Alpha handle"

        # And the knot component stored under knot section
        assert "knot" in saved_data, "Knot section should exist"
        assert "Alpha" in saved_data["knot"], "Alpha brand should exist in knot section"
        assert "G5" in saved_data["knot"]["Alpha"], "G5 model should exist under Alpha knot"

        # The normalized text should be in both sections
        handle_entries = saved_data["handle"]["Alpha"]["Outlaw"]
        knot_entries = saved_data["knot"]["Alpha"]["G5"]

        assert (
            "alpha shaving works outlaw 28mm g5" in handle_entries
        ), "Dual-component brush text should be stored in handle section"
        assert (
            "alpha shaving works outlaw 28mm g5" in knot_entries
        ), "Dual-component brush text should be stored in knot section"

        # Restore original method
        updater.save_correct_matches = original_save
