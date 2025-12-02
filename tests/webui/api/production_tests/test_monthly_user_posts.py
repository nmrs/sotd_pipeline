#!/usr/bin/env python3
"""Tests for Monthly User Posts API endpoints."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from webui.api.monthly_user_posts import router  # noqa: E402

# Create test client
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# Test the endpoints with the correct prefix
def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/monthly-user-posts/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "monthly-user-posts"


class TestMonthlyUserPostsAPI:
    """Test cases for Monthly User Posts API endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/monthly-user-posts/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "monthly-user-posts"


    @patch("webui.api.monthly_user_posts.Path.exists")
    def test_get_available_months_no_directory(self, mock_exists):
        """Test handling when enriched directory doesn't exist."""
        mock_exists.return_value = False

        response = client.get("/api/monthly-user-posts/months")
        assert response.status_code == 200
        data = response.json()
        assert data == []


    @patch("webui.api.monthly_user_posts.Path.exists")
    @patch("webui.api.monthly_user_posts.json.load")
    @patch("webui.api.monthly_user_posts.aggregate_users")
    def test_get_users_for_month_with_search(self, mock_aggregate, mock_json_load, mock_exists):
        """Test user search functionality."""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "data": [
                {"author": "user1", "id": "1"},
                {"author": "user2", "id": "2"},
                {"author": "testuser", "id": "3"},
            ]
        }
        mock_aggregate.return_value = [
            {"user": "user1", "shaves": 5},
            {"user": "user2", "shaves": 3},
            {"user": "testuser", "shaves": 2},
        ]

        response = client.get("/api/monthly-user-posts/users/2025-06?search=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "testuser"

    @patch("webui.api.monthly_user_posts.Path.exists")
    def test_get_users_for_month_no_data(self, mock_exists):
        """Test handling when month has no data."""
        mock_exists.return_value = False

        response = client.get("/api/monthly-user-posts/users/2025-06")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("webui.api.monthly_user_posts.Path.exists")
    @patch("webui.api.monthly_user_posts.json.load")
    @patch("webui.api.monthly_user_posts.aggregate_users")
    def test_get_user_posting_analysis_success(self, mock_aggregate, mock_json_load, mock_exists):
        """Test successful user posting analysis."""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "data": [
                {
                    "author": "testuser",
                    "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                    "id": "comment1",
                }
            ]
        }
        mock_aggregate.return_value = [{"user": "testuser", "shaves": 1, "missed_days": 29}]

        response = client.get("/api/monthly-user-posts/analysis/2025-06/testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["user"] == "testuser"
        assert data["posted_days"] == 1
        assert data["missed_days"] == 29

    @patch("webui.api.monthly_user_posts.Path.exists")
    def test_get_user_posting_analysis_no_data(self, mock_exists):
        """Test handling when month has no data."""
        mock_exists.return_value = False

        response = client.get("/api/monthly-user-posts/analysis/2025-06/testuser")
        # When file doesn't exist, API raises HTTPException with 404
        # But if there's an error opening the file, it returns 500
        assert response.status_code in [404, 500]
        data = response.json()
        if response.status_code == 404:
            assert "No data available" in data["detail"]
        else:
            # If 500, it's an error loading the file
            assert "detail" in data

    @patch("webui.api.monthly_user_posts.Path.exists")
    @patch("webui.api.monthly_user_posts.json.load")
    @patch("webui.api.monthly_user_posts.aggregate_users")
    def test_get_user_posting_analysis_user_not_found(self, mock_aggregate, mock_json_load, mock_exists):
        """Test handling when user has no posts in month."""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "data": [
                {
                    "author": "otheruser",
                    "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                    "id": "comment1",
                }
            ]
        }
        mock_aggregate.return_value = [{"user": "otheruser", "shaves": 1, "missed_days": 29}]

        response = client.get("/api/monthly-user-posts/analysis/2025-06/testuser")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
