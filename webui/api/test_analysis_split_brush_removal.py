import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import FastAPI
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
    def mock_get_correct_matches(self):
        """Mock the get_correct_matches function"""
        with patch("webui.api.analysis.get_correct_matches") as mock:
            yield mock

    @pytest.fixture
    def mock_get_comment_detail(self):
        """Mock the get_comment_detail function"""
        with patch("webui.api.analysis.get_comment_detail") as mock:
            yield mock

    def test_analyze_mismatch_response_without_split_brush(self, mock_analyze_mismatch):
        """Test that analyze_mismatch endpoint returns data without split_brush fields"""

        # Mock response without split_brush fields
        mock_response = {
            "total_items": 2,
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
                },
                {
                    "id": "2",
                    "original": "Alpha Amber",
                    "matched": {
                        "brand": "Alpha",
                        "model": "Amber",
                        "handle_maker": "Alpha",
                        "knot_maker": "Alpha",
                        "knot_type": "badger",
                        "knot_size": "24mm",
                    },
                    "count": 3,
                    "is_complete_brush": True,
                    "is_regex_match": False,
                    "is_intentionally_unmatched": False,
                },
            ],
        }

        mock_analyze_mismatch.return_value = mock_response

        response = client.get(
            "/analyze-mismatch?field=brush&month=2025-01&threshold=3&use_enriched_data=false"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush fields are not present
        assert "split_brush" not in data
        assert "is_split_brush" not in data["mismatch_items"][0]
        assert "is_split_brush" not in data["mismatch_items"][1]

        # Verify that other fields are present
        assert data["total_items"] == 2
        assert len(data["mismatch_items"]) == 2
        assert data["mismatch_items"][0]["original"] == "Declaration Grooming B2"
        assert data["mismatch_items"][1]["original"] == "Alpha Amber"

    def test_get_correct_matches_response_without_split_brush(self, mock_get_correct_matches):
        """Test that get_correct_matches endpoint returns data without split_brush section"""

        # Mock response without split_brush section
        mock_response = {
            "brush": {
                "declaration grooming b2": {
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
            },
            "handle": {},
            "knot": {},
        }

        mock_get_correct_matches.return_value = mock_response

        response = client.get("/correct-matches?field=brush")

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush section is not present
        assert "split_brush" not in data

        # Verify that other sections are present
        assert "brush" in data
        assert "handle" in data
        assert "knot" in data
        assert "declaration grooming b2" in data["brush"]

    def test_brush_field_processing_without_split_brush(
        self, mock_analyze_mismatch, mock_get_correct_matches
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

        # Mock correct_matches response without split_brush section
        mock_correct_matches_response = {
            "brush": {
                "declaration grooming b2": {
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
            },
            "handle": {},
            "knot": {},
        }

        mock_analyze_mismatch.return_value = mock_analyze_response
        mock_get_correct_matches.return_value = mock_correct_matches_response

        # Test analyze_mismatch endpoint
        response = client.get(
            "/analyze-mismatch?field=brush&month=2025-01&threshold=3&use_enriched_data=false"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush processing is not attempted
        assert "split_brush" not in data
        assert "is_split_brush" not in data["mismatch_items"][0]

        # Test correct_matches endpoint
        response = client.get("/correct-matches?field=brush")

        assert response.status_code == 200
        data = response.json()

        # Verify that split_brush section is not processed
        assert "split_brush" not in data

    def test_non_brush_field_processing(self, mock_analyze_mismatch):
        """Test that non-brush fields work correctly without split_brush processing"""

        mock_response = {
            "total_items": 1,
            "mismatch_items": [
                {
                    "id": "1",
                    "original": "Feather Hi-Stainless",
                    "matched": {
                        "brand": "Feather",
                        "model": "Hi-Stainless",
                    },
                    "count": 10,
                    "is_regex_match": False,
                    "is_intentionally_unmatched": False,
                }
            ],
        }

        mock_analyze_mismatch.return_value = mock_response

        response = client.get(
            "/analyze-mismatch?field=blade&month=2025-01&threshold=3&use_enriched_data=false"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify that non-brush fields don't have split_brush processing
        assert "split_brush" not in data
        assert data["mismatch_items"][0]["original"] == "Feather Hi-Stainless"

    def test_error_handling_without_split_brush(self, mock_analyze_mismatch):
        """Test error handling without split_brush functionality"""

        mock_analyze_mismatch.side_effect = Exception("Test error")

        response = client.get(
            "/analyze-mismatch?field=brush&month=2025-01&threshold=3&use_enriched_data=false"
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_comment_detail_response_without_split_brush(self, mock_get_comment_detail):
        """Test that comment detail endpoint works without split_brush considerations"""

        mock_response = {
            "id": "1",
            "text": "Test comment with Declaration Grooming B2",
            "author": "testuser",
            "timestamp": "2025-01-01T00:00:00Z",
        }

        mock_get_comment_detail.return_value = mock_response

        response = client.get("/comment-detail?comment_id=1&field=brush&month=2025-01")

        assert response.status_code == 200
        data = response.json()

        # Verify that comment detail works without split_brush processing
        assert data["id"] == "1"
        assert data["text"] == "Test comment with Declaration Grooming B2"
        assert data["author"] == "testuser"

    def test_mark_matches_as_correct_without_split_brush(self):
        """Test that mark_matches_as_correct endpoint works without split_brush processing"""

        with patch("webui.api.analysis.mark_matches_as_correct") as mock_mark:
            mock_mark.return_value = {"success": True, "message": "Matches marked as correct"}

            response = client.post(
                "/mark-matches-as-correct",
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
            assert data["message"] == "Matches marked as correct"

    def test_remove_matches_from_correct_without_split_brush(self):
        """Test that remove_matches_from_correct endpoint works without split_brush processing"""

        with patch("webui.api.analysis.remove_matches_from_correct") as mock_remove:
            mock_remove.return_value = {"success": True, "message": "Matches removed from correct"}

            response = client.post(
                "/remove-matches-from-correct",
                json={"field": "brush", "matches": ["declaration grooming b2"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Matches removed from correct"

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
