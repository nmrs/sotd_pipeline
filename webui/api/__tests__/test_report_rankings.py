#!/usr/bin/env python3
"""Tests for report rankings API endpoints."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.main import app

client = TestClient(app)


def _mock_aggregated_content():
    """Minimal aggregated file content with meta and data (one table with rank/name)."""
    return {
        "meta": {
            "month": "2025-06",
            "total_shaves": 1000,
            "unique_shavers": 50,
        },
        "data": {
            "razors": [
                {"name": "Razor A", "shaves": 100, "unique_users": 10, "rank": 1},
                {"name": "Razor B", "shaves": 80, "unique_users": 8, "rank": 2},
                {"name": "Razor C", "shaves": 60, "unique_users": 6, "rank": 3},
            ],
            "blades": [
                {"name": "Blade X", "shaves": 200, "unique_users": 20, "rank": 1},
            ],
        },
    }


def test_report_rankings_months_empty(tmp_path):
    """GET /api/report-rankings/months returns empty when no aggregated data."""
    with patch("api.report_rankings._get_aggregated_dir", return_value=tmp_path):
        resp = client.get("/api/report-rankings/months")
    assert resp.status_code == 200
    data = resp.json()
    assert "months" in data
    assert data["months"] == []


def test_report_rankings_months_returns_sorted_stems(tmp_path):
    """GET /api/report-rankings/months returns sorted YYYY-MM stems from JSON files."""
    (tmp_path / "2025-07.json").write_text("{}")
    (tmp_path / "2025-06.json").write_text("{}")
    (tmp_path / "2025-08.json").write_text("{}")
    with patch("api.report_rankings._get_aggregated_dir", return_value=tmp_path):
        resp = client.get("/api/report-rankings/months")
    assert resp.status_code == 200
    data = resp.json()
    assert data["months"] == ["2025-06", "2025-07", "2025-08"]


def test_report_rankings_tables_empty_when_no_months(tmp_path):
    """GET /api/report-rankings/tables returns empty when no months available."""
    with patch("api.report_rankings._get_aggregated_dir", return_value=tmp_path):
        resp = client.get("/api/report-rankings/tables")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tables"] == []


def test_report_rankings_tables_from_aggregated_data(tmp_path):
    """GET /api/report-rankings/tables returns table list from one aggregated file."""
    agg_file = tmp_path / "2025-06.json"
    agg_file.write_text(json.dumps(_mock_aggregated_content(), indent=2), encoding="utf-8")

    with patch("api.report_rankings._get_aggregated_dir", return_value=tmp_path):
        with patch("api.report_rankings.load_aggregated_data") as load_mock:
            metadata = {"month": "2025-06", "total_shaves": 1000, "unique_shavers": 50}
            content = _mock_aggregated_content()
            load_mock.return_value = (metadata, content["data"])
            resp = client.get("/api/report-rankings/tables")
    assert resp.status_code == 200
    data = resp.json()
    tables = data["tables"]
    ids = [t["id"] for t in tables]
    assert "razors" in ids
    assert "blades" in ids
    labels = [t["label"] for t in tables]
    assert "Razors" in labels
    assert "Blades" in labels


def test_report_rankings_series_requires_items():
    """GET /api/report-rankings/series returns 400 when items missing."""
    resp = client.get("/api/report-rankings/series", params={"table": "razors", "items": ""})
    assert resp.status_code == 400


def test_report_rankings_series_returns_shape(tmp_path):
    """GET /api/report-rankings/series returns months and series for requested items."""
    agg1 = _mock_aggregated_content()
    agg1["meta"]["month"] = "2025-06"
    (tmp_path / "2025-06.json").write_text(json.dumps(agg1, indent=2), encoding="utf-8")
    agg2 = _mock_aggregated_content()
    agg2["meta"]["month"] = "2025-07"
    agg2["data"]["razors"][0]["rank"] = 2
    agg2["data"]["razors"][1]["rank"] = 1
    (tmp_path / "2025-07.json").write_text(json.dumps(agg2, indent=2), encoding="utf-8")

    def load_side_effect(file_path, debug=False):
        content = json.loads(file_path.read_text(encoding="utf-8"))
        return content["meta"], content["data"]

    return_2025_06 = [
        {"name": "Razor A", "rank": 1, "shaves": 100},
        {"name": "Razor B", "rank": 2, "shaves": 80},
    ]
    return_2025_07 = [
        {"name": "Razor B", "rank": 1, "shaves": 90},
        {"name": "Razor A", "rank": 2, "shaves": 70},
    ]

    with patch("api.report_rankings._get_aggregated_dir", return_value=tmp_path):
        with patch("api.report_rankings.load_aggregated_data", side_effect=load_side_effect):
            with patch("api.report_rankings.TableGenerator") as tg_mock:
                gen = tg_mock.return_value
                gen.get_structured_table_data.side_effect = [return_2025_06, return_2025_07]

                resp = client.get(
                    "/api/report-rankings/series",
                    params={"table": "razors", "items": "Razor A,Razor B"},
                )
    assert resp.status_code == 200
    data = resp.json()
    assert "months" in data
    assert "series" in data
    assert len(data["series"]) == 2
    items = {s["item"]: s["data"] for s in data["series"]}
    assert "Razor A" in items
    assert "Razor B" in items
    assert len(items["Razor A"]) == len(data["months"])
    assert len(items["Razor B"]) == len(data["months"])
