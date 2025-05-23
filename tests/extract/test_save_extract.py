import json
import tempfile
from pathlib import Path
from sotd.extract.run import save_extraction_result


def test_save_extraction_result_writes_file_correctly(monkeypatch):
    result = {
        "meta": {"month": "2025-04", "comment_count": 1},
        "data": [
            {"id": "abc123", "body": "* **Razor:** Blackbird", "extracted": {"razor": "Blackbird"}}
        ],
        "skipped": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "data/extracted"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "2025-04.json"

        save_extraction_result("2025-04", result, base_path=str(out_dir))

        with open(out_file, "r") as f:
            loaded = json.load(f)
            assert loaded == result
