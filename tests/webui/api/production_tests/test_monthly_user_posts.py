#!/usr/bin/env python3
"""Tests for Monthly User Posts API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from monthly_user_posts import router  # noqa: E402

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

    @patch("monthly_user_posts.Path.exists")
    @patch("monthly_user_posts.Path.glob")
    def test_get_available_months_success(self, mock_glob, mock_exists):
        """Test successful retrieval of available months."""
        mock_exists.return_value = True

        # Mock file paths
        mock_file_paths = [Mock(stem="2025-06"), Mock(stem="2025-05"), Mock(stem="2025-04")]
        mock_glob.return_value = mock_file_paths

        # Mock file reading
        mock_data = {"data": [{"author": "user1"}, {"author": "user2"}]}

        with patch("builtins.open", Mock(return_value=Mock())):
            with patch("json.load", Mock(return_value=mock_data)):
                response = client.get("/api/monthly-user-posts/months")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 3
                assert data[0]["month"] == "2025-06"  # Newest first
                assert data[0]["has_data"] is True
                assert data[0]["user_count"] == 2

    @patch("monthly_user_posts.Path.exists")
    def test_get_available_months_no_directory(self, mock_exists):
        """Test handling when enriched directory doesn't exist."""
        mock_exists.return_value = False

        response = client.get("/api/monthly-user-posts/months")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_users_for_month_success(self, mock_analyzer_class):
        """Test successful retrieval of users for a month."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock enriched data
        mock_enriched_data = [
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user2"},
            {"author": "user3"},
        ]
        mock_analyzer.load_enriched_data.return_value = mock_enriched_data

        response = client.get("/users/2025-06")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Check user1 has highest post count
        user1 = next(user for user in data if user["username"] == "user1")
        assert user1["post_count"] == 2

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_users_for_month_with_search(self, mock_analyzer_class):
        """Test user search functionality."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock enriched data
        mock_enriched_data = [{"author": "user1"}, {"author": "user2"}, {"author": "testuser"}]
        mock_analyzer.load_enriched_data.return_value = mock_enriched_data

        response = client.get("/api/monthly-user-posts/users/2025-06?search=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "testuser"

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_users_for_month_no_data(self, mock_analyzer_class):
        """Test handling when month has no data."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.load_enriched_data.return_value = []

        response = client.get("/users/2025-06")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_user_posting_analysis_success(self, mock_analyzer_class):
        """Test successful user posting analysis."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock enriched data
        mock_enriched_data = [
            {
                "author": "testuser",
                "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                "id": "comment1",
            }
        ]
        mock_analyzer.load_enriched_data.return_value = mock_enriched_data

        # Mock analysis result
        mock_analysis = {
            "user": "testuser",
            "posted_days": 1,
            "missed_days": 29,
            "posted_dates": ["2025-06-01"],
            "comment_ids": ["comment1"],
        }
        mock_analyzer.analyze_user_posting.return_value = mock_analysis

        response = client.get("/analysis/2025-06/testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["user"] == "testuser"
        assert data["posted_days"] == 1
        assert data["missed_days"] == 29

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_user_posting_analysis_no_data(self, mock_analyzer_class):
        """Test handling when month has no data."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.load_enriched_data.return_value = []

        response = client.get("/analysis/2025-06/testuser")
        assert response.status_code == 404
        data = response.json()
        assert "No data available" in data["detail"]

    @patch("monthly_user_posts.UserPostingAnalyzer")
    def test_get_user_posting_analysis_user_not_found(self, mock_analyzer_class):
        """Test handling when user has no posts in month."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock enriched data with different user
        mock_enriched_data = [
            {
                "author": "otheruser",
                "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                "id": "comment1",
            }
        ]
        mock_analyzer.load_enriched_data.return_value = mock_enriched_data

        # Mock analysis result for user with no posts
        mock_analysis = {
            "user": "testuser",
            "posted_days": 0,
            "missed_days": 30,
            "posted_dates": [],
            "comment_ids": [],
        }
        mock_analyzer.analyze_user_posting.return_value = mock_analysis

        response = client.get("/analysis/2025-06/testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["posted_days"] == 0
        assert data["missed_days"] == 30
