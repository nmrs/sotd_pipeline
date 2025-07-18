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
    with patch("analysis.UnmatchedAnalyzer") as mock:
        analyzer_instance = MagicMock()
        mock.return_value = analyzer_instance

        # Mock load_matched_data to return test records
        test_records = [
            {
                "razor": {
                    "original": "Unknown Razor 1",
                    "matched": None,
                    "_source_file": "test_file.json",
                    "_source_line": "123",
                }
            },
            {
                "razor": {
                    "original": "Unknown Razor 2",
                    "matched": None,
                    "_source_file": "test_file.json",
                    "_source_line": "456",
                }
            },
        ]
        analyzer_instance.load_matched_data.return_value = test_records

        # Mock _process_field_unmatched to populate all_unmatched
        def mock_process(record, field, all_unmatched):
            if field == "razor" and record.get("razor"):
                razor_data = record["razor"]
                if razor_data.get("matched") is None:
                    original = razor_data.get("original", "")
                    file_info = {
                        "file": razor_data.get("_source_file", ""),
                        "line": razor_data.get("_source_line", "unknown"),
                    }
                    if original not in all_unmatched:
                        all_unmatched[original] = []
                    all_unmatched[original].append(file_info)

        analyzer_instance._process_field_unmatched = mock_process

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
        assert len(data["results"]) == 2

        # Check first result
        first_result = data["results"][0]
        assert "original_text" in first_result
        assert "use_count" in first_result
        assert "source_files" in first_result
        assert "source_lines" in first_result

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
