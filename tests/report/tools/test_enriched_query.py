"""Tests for the enriched_query CLI tool."""

import json

import pytest

from sotd.report.tools.enriched_query import main


def record(author, created, soap=None, razor=None, blade=None, brush=None):
    """Build one enriched record with only the fields the CLI reads."""
    return {
        "author": author,
        "created_utc": created,
        "soap": soap,
        "razor": razor,
        "blade": blade,
        "brush": brush,
    }


def soap(brand, scent):
    return {"original": "x", "normalized": "x", "matched": {"brand": brand, "scent": scent}}


def razor(brand, model):
    return {"matched": {"brand": brand, "model": model, "format": "DE"}}


@pytest.fixture
def data_dir(tmp_path):
    """One enriched file: a double-shave day, a single-product zealot, an unmatched entry."""
    enriched = tmp_path / "enriched"
    enriched.mkdir()
    doc = {
        "meta": {"month": "2026-07", "record_count": 5},
        "data": [
            {
                "author": "scribe__",
                "created_utc": "2026-07-05T09:00:00Z",
                "soap": soap("Barrister and Mann", "Seville"),
                "razor": razor("Blackland", "Blackbird"),
                "blade": None,
                "brush": None,
            },
            {
                "author": "scribe__",
                "created_utc": "2026-07-05T20:00:00Z",
                "soap": soap("Stirling Soap Co.", "I, Rich Moose"),
                "razor": None,
                "blade": None,
                "brush": None,
            },
            {
                "author": "scribe__",
                "created_utc": "2026-07-11T09:00:00Z",
                "soap": soap("Catie's Bubbles", "Le Petit"),
                "razor": None,
                "blade": None,
                "brush": None,
            },
            {
                "author": "Glass_Procedure7497",
                "created_utc": "2026-07-02T08:00:00Z",
                "soap": soap("Catie's Bubbles", "Tonsorium"),
                "razor": None,
                "blade": None,
                "brush": None,
            },
            {
                "author": "Glass_Procedure7497",
                "created_utc": "2026-07-12T08:00:00Z",
                "soap": soap("Catie's Bubbles", "Tonsorium"),
                "razor": None,
                "blade": None,
                "brush": None,
            },
            {
                "author": "unmatched",
                "created_utc": "2026-07-13T08:00:00Z",
                "soap": {"original": "Mystery Soap", "matched": None},
                "razor": None,
                "blade": None,
                "brush": None,
            },
        ],
    }
    (enriched / "2026-07.json").write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path


def run(capsys, argv):
    """Run the CLI and return (exit_code, stdout, stderr)."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestUser:
    def test_user_rows_and_summary(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "user", "--month", "2026-07", "--name", "scribe__"],
        )
        assert code == 0
        assert out.count("\n") >= 3
        assert "entries: 3, distinct shave dates: 2" in out
        assert "multi-shave dates: 2026-07-05" in out
        assert "Barrister and Mann - Seville" in out
        assert "Blackland Blackbird" in out

    def test_user_json(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "user",
                "--month",
                "2026-07",
                "--name",
                "scribe__",
            ],
        )
        assert code == 0
        result = json.loads(out)
        assert result["total_entries"] == 3
        assert result["distinct_dates"] == 2
        assert result["multi_shave_dates"] == ["2026-07-05"]

    def test_user_product_filter(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "user",
                "--month",
                "2026-07",
                "--name",
                "scribe__",
                "--category",
                "soap",
                "--product",
                "Stirling Soap Co. - I, Rich Moose",
            ],
        )
        assert code == 0
        result = json.loads(out)
        assert result["total_entries"] == 1
        assert result["rows"][0]["date"] == "2026-07-05"

    def test_user_unknown_author(self, data_dir, capsys):
        code, _, err = run(
            capsys, ["--data-dir", str(data_dir), "user", "--month", "2026-07", "--name", "nobody"]
        )
        assert code == 1
        assert "no entries by author" in err

    def test_user_unmatched_renders_dash(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "user", "--month", "2026-07", "--name", "unmatched"],
        )
        assert code == 0
        assert "-" in out


class TestUsage:
    def test_usage_exact(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "usage",
                "--month",
                "2026-07",
                "--category",
                "soap",
                "--name",
                "Catie's Bubbles - Tonsorium",
            ],
        )
        assert code == 0
        assert "total shaves: 2" in out
        assert "Glass_Procedure7497" in out

    def test_usage_by_user(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "usage",
                "--month",
                "2026-07",
                "--category",
                "soap",
                "--name",
                "Catie's Bubbles - Tonsorium",
                "--by-user",
            ],
        )
        assert code == 0
        assert "author" in out and "shaves" in out
        assert "Glass_Procedure7497" in out

    def test_usage_contains_ambiguous(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "usage",
                "--month",
                "2026-07",
                "--category",
                "soap",
                "--name",
                "Catie's Bubbles",
                "--contains",
            ],
        )
        assert code == 1
        assert "ambiguous name" in err
        assert "Le Petit" in err and "Tonsorium" in err

    def test_usage_no_match(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "usage",
                "--month",
                "2026-07",
                "--category",
                "razor",
                "--name",
                "Merkur 37C",
            ],
        )
        assert code == 1
        assert "no razor entries matching" in err

    def test_usage_json(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "usage",
                "--month",
                "2026-07",
                "--category",
                "soap",
                "--name",
                "Catie's Bubbles - Tonsorium",
                "--by-user",
            ],
        )
        assert code == 0
        result = json.loads(out)
        assert result["total_shaves"] == 2
        assert result["rows"] == [{"author": "Glass_Procedure7497", "shaves": 2}]


class TestErrors:
    def test_missing_month(self, tmp_path, capsys):
        (tmp_path / "enriched").mkdir()
        code, _, err = run(
            capsys, ["--data-dir", str(tmp_path), "user", "--month", "2026-01", "--name", "x"]
        )
        assert code == 1
        assert "file not found" in err

    def test_bad_structure(self, tmp_path, capsys):
        (tmp_path / "enriched").mkdir()
        (tmp_path / "enriched" / "2026-07.json").write_text('{"data": {}}', encoding="utf-8")
        code, _, err = run(
            capsys, ["--data-dir", str(tmp_path), "user", "--month", "2026-07", "--name", "x"]
        )
        assert code == 1
        assert "unexpected structure" in err

    def test_unknown_category_rejected(self, data_dir, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "--data-dir",
                    str(data_dir),
                    "usage",
                    "--month",
                    "2026-07",
                    "--category",
                    "wands",
                    "--name",
                    "x",
                ]
            )
        assert excinfo.value.code == 2  # argparse rejects bad choices before main() runs
