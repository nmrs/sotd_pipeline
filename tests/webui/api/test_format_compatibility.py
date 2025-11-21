"""Tests for format compatibility API endpoint."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from webui.api.main import app

client = TestClient(app)


@pytest.fixture
def sample_enriched_data():
    """Create sample enriched data for testing."""
    return {
        "data": [
            {
                "id": "comment1",
                "author": "user1",
                "razor": {
                    "original": "Gillette Tech",
                    "matched": {"brand": "Gillette", "model": "Tech", "format": "DE"},
                    "enriched": {"format": "DE"},
                },
                "blade": {
                    "original": "Feather Hi-Stainless",
                    "matched": {"brand": "Feather", "model": "Hi-Stainless", "format": "DE"},
                },
            },
            {
                "id": "comment2",
                "author": "user2",
                "razor": {
                    "original": "Gillette Tech",
                    "matched": {"brand": "Gillette", "model": "Tech", "format": "DE"},
                    "enriched": {"format": "DE"},
                },
                "blade": {
                    "original": "Feather AC",
                    "matched": {"brand": "Feather", "model": "Pro", "format": "AC"},
                },
            },
            {
                "id": "comment3",
                "author": "user3",
                "razor": {
                    "original": "Other Shavette",
                    "matched": {"brand": "Other Shavette", "format": "Shavette"},
                    "enriched": {"format": "Shavette (AC)"},
                },
                "blade": {
                    "original": "Feather AC",
                    "matched": {"brand": "Feather", "model": "Pro", "format": "AC"},
                },
            },
            {
                "id": "comment4",
                "author": "user4",
                "razor": {
                    "original": "Gillette Tech",
                    "matched": {"brand": "Gillette", "model": "Tech", "format": "DE"},
                },
                # Missing blade
            },
            {
                "id": "comment5",
                "author": "user5",
                "razor": {
                    "original": "Cartridge Razor",
                    "matched": {"brand": "Gillette", "format": "Cartridge/Disposable"},
                },
                "blade": {
                    "original": "Some Blade",
                    "matched": {"brand": "Gillette", "format": "DE"},
                },
            },
            {
                "id": "comment6",
                "author": "user6",
                "razor": {
                    "original": "Straight Razor",
                    "matched": {"brand": "Dovo", "format": "Straight"},
                },
                "blade": {
                    "original": "Some Blade",
                    "matched": {"brand": "Gillette", "format": "DE"},
                },
            },
            {
                "id": "comment7",
                "author": "user7",
                "razor": {
                    "original": "Gillette Tech",
                    "matched": {"brand": "Gillette", "model": "Tech", "format": "DE"},
                },
                "blade": {
                    "original": "Feather Hi-Stainless",
                    # Missing blade format
                    "matched": {"brand": "Feather", "model": "Hi-Stainless"},
                },
            },
        ]
    }


@pytest.fixture
def mock_enriched_data_file(sample_enriched_data, tmp_path):
    """Create a temporary enriched data file."""
    enriched_dir = tmp_path / "data" / "enriched"
    enriched_dir.mkdir(parents=True)

    file_path = enriched_dir / "2025-05.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(sample_enriched_data, f)

    return file_path


def test_format_compatibility_de_with_de_blade_compatible(mock_enriched_data_file):
    """Test that DE razor with DE blade is compatible (no error)."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # DE with DE should not appear in results (compatible)
    de_de_issues = [
        r
        for r in data["results"]
        if r["razor_matched"].get("format") == "DE" and r["blade_matched"].get("format") == "DE"
    ]
    assert len(de_de_issues) == 0


def test_format_compatibility_de_with_ac_blade_incompatible(mock_enriched_data_file):
    """Test that DE razor with AC blade is flagged as incompatible."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # Should find DE with AC incompatibility
    de_ac_issues = [
        r
        for r in data["results"]
        if r["razor_matched"].get("format") == "DE"
        and r["blade_matched"].get("format") == "AC"
        and r["severity"] == "error"
    ]
    assert len(de_ac_issues) == 1
    assert de_ac_issues[0]["issue_type"] == "DE razor incompatible with AC blade"
    assert de_ac_issues[0]["count"] == 1
    assert "comment2" in de_ac_issues[0]["comment_ids"]


def test_format_compatibility_shavette_with_any_blade_compatible(mock_enriched_data_file):
    """Test that Shavette with any blade format is compatible."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # Shavette with AC should not appear in results (compatible)
    shavette_issues = [
        r
        for r in data["results"]
        if "Shavette" in r["razor_matched"].get("format", "")
    ]
    assert len(shavette_issues) == 0


