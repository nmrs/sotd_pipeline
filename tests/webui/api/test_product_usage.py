#!/usr/bin/env python3
"""Tests for Product Usage API endpoints."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from webui.api.product_usage import router  # noqa: E402

# Create test client
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestProductUsageAPI:
    """Test cases for Product Usage API endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/product-usage/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "product-usage"

    def test_get_products_invalid_product_type(self):
        """Test handling of invalid product type."""
        response = client.get("/api/product-usage/products/2025-06/invalid")
        assert response.status_code == 400
        assert "Invalid product type" in response.json()["detail"]

    @patch("webui.api.product_usage.Path.exists")
    def test_get_products_for_month_no_data(self, mock_exists):
        """Test handling when month has no data."""
        mock_exists.return_value = False

        response = client.get("/api/product-usage/products/2025-06/razor")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_products_for_month_razor(self, mock_open, mock_exists):
        """Test getting products for razor type."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
                {
                    "author": "user2",
                    "id": "2",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
                {
                    "author": "user1",
                    "id": "3",
                    "razor": {
                        "matched": {"brand": "Merkur", "model": "34C"},
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            response = client.get("/api/product-usage/products/2025-06/razor")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            # Should be sorted by usage count
            assert data[0]["brand"] == "Gillette"
            assert data[0]["model"] == "Tech"
            assert data[0]["usage_count"] == 2
            assert data[0]["unique_users"] == 2

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_products_for_month_with_search(self, mock_open, mock_exists):
        """Test product search functionality."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
                {
                    "author": "user2",
                    "id": "2",
                    "razor": {
                        "matched": {"brand": "Merkur", "model": "34C"},
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            response = client.get("/api/product-usage/products/2025-06/razor?search=Gillette")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["brand"] == "Gillette"

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_products_for_month_soap(self, mock_open, mock_exists):
        """Test getting products for soap type."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "soap": {
                        "matched": {"brand": "Grooming Dept", "scent": "Laundry II"},
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            response = client.get("/api/product-usage/products/2025-06/soap")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["brand"] == "Grooming Dept"
            assert data[0]["model"] == "Laundry II"

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_product_usage_analysis_success(self, mock_open, mock_exists):
        """Test successful product usage analysis."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
                {
                    "author": "user2",
                    "id": "2",
                    "thread_title": "Monday SOTD Thread - Jun 01, 2025",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
                {
                    "author": "user1",
                    "id": "3",
                    "thread_title": "Tuesday SOTD Thread - Jun 02, 2025",
                    "razor": {
                        "matched": {"brand": "Gillette", "model": "Tech"},
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            with patch(
                "webui.api.product_usage._extract_date_from_thread_title"
            ) as mock_extract:
                # Mock date extraction
                from datetime import datetime

                def extract_date(title):
                    if "Jun 01" in title:
                        return datetime(2025, 6, 1)
                    elif "Jun 02" in title:
                        return datetime(2025, 6, 2)
                    return datetime(2025, 6, 1)

                mock_extract.side_effect = extract_date

                response = client.get(
                    "/api/product-usage/analysis/2025-06/razor/Gillette/Tech"
                )
                assert response.status_code == 200
                data = response.json()
                assert data["product"]["brand"] == "Gillette"
                assert data["product"]["model"] == "Tech"
                assert data["total_usage"] == 3
                assert data["unique_users"] == 2
                assert len(data["users"]) == 2
                # user1 should have higher usage count
                assert data["users"][0]["username"] == "user1"
                assert data["users"][0]["usage_count"] == 2

    @patch("webui.api.product_usage.Path.exists")
    def test_get_product_usage_analysis_no_data(self, mock_exists):
        """Test handling when month has no data."""
        mock_exists.return_value = False

        response = client.get("/api/product-usage/analysis/2025-06/razor/Gillette/Tech")
        assert response.status_code == 404

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_product_usage_analysis_product_not_found(self, mock_open, mock_exists):
        """Test handling when product is not found."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "razor": {
                        "matched": {"brand": "Merkur", "model": "34C"},
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            response = client.get(
                "/api/product-usage/analysis/2025-06/razor/Gillette/Tech"
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @patch("webui.api.product_usage.Path.exists")
    @patch("webui.api.product_usage.Path.open")
    def test_get_products_for_month_brush(self, mock_open, mock_exists):
        """Test getting products for brush type."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=False)
        mock_file.read.return_value = ""
        mock_open.return_value = mock_file

        enriched_data = {
            "data": [
                {
                    "author": "user1",
                    "id": "1",
                    "brush": {
                        "matched": {
                            "brand": "Semogue",
                            "model": "610",
                            "handle": {"brand": "Semogue", "model": "610"},
                            "knot": {"brand": "Semogue", "model": "610", "fiber": "Boar"},
                        },
                    },
                },
            ]
        }

        with patch("webui.api.product_usage.json.load", return_value=enriched_data):
            response = client.get("/api/product-usage/products/2025-06/brush")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["brand"] == "Semogue"
            assert data[0]["model"] == "610"

