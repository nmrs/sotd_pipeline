"""Tests for brush validation API endpoints."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
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