def test_format_compatibility_missing_blade_format_warning(mock_enriched_data_file):
    """Test that missing blade format is flagged as warning."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # Should find missing blade format warning
    missing_format_issues = [
        r
        for r in data["results"]
        if r["severity"] == "warning"
        and "missing" in r["issue_type"].lower()
        and r["razor_matched"].get("format") == "DE"
    ]
    assert len(missing_format_issues) >= 1
    assert any("missing" in issue["issue_type"].lower() for issue in missing_format_issues)


def test_format_compatibility_cartridge_with_blade_warning(mock_enriched_data_file):
    """Test that Cartridge/Disposable razor with blade is flagged as warning."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # Should find Cartridge/Disposable with blade warning
    cartridge_issues = [
        r
        for r in data["results"]
        if r["razor_matched"].get("format") == "Cartridge/Disposable"
        and r["severity"] == "warning"
    ]
    assert len(cartridge_issues) == 1
    assert "Cartridge/Disposable" in cartridge_issues[0]["issue_type"]
    assert cartridge_issues[0]["count"] == 1


def test_format_compatibility_straight_with_blade_warning(mock_enriched_data_file):
    """Test that Straight razor with blade is flagged as warning."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    data = response.json()

    # Should find Straight with blade warning
    straight_issues = [
        r
        for r in data["results"]
        if r["razor_matched"].get("format") == "Straight" and r["severity"] == "warning"
    ]
    assert len(straight_issues) == 1
    assert "Straight" in straight_issues[0]["issue_type"]
    assert straight_issues[0]["count"] == 1


def test_format_compatibility_severity_filter_error(mock_enriched_data_file):
    """Test severity filter for errors only."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=error")

    assert response.status_code == 200
    data = response.json()

    # Should only return errors, no warnings
    assert all(r["severity"] == "error" for r in data["results"])
    assert data["errors"] > 0
    assert data["warnings"] == 0


def test_format_compatibility_severity_filter_warning(mock_enriched_data_file):
    """Test severity filter for warnings only."""
    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", mock_enriched_data_file.parent):
        response = client.get("/api/format-compatibility?months=2025-05&severity=warning")

    assert response.status_code == 200
    data = response.json()

    # Should only return warnings, no errors
    assert all(r["severity"] == "warning" for r in data["results"])
    assert data["warnings"] > 0
    assert data["errors"] == 0


def test_format_compatibility_multiple_months(mock_enriched_data_file):
    """Test analysis with multiple months."""
    # Create second month file
    enriched_dir = mock_enriched_data_file.parent
    file_path2 = enriched_dir / "2025-06.json"
    with file_path2.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "data": [
                    {
                        "id": "comment8",
                        "author": "user8",
                        "razor": {
                            "original": "Gillette Tech",
                            "matched": {"brand": "Gillette", "model": "Tech", "format": "DE"},
                        },
                        "blade": {
                            "original": "Feather GEM",
                            "matched": {"brand": "Feather", "format": "GEM"},
                        },
                    }
                ]
            },
            f,
        )

    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", enriched_dir):
        response = client.get("/api/format-compatibility?months=2025-05,2025-06&severity=all")

    assert response.status_code == 200
    data = response.json()

    assert len(data["months"]) == 2
    assert "2025-05" in data["months"]
    assert "2025-06" in data["months"]


def test_format_compatibility_missing_month_file():
    """Test handling of missing month file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        enriched_dir = Path(tmpdir) / "data" / "enriched"
        enriched_dir.mkdir(parents=True)

        with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", enriched_dir):
            response = client.get("/api/format-compatibility?months=2025-99&severity=all")

        assert response.status_code == 404


def test_format_compatibility_invalid_severity():
    """Test validation of severity parameter."""
    response = client.get("/api/format-compatibility?months=2025-05&severity=invalid")

    assert response.status_code == 400
    assert "severity must be" in response.json()["detail"]


def test_format_compatibility_missing_months():
    """Test validation of months parameter."""
    response = client.get("/api/format-compatibility?severity=all")

    assert response.status_code == 422  # FastAPI validation error


def test_format_compatibility_half_de_with_de_compatible(mock_enriched_data_file):
    """Test that Half DE razor with DE blade is compatible."""
    # Add Half DE test case
    enriched_dir = mock_enriched_data_file.parent
    file_path = enriched_dir / "2025-05.json"
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["data"].append(
        {
            "id": "comment9",
            "author": "user9",
            "razor": {
                "original": "Half DE Razor",
                "matched": {"brand": "Other", "format": "Half DE"},
            },
            "blade": {
                "original": "Feather DE",
                "matched": {"brand": "Feather", "format": "DE"},
            },
        }
    )

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    with patch("webui.api.format_compatibility.ENRICHED_DATA_DIR", enriched_dir):
        response = client.get("/api/format-compatibility?months=2025-05&severity=all")

    assert response.status_code == 200
    result_data = response.json()

    # Half DE with DE should not appear in results (compatible)
    half_de_issues = [
        r
        for r in result_data["results"]
        if r["razor_matched"].get("format") == "Half DE"
        and r["blade_matched"].get("format") == "DE"
    ]
    assert len(half_de_issues) == 0

