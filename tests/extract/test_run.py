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
        with open(path, "w") as f:
            json.dump({"data": comments}, f)

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


def test_run_extraction_for_month_file_not_found():
    result = run_extraction_for_month("1900-01")
    assert result is None
