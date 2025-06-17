import os
import json
import subprocess
import tempfile
from pathlib import Path


def test_cli_extracts_shaves_successfully():
    comments = [
        {"id": "1", "body": "* **Razor:** Blackbird"},
        {"id": "2", "body": "* **Blade:** Feather"},
        {"id": "3", "body": "No product listed here"},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        comments_path = Path(tmpdir) / "data/comments/2025-04.json"
        output_path = Path(tmpdir) / "data/extracted/2025-04.json"
        comments_path.parent.mkdir(parents=True)
        with open(comments_path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])

        result = subprocess.run(
            ["python", "-m", "sotd.extract.run", "--month", "2025-04"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        print(result.stderr)

        assert result.returncode == 0
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
            assert "meta" in data
            assert "data" in data
            assert "skipped" in data
            assert data["meta"]["shave_count"] == 2
            assert data["meta"]["skipped_count"] == 1

    with tempfile.TemporaryDirectory() as tmpdir:
        comments_path = Path(tmpdir) / "data/comments/2025-05.json"
        output_path = Path(tmpdir) / "data/extracted/2025-05.json"
        comments_path.parent.mkdir(parents=True)
        with open(comments_path, "w", encoding="utf-8") as f:
            json.dump({"data": comments}, f)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])

        result = subprocess.run(
            ["python", "-m", "sotd.extract.run", "--month", "2025-05"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        print(result.stderr)

        assert result.returncode == 0
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)
            assert "meta" in data
            assert "data" in data
            assert "skipped" in data
            assert data["meta"]["shave_count"] == 2
            assert data["meta"]["skipped_count"] == 1
