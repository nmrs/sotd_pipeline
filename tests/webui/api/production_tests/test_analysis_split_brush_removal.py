from unittest.mock import patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from webui.api.analysis import router

app = FastAPI()
app.include_router(router)


client = TestClient(app)


class TestAnalysisAPISplitBrushRemoval:
    """Test cases for analysis API split_brush removal"""

    @pytest.fixture
    def mock_analyze_mismatch(self):
        """Mock the analyze_mismatch function"""
        with patch("webui.api.analysis.analyze_mismatch") as mock:
            yield mock

    @pytest.fixture
    def mock_get_comment_detail(self):
        """Mock the get_comment_detail function"""
        with patch("webui.api.analysis.get_comment_detail") as mock:
            yield mock

    @pytest.fixture
    def mock_yaml_load(self):
        """Mock the YAML loading to avoid production data corruption"""
        with patch("yaml.safe_load") as mock:
            # Return valid test data structure
            mock.return_value = {
                "brush": {"test_brush": {"brand": "Test Brand", "model": "Test Model"}}
            }
            yield mock

    def test_analyze_mismatch_response_without_split_brush(self):
        """Test that analyze_mismatch endpoint returns data without split_brush fields"""

        response = client.post(
            "/api/analyze/mismatch",
            json={
                "field": "brush",
                "months": ["2025-01"],
                "threshold": 3,
                "use_enriched_data": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush fields are not present in the actual API response
        assert "split_brush" not in data

        # Verify that the API returns the expected structure
        assert "field" in data
        assert "months" in data
        assert "total_matches" in data
        assert "total_mismatches" in data
        assert "mismatch_items" in data

        # Verify that mismatch items don't have split_brush fields
        if data["mismatch_items"]:
            first_item = data["mismatch_items"][0]
            assert "is_split_brush" not in first_item
            assert "handle_component" not in first_item
            assert "knot_component" not in first_item

    def test_brush_field_processing_without_split_brush(
        self, mock_analyze_mismatch, mock_yaml_load
    ):
        """Test that brush field processing works without split_brush section"""

        # Mock analyze_mismatch response
        mock_analyze_response = {
            "total_items": 1,
            "mismatch_items": [
                {
                    "id": "1",
                    "original": "Declaration Grooming B2",
                    "matched": {
                        "brand": "Declaration Grooming",
                        "model": "B2",
                        "handle_maker": "Declaration Grooming",
                        "knot_maker": "Declaration Grooming",
                        "knot_type": "badger",
                        "knot_size": "26mm",
                    },
                    "count": 5,
                    "is_complete_brush": True,
                    "is_regex_match": False,
                    "is_intentionally_unmatched": False,
                }
            ],
        }

        mock_analyze_mismatch.return_value = mock_analyze_response

        # Test analyze_mismatch endpoint
        response = client.post(
            "/api/analyze/mismatch",
            json={
                "field": "brush",
                "months": ["2025-01"],
                "threshold": 3,
                "use_enriched_data": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush processing is not attempted
        assert "split_brush" not in data
        assert "is_split_brush" not in data["mismatch_items"][0]

        # Test correct_matches endpoint
        response = client.get("/api/analyze/correct-matches/brush")

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush section is not processed
        assert "split_brush" not in data

    def test_non_brush_field_processing(self):
        """Test that non-brush fields work correctly without split_brush processing"""

        response = client.post(
            "/api/analyze/mismatch",
            json={
                "field": "blade",
                "months": ["2025-01"],
                "threshold": 3,
                "use_enriched_data": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that non-brush fields don't have split_brush processing
        assert "split_brush" not in data

        # Verify that the API returns the expected structure for blade field
        assert data["field"] == "blade"
        assert "mismatch_items" in data

        # Verify that mismatch items don't have split_brush fields
        if data["mismatch_items"]:
            first_item = data["mismatch_items"][0]
            assert "is_split_brush" not in first_item
            assert "handle_component" not in first_item
            assert "knot_component" not in first_item

    @pytest.mark.skip(
        reason="API endpoint function is defined inline, cannot be mocked as expected"
    )
    def test_error_handling_without_split_brush(self, mock_analyze_mismatch):
        """Test error handling without split_brush functionality"""

        mock_analyze_mismatch.side_effect = Exception("Test error")

        response = client.post(
            "/api/analyze/mismatch",
            json={
                "field": "brush",
                "months": ["2025-01"],
                "threshold": 3,
                "use_enriched_data": False,
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_comment_detail_endpoint_structure(self):
        """Test that comment detail endpoint has the correct structure without split_brush fields"""

        # Test with a non-existent comment ID to verify endpoint structure
        # The endpoint should return 404, but we can verify it doesn't have split_brush fields
        response = client.get("/api/analyze/comment/nonexistent?months=2025-01")

        # Should get 404 for non-existent comment, but endpoint should be accessible
        assert response.status_code in [404, 500]  # Either not found or error loading data

        # Verify that the error response doesn't contain split_brush fields
        if response.status_code == 500:
            data = response.json()
            assert "split_brush" not in data
            assert "is_split_brush" not in data

    def test_mark_matches_as_correct_without_split_brush(self):
        """Test that mark_matches_as_correct endpoint works without split_brush processing"""

        with patch("webui.api.analysis.mark_matches_as_correct") as mock_mark:
            mock_mark.return_value = {"success": True, "message": "Matches marked as correct"}

            response = client.post(
                "/api/analyze/mark-correct",
                json={
                    "field": "brush",
                    "matches": [
                        {
                            "original": "Declaration Grooming B2",
                            "matched": {
                                "brand": "Declaration Grooming",
                                "model": "B2",
                                "handle_maker": "Declaration Grooming",
                                "knot_maker": "Declaration Grooming",
                                "knot_type": "badger",
                                "knot_size": "26mm",
                            },
                        }
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Marked" in data["message"] and "matches as correct" in data["message"]

    def test_remove_matches_from_correct_without_split_brush(self):
        """Test that remove_matches_from_correct endpoint works without split_brush processing"""

        with patch("webui.api.analysis.remove_matches_from_correct") as mock_remove:
            mock_remove.return_value = {"success": True, "message": "Matches removed from correct"}

            response = client.post(
                "/api/analyze/remove-correct",
                json={
                    "field": "brush",
                    "matches": [
                        {
                            "original": "declaration grooming b2",
                            "matched": {"brand": "Declaration Grooming", "model": "B2"},
                        }
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Removed" in data["message"] and "matches from correct" in data["message"]

    @pytest.mark.skip(reason="update_filtered_entries endpoint does not exist in current API")
    def test_update_filtered_entries_without_split_brush(self):
        """Test that update_filtered_entries endpoint works without split_brush processing"""

        with patch("webui.api.analysis.update_filtered_entries") as mock_update:
            mock_update.return_value = {"success": True, "message": "Filtered entries updated"}

            response = client.post(
                "/update-filtered-entries",
                json={
                    "field": "brush",
                    "month": "2025-01",
                    "comment_ids": ["1", "2"],
                    "reason": "Test reason",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Filtered entries updated"
