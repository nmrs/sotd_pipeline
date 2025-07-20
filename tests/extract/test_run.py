import json
import tempfile
from pathlib import Path
from sotd.extract.run import run_extraction_for_month


def test_run_extraction_for_month_valid(monkeypatch):
    comments = [
        {"id": "1", "body": "* **Razor:** Blackbird"},
        {"id": "2", "body": "* **Blade:** Feather"},
        {"id": "3", "body": "No product listed here"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None

        assert result["meta"]["shave_count"] == 2
        assert result["meta"]["skipped_count"] == 1
        assert result["meta"]["comment_count"] == 3
        assert result["meta"]["field_coverage"]["razor"] == 1
        assert result["meta"]["field_coverage"]["blade"] == 1
        assert len(result["data"]) == 2
        assert len(result["skipped"]) == 1

        # Check that extracted data has structured format
        razor_data = result["data"][0]
        blade_data = result["data"][1]

        assert "razor" in razor_data
        assert razor_data["razor"]["original"] == "Blackbird"
        assert razor_data["razor"]["normalized"] == "Blackbird"

        assert "blade" in blade_data
        assert blade_data["blade"]["original"] == "Feather"
        assert blade_data["blade"]["normalized"] == "Feather"


def test_run_extraction_for_month_file_not_found():
    result = run_extraction_for_month("1900-01")
    assert result is None


def test_run_extraction_for_month_with_normalization(monkeypatch):
    """Test that normalization works correctly during extraction."""
    comments = [
        {"id": "1", "body": "* **Razor:** Blackbird $DOORKNOB"},
        {"id": "2", "body": "* **Blade:** Feather (3x)"},
        {"id": "3", "body": "* **Soap:** Tabac (sample)"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "data/comments/2025-04.json"
        path.parent.mkdir(parents=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f, ensure_ascii=False)

        monkeypatch.chdir(tmpdir)
        result = run_extraction_for_month("2025-04")

        assert result is not None
        assert len(result["data"]) == 3

        # Check normalization results
        razor_data = result["data"][0]
        blade_data = result["data"][1]
        soap_data = result["data"][2]

        # Razor: competition tags should be stripped
        assert razor_data["razor"]["original"] == "Blackbird $DOORKNOB"
        assert razor_data["razor"]["normalized"] == "Blackbird"

        # Blade: usage count should be stripped
        assert blade_data["blade"]["original"] == "Feather (3x)"
        assert blade_data["blade"]["normalized"] == "Feather"

        # Soap: sample marker should be stripped
        assert soap_data["soap"]["original"] == "Tabac (sample)"
        assert soap_data["soap"]["normalized"] == "Tabac"
