"""Test configuration for webui tests."""

import pytest
from fastapi.testclient import TestClient

from webui.api.main import app


@pytest.fixture
def client():
    """Provide a test client for FastAPI app."""
    return TestClient(app)
