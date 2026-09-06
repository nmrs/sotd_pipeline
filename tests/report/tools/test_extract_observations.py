"""Tests for the extract_observations CLI tool."""

import json

import pytest

from sotd.report.tools.extract_observations import main


def write_archive(path, month, report_type, observations, with_heading=True):
    body = (
        "# Report\n\n## Observations\n\n"
        + "\n".join(observations)
        + "\n\n## Notes & Caveats\n\n* note\n"
    )
    if not with_heading:
        body = "# Report\n\n## Notes & Caveats\n\n* note\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    """Archive files for three months, both types, plus edge-case files."""
    archive = tmp_path / "report_archive"
    write_archive(
        archive / "2026-01-hardware.md",
        "2026-01",
        "hardware",
        ["* Blackbird takes January.", "* GEMs tussle with straights."],
    )
    write_archive(
        archive / "2026-01-software.md", "2026-01", "software", ["* B&M opens the year on top."]
    )
    # placeholder-era file, exactly as the pipeline emits it before drafting
    (archive / "2026-02-hardware.md").write_text(
        "# Report\n\n## Observations\n\n* [Observations will be generated based on data analysis]"
        "\n\n## Notes & Caveats\n\n* note\n",
        encoding="utf-8",
    )
    write_archive(
        archive / "2026-02-software.md", "2026-02", "software", ["* Stirling fights back."]
    )
    write_archive(
        archive / "2026-03-hardware.md", "2026-03", "hardware", ["* Blackbird bounces back."]
    )
    write_archive(
        archive / "2026-03-software.md",
        "2026-03",
        "software",
        ["* A link: [brain bowl](https://x.example/1)"],
        with_heading=False,
    )
    (archive / "annual").mkdir()
    (archive / "annual" / "2025-hardware.md").write_text(
        "## Observations\n\n* annual\n", encoding="utf-8"
    )
    return tmp_path


def run(capsys, argv):
    """Run the CLI and return (exit_code, stdout, stderr)."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestExtraction:
    def test_all_months_both_types(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir)])
        assert code == 0
        assert "== 2026-01 — hardware ==" in out
        assert "== 2026-01 — software ==" in out
        assert "* Blackbird takes January." in out
        assert "Notes & Caveats" not in out  # tables and caveats stay out

    def test_stops_at_next_heading(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "--type", "hardware"])
        assert code == 0
        assert "* note" not in out

    def test_type_filter(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "--type", "software"])
        assert code == 0
        assert "hardware" not in out
        assert "* Stirling fights back." in out

    def test_last_two_months(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "--last", "2"])
        assert code == 0
        assert "2026-01" not in out
        assert "2026-02" in out and "2026-03" in out

    def test_months_range(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "--months", "2026-01:2026-02", "--type", "hardware"],
        )
        assert code == 0
        assert "2026-03" not in out
        assert "2026-01" in out and "2026-02" in out

    def test_months_list(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "--months", "2026-03", "--type", "software"]
        )
        assert code == 0
        assert "2026-01" not in out

    def test_months_with_missing_month(self, data_dir, capsys):
        code, _, err = run(capsys, ["--data-dir", str(data_dir), "--months", "2026-01,2025-09"])
        assert code == 1
        assert "no archive files for months: 2025-09" in err

    def test_last_zero(self, data_dir, capsys):
        code, _, err = run(capsys, ["--data-dir", str(data_dir), "--last", "0"])
        assert code == 1
        assert "positive integer" in err

    def test_file_without_section_skipped_with_warning(self, data_dir, capsys):
        code, out, err = run(capsys, ["--data-dir", str(data_dir), "--months", "2026-03"])
        assert code == 0
        assert "2026-03 — software" not in out
        assert "no Observations section in 2026-03-software.md" in err

    def test_placeholder_content_passes_through(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "--type", "hardware", "--months", "2026-02"]
        )
        assert code == 0
        assert "[Observations will be generated based on data analysis]" in out

    def test_annual_subdir_ignored(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir)])
        assert code == 0
        assert "annual" not in out

    def test_json_mode(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--json", "--data-dir", str(data_dir), "--type", "software"])
        assert code == 0
        blocks = json.loads(out)
        assert blocks[0]["month"] == "2026-01"
        assert blocks[0]["type"] == "software"
        assert blocks[0]["observations"] == ["* B&M opens the year on top."]

    def test_empty_archive(self, tmp_path, capsys):
        (tmp_path / "report_archive").mkdir()
        code, out, err = run(capsys, ["--data-dir", str(tmp_path)])
        assert code == 0
        assert out == ""
        assert "no Observations sections found" in err

    def test_missing_archive_dir(self, tmp_path, capsys):
        code, _, err = run(capsys, ["--data-dir", str(tmp_path)])
        assert code == 1
        assert "archive directory not found" in err


class TestEndBound:
    def test_last_with_end_bounds_selection(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "--last", "2", "--end", "2026-02"])
        assert code == 0
        assert "2026-01" in out and "2026-02" in out
        assert "2026-03" not in out

    def test_end_bounds_default_history(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "--end", "2026-01"])
        assert code == 0
        assert "2026-01" in out
        assert "2026-02" not in out and "2026-03" not in out

    def test_end_rejected_with_months(self, data_dir, capsys):
        code, _, err = run(
            capsys, ["--data-dir", str(data_dir), "--months", "2026-01", "--end", "2026-02"]
        )
        assert code == 1
        assert "--end cannot be combined with --months" in err

    def test_end_before_all_months_empty(self, data_dir, capsys):
        code, out, err = run(
            capsys, ["--data-dir", str(data_dir), "--last", "2", "--end", "2025-12"]
        )
        assert code == 0
        assert out == ""
        assert "no Observations sections found" in err

    def test_end_invalid_format(self, data_dir, capsys):
        code, _, err = run(capsys, ["--data-dir", str(data_dir), "--end", "2026-1"])
        assert code == 1
        assert "invalid month" in err
