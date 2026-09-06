"""Tests for the aggregate_query CLI tool."""

import json

import pytest

from sotd.report.tools.aggregate_query import main


def make_month_file(path, month, razors, soaps, meta_extra=None):
    meta = {"month": month, "total_shaves": 100, "unique_shavers": 5}
    meta.update(meta_extra or {})
    doc = {
        "meta": meta,
        "data": {
            "razors": razors,
            "soaps": soaps,
            "sample_usage_metrics": {"total_samples": 0},
        },
    }
    path.write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    """Three monthly files plus one annual file under a tmp data dir."""
    agg = tmp_path / "aggregated"
    agg.mkdir()
    razor_sets = {
        "2026-01": [
            {"rank": 1, "name": "Blackland Blackbird", "shaves": 90, "unique_users": 4},
            {"rank": 2, "name": "RazoRock Game Changer", "shaves": 6, "unique_users": 2},
        ],
        "2026-02": [
            {"rank": 1, "name": "RazoRock Game Changer", "shaves": 80, "unique_users": 3},
            {"rank": 2, "name": "Blackland Blackbird", "shaves": 15, "unique_users": 3},
        ],
        "2026-03": [
            {"rank": 1, "name": "Blackland Blackbird", "shaves": 70, "unique_users": 4},
            {"rank": 2, "name": "RazoRock Game Changer", "shaves": 9, "unique_users": 2},
        ],
    }
    soaps = [
        {"rank": 1, "name": "Martin de Candre - Fougere", "shaves": 30, "unique_users": 3},
        {"rank": 2, "name": "Barrister and Mann - Seville", "shaves": 4, "unique_users": 2},
    ]
    for month, razors in razor_sets.items():
        make_month_file(agg / f"{month}.json", month, razors, soaps)
    annual = {
        "metadata": {"year": 2025, "total_shaves": 12000},
        "razors": [{"rank": 1, "name": "Blackland Blackbird", "shaves": 900, "unique_users": 30}],
        "sample_usage_metrics": {"total_samples": 0},
    }
    (agg / "annual").mkdir()
    (agg / "annual" / "2025.json").write_text(json.dumps(annual), encoding="utf-8")
    return tmp_path


def run(capsys, argv):
    """Run the CLI and return (exit_code, stdout, stderr)."""
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestMeta:
    def test_meta_month(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "meta", "--month", "2026-02"])
        assert code == 0
        assert "total_shaves" in out
        assert "100" in out
        assert '"2026-02"' in out

    def test_meta_annual(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "meta", "--year", "2025"])
        assert code == 0
        assert "total_shaves" in out
        assert "12000" in out

    def test_meta_missing_file(self, data_dir, capsys):
        code, _, err = run(capsys, ["--data-dir", str(data_dir), "meta", "--month", "2025-01"])
        assert code == 1
        assert "file not found" in err


class TestTop:
    def test_top_default(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "top", "--month", "2026-01", "--category", "razors"],
        )
        assert code == 0
        assert "Blackland Blackbird" in out
        assert "90" in out

    def test_top_n_and_min_shaves(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "top",
                "--month",
                "2026-01",
                "--category",
                "razors",
                "--top",
                "1",
                "--min-shaves",
                "10",
            ],
        )
        assert code == 0
        assert "Blackland Blackbird" in out
        assert "RazoRock" not in out

    def test_top_unknown_category_lists_valid(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            ["--data-dir", str(data_dir), "top", "--month", "2026-01", "--category", "wands"],
        )
        assert code == 1
        assert "unknown category" in err
        assert "razors" in err

    def test_top_non_list_category(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "top",
                "--month",
                "2026-01",
                "--category",
                "sample_usage_metrics",
            ],
        )
        assert code == 1
        assert "not a ranked list" in err

    def test_top_annual(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "top", "--year", "2025", "--category", "razors"]
        )
        assert code == 0
        assert "Blackland Blackbird" in out


class TestHistory:
    def test_history_last_n(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "blackland blackbird",
                "--last",
                "3",
            ],
        )
        assert code == 0
        for period in ("2026-01", "2026-02", "2026-03"):
            assert period in out
        assert "1" in out and "2" in out

    def test_history_absent_rows(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Karve Overlander",
                "--last",
                "2",
            ],
        )
        assert code == 0
        rows = json.loads(out)["rows"]
        assert len(rows) == 2
        for row in rows:
            assert row["rank"] is None
            assert row["shaves"] is None
            assert row["unique_users"] is None

    def test_history_start_end_range(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--start",
                "2026-02",
                "--end",
                "2026-03",
            ],
        )
        assert code == 0
        assert "2026-01" not in out
        assert "2026-02" in out and "2026-03" in out

    def test_history_last_with_end(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--last",
                "2",
                "--end",
                "2026-02",
            ],
        )
        assert code == 0
        assert "2026-03" not in out
        assert "2026-01" in out and "2026-02" in out

    def test_history_contains_ambiguous(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "soaps",
                "--name",
                "-",
                "--contains",
                "--last",
                "1",
            ],
        )
        assert code == 1
        assert "ambiguous name" in err

    def test_history_min_shaves_masks_month(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "RazoRock Game Changer",
                "--last",
                "2",
                "--min-shaves",
                "10",
            ],
        )
        assert code == 0
        rows = json.loads(out)["rows"]
        # --last 2 = 2026-02 (80 shaves, stays) and 2026-03 (9 shaves, masked)
        assert rows[0]["shaves"] == 80
        assert rows[1]["shaves"] is None

    def test_history_year_annual(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--year",
                "2025",
            ],
        )
        assert code == 0
        assert "2025" in out and "900" in out

    def test_history_year_rejects_range(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--year",
                "2025",
                "--last",
                "2",
            ],
        )
        assert code == 1
        assert "cannot be combined" in err

    def test_history_no_mode(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
            ],
        )
        assert code == 1
        assert "needs" in err

    def test_history_last_zero(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--last",
                "0",
            ],
        )
        assert code == 1
        assert "positive integer" in err

    def test_history_skips_missing_month(self, data_dir, capsys):
        (data_dir / "aggregated" / "2026-02.json").unlink()
        code, out, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--start",
                "2026-01",
                "--end",
                "2026-03",
            ],
        )
        assert code == 0
        assert "skipped missing files: 2026-02" in out

    def test_history_json(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--json",
                "--data-dir",
                str(data_dir),
                "history",
                "--category",
                "razors",
                "--name",
                "Blackland Blackbird",
                "--last",
                "1",
            ],
        )
        assert code == 0
        result = json.loads(out)
        assert result["rows"][0]["rank"] == 1
        assert result["rows"][0]["shaves"] == 70
