#!/usr/bin/env python3
"""Tests for analysis endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_analyzer():
    """Mock UnmatchedAnalyzer for testing."""
    with patch("webui.api.analysis.UnmatchedAnalyzer") as mock:
        analyzer_instance = MagicMock()
        mock.return_value = analyzer_instance

        # Mock analyze_unmatched to return expected data structure
        def mock_analyze_unmatched(args):
            # Return the data structure that the API expects
            return {
                "Unknown Razor 1": [
                    {
                        "file": "test_file.json",
                        "line": "123",
                        "comment_id": "test_comment_1",
                    }
                ],
                "Unknown Razor 2": [
                    {
                        "file": "test_file.json",
                        "line": "456",
                        "comment_id": "test_comment_2",
                    }
                ],
            }

        analyzer_instance.analyze_unmatched = mock_analyze_unmatched

        yield mock


class TestAnalysisEndpoints:
    """Test analysis endpoints."""

    def test_analyze_unmatched_success(self, client, mock_analyzer):
        """Test successful unmatched analysis."""
        request_data = {"field": "razor", "months": ["2025-01"], "limit": 10}

        response = client.post("/api/analyze/unmatched", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["field"] == "razor"
        assert data["months"] == ["2025-01"]
        assert data["total_unmatched"] == 2
        assert len(data["unmatched_items"]) == 2

        # Check first result
        first_result = data["unmatched_items"][0]
        assert "item" in first_result
        assert "count" in first_result
        assert "examples" in first_result
        assert "comment_ids" in first_result

    def test_analyze_unmatched_invalid_field(self, client):
        """Test analysis with invalid field."""
        request_data = {"field": "invalid_field", "months": ["2025-01"], "limit": 10}

        response = client.post("/api/analyze/unmatched", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported field" in data["detail"]

    def test_analyze_unmatched_invalid_month_format(self, client):
        """Test analysis with invalid month format."""
        request_data = {"field": "razor", "months": ["2025-1"], "limit": 10}  # Invalid format

        response = client.post("/api/analyze/unmatched", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "Invalid month format" in data["detail"]

    def test_analyze_unmatched_empty_months(self, client):
        """Test analysis with empty months list."""
        request_data = {"field": "razor", "months": [], "limit": 10}

        response = client.post("/api/analyze/unmatched", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "At least one month must be specified" in data["detail"]

    def test_analyze_unmatched_limit_validation(self, client):
        """Test limit validation."""
        # Test limit too low
        request_data = {"field": "razor", "months": ["2025-01"], "limit": 0}

        response = client.post("/api/analyze/unmatched", json=request_data)
        assert response.status_code == 422  # Validation error

        # Test limit too high
        request_data["limit"] = 1001
        response = client.post("/api/analyze/unmatched", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_analyze_unmatched_brush_case_insensitive_grouping(self, client):
        """Test that brush items are grouped case-insensitively."""
        with patch("webui.api.analysis.UnmatchedAnalyzer") as mock:
            analyzer_instance = MagicMock()
            mock.return_value = analyzer_instance

            # Mock analyze_unmatched to return brush data with different cases
            def mock_analyze_unmatched(args):
                return {
                    "AP Shave Co. 24mm 'Synbad' Synthetic": [
                        {
                            "file": "test_file1.json",
                            "line": "123",
                            "comment_id": "test_comment_1",
                        }
                    ],
                    "AP Shave Co. 24mm 'SynBad' Synthetic": [
                        {
                            "file": "test_file2.json",
                            "line": "456",
                            "comment_id": "test_comment_2",
                        }
                    ],
                }

            analyzer_instance.analyze_unmatched = mock_analyze_unmatched

            request_data = {"field": "brush", "months": ["2025-01"], "limit": 10}
            response = client.post("/api/analyze/unmatched", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Should only have one item due to case-insensitive grouping
            assert data["total_unmatched"] == 1
            assert len(data["unmatched_items"]) == 1

            # Should use the first occurrence as the display text
            first_item = data["unmatched_items"][0]
            assert first_item["item"] == "AP Shave Co. 24mm 'Synbad' Synthetic"
            assert first_item["count"] == 2  # Combined count from both cases
