import json
import tempfile
from pathlib import Path
from sotd.match.tools.legacy.analyze_unmatched import main
from io import StringIO
import sys


def test_analyze_unmatched_razors_outputs_expected_counts(tmp_path):
    out_dir = tmp_path / "data" / "matched"
    out_dir.mkdir(parents=True)

    file1 = out_dir / "2025-04.json"
    file2 = out_dir / "2025-05.json"

    data1 = {
        "data": [
            {"razor": "Fancy Razor"},
            {"razor": {"original": "Another Razor", "matched": None}},
            {"razor": {"original": "Fancy Razor"}},
        ]
    }

    data2 = {
        "data": [
            {"razor": "Fancy Razor"},
            {"razor": {"original": "Another Razor"}},
            {"razor": {"original": "New Razor"}},
        ]
    }

    file1.write_text(json.dumps(data1))
    file2.write_text(json.dumps(data2))

    output = StringIO()
    sys_stdout = sys.stdout
    try:
        sys.stdout = output
        main(
            [
                "--range",
                "2025-04:2025-05",
                "--out-dir",
                str(tmp_path / "data"),
            ]
        )
    finally:
        sys.stdout = sys_stdout

    result_stdout = output.getvalue()

    print("\nSTDOUT:\n", result_stdout)

    assert "Fancy Razor" in result_stdout
    assert "Another Razor" in result_stdout
    assert "New Razor" in result_stdout
    assert "3 uses" in result_stdout or "(3 uses)" in result_stdout
    assert "2 uses" in result_stdout or "(2 uses)" in result_stdout
