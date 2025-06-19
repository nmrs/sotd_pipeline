"""Tests for the enrich phase CLI and main functionality."""

import json
from pathlib import Path
from unittest.mock import patch
import argparse

import pytest

from sotd.enrich.enrich import enrich_comments, setup_enrichers
from sotd.enrich.run import _process_month, main, run


def test_setup_enrichers():
    """Test that all enrichers are properly registered."""
    setup_enrichers()
    # This should not raise any exceptions


def test_enrich_comments_basic():
    """Test basic enrichment functionality."""
    comments = [
        {
            "comment_id": "test1",
            "blade": {"matched": {"brand": "Feather", "model": "Hi-Stainless"}},
            "razor": {"matched": {"brand": "RazoRock", "model": "Game Changer"}},
            "blade_extracted": "Feather blade (3rd use)",
            "razor_extracted": "RazoRock Game Changer .84",
        }
    ]
    original_comments = ["Feather blade (3rd use), RazoRock Game Changer .84"]

    enriched = enrich_comments(comments, original_comments)

    assert len(enriched) == 1
    # Check for unified structure: enriched data under product fields
    assert "enriched" in enriched[0]["blade"]
    # Should have blade enrichment (use count)
    assert "use_count" in enriched[0]["blade"]["enriched"]


def test_process_month_missing_file(tmp_path):
    """Test processing a month with missing input file."""
    base_path = Path(tmp_path)
    result = _process_month(2025, 1, base_path, debug=True, force=False)
    assert result is None


def test_process_month_invalid_json(tmp_path):
    """Test processing a month with invalid JSON."""
    base_path = Path(tmp_path)
    matched_dir = base_path / "matched"
    matched_dir.mkdir(parents=True)

    # Create invalid JSON file
    invalid_file = matched_dir / "2025-01.json"
    invalid_file.write_text("invalid json")

    result = _process_month(2025, 1, base_path, debug=True, force=False)
    assert result is None


def test_process_month_valid_data(tmp_path):
    """Test processing a month with valid data."""
    base_path = Path(tmp_path)
    matched_dir = base_path / "matched"
    matched_dir.mkdir(parents=True)

    # Create valid matched data
    matched_data = {
        "meta": {"month": "2025-01"},
        "data": [
            {
                "comment_id": "test1",
                "blade": {"matched": {"brand": "Feather", "model": "Hi-Stainless"}},
                "razor": {"matched": {"brand": "RazoRock", "model": "Game Changer"}},
                "blade_extracted": "Feather blade (3rd use)",
                "razor_extracted": "RazoRock Game Changer .84",
            }
        ],
    }

    matched_file = matched_dir / "2025-01.json"
    with matched_file.open("w") as f:
        json.dump(matched_data, f)

    result = _process_month(2025, 1, base_path, debug=True, force=False)

    assert result is not None
    assert result["month"] == "2025-01"
    assert result["records_processed"] == 1

    # Check that output file was created
    enriched_file = base_path / "enriched" / "2025-01.json"
    assert enriched_file.exists()


def test_main_cli_help():
    """Test that the CLI help works."""
    with patch("sys.argv", ["test", "--help"]):
        with pytest.raises(SystemExit):
            main()


def test_run_with_no_months():
    """Test running with no valid months."""
    with patch("sotd.enrich.run.month_span") as mock_span:
        mock_span.return_value = []

        args = argparse.Namespace(out_dir="data", debug=True, force=False)

        # Should not raise any exceptions
        run(args)
