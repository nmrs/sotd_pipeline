"""Tests for extract override API and comment-detail pending merge."""

import pytest
from fastapi.testclient import TestClient

from sotd.extract.override_manager import OverrideManager
from webui.api.analysis import extract_product_field_data
from webui.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestExtractProductFieldData:
    def test_applied_override_shows_normalized(self):
        result = extract_product_field_data(
            {
                "original": "Ko",
                "normalized": "Koraat",
                "overridden": "Normalized",
                "matched": {"brand": "Koraat"},
            }
        )
        assert result is not None
        assert result.original == "Ko"
        assert result.override_value == "Koraat"
        assert result.override_pending is False

    def test_pending_yaml_override(self):
        result = extract_product_field_data(
            {"original": "Ko", "normalized": "Ko", "matched": None},
            yaml_override="Koraat",
        )
        assert result is not None
        assert result.override_value == "Koraat"
        assert result.override_pending is True

    def test_yaml_only_missing_field(self):
        result = extract_product_field_data(None, yaml_override="Feather")
        assert result is not None
        assert result.original == ""
        assert result.override_value == "Feather"
        assert result.override_pending is True


class TestExtractOverridesAPI:
    def test_put_and_get_with_tmp_yaml(self, client, tmp_path, monkeypatch):
        override_file = tmp_path / "extract_overrides.yaml"
        override_file.write_text("")
        monkeypatch.setenv("SOTD_DATA_DIR", str(tmp_path))

        put = client.put(
            "/api/extract-overrides/2026-08/testid1",
            json={"razor": "Gillette Tech", "blade": None},
        )
        assert put.status_code == 200
        assert put.json()["fields"]["razor"] == "Gillette Tech"
        assert "blade" not in put.json()["fields"]

        get = client.get("/api/extract-overrides/2026-08/testid1")
        assert get.status_code == 200
        assert get.json()["fields"] == {"razor": "Gillette Tech"}

        # Clear razor
        clear = client.put(
            "/api/extract-overrides/2026-08/testid1",
            json={"razor": None},
        )
        assert clear.status_code == 200
        assert clear.json()["fields"] == {}

        manager = OverrideManager(override_file)
        manager.load_overrides()
        assert manager.overrides == {}
