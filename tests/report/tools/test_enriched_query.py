"""Tests for the enriched_query CLI tool."""

import json
import re

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


class TestSchema:
    def test_schema_shows_record_count_and_top_keys(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "schema", "--month", "2026-07"])
        assert code == 0
        assert "records=6" in out
        assert "author" in out
        assert "created_utc" in out

    def test_schema_shows_category_subobject_shapes(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "schema", "--month", "2026-07"])
        assert code == 0
        assert "razor" in out
        assert "matched" in out
        assert "brand" in out
        assert "scent" in out  # from soap matched keys

    def test_schema_notes_absent_categories(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "schema", "--month", "2026-07"])
        assert code == 0
        # fixture has no brush dicts — count line should read present=0
        assert re.search(r"brush\b.*present=0", out)

    def test_json_output(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--json", "--data-dir", str(data_dir), "schema", "--month", "2026-07"]
        )
        assert code == 0
        doc = json.loads(out)
        assert doc["record_count"] == 6
        assert "author" in doc["record_keys"]
        assert doc["categories"]["razor"]["present"] >= 1
        assert "brand" in doc["categories"]["razor"]["matched_keys"]

    def test_missing_month_exits_1(self, tmp_path, capsys):
        code, _, err = run(capsys, ["--data-dir", str(tmp_path), "schema", "--month", "2025-01"])
        assert code == 1
        assert "file not found" in err


@pytest.fixture
def timeline_dir(tmp_path):
    """Three months of Tonsorium usage: May adopter, June carryover, July newcomers."""
    enriched = tmp_path / "enriched"
    enriched.mkdir()
    tonso = soap("Catie's Bubbles", "Tonsorium")
    months = {
        "2026-05": [
            record("Glass_Procedure7497", "2026-05-02T08:00:00Z", soap=tonso),
        ],
        "2026-06": [
            record("Glass_Procedure7497", "2026-06-02T08:00:00Z", soap=tonso),
            record(
                "scribe__", "2026-06-03T08:00:00Z", soap=soap("Stirling Soap Co.", "I, Rich Moose")
            ),
        ],
        "2026-07": [
            record("Glass_Procedure7497", "2026-07-02T08:00:00Z", soap=tonso),
            record("Glass_Procedure7497", "2026-07-12T08:00:00Z", soap=tonso),
            record("tsrblke", "2026-07-04T08:00:00Z", soap=tonso),
            record("scribe__", "2026-07-04T20:00:00Z", soap=tonso),
        ],
    }
    for month, recs in months.items():
        (enriched / f"{month}.json").write_text(
            json.dumps({"meta": {"month": month}, "data": recs}), encoding="utf-8"
        )
    return tmp_path


TIMELINE_BASE = [
    "--data-dir",
    "{data_dir}",
    "timeline",
    "--months",
    "2026-06:2026-07",
    "--category",
    "soap",
    "--name",
    "Catie's Bubbles - Tonsorium",
]


class TestTimeline:
    def _argv(self, timeline_dir, *extra):
        base = [arg.format(data_dir=str(timeline_dir)) for arg in TIMELINE_BASE]
        args = base + list(extra)
        if "--json" in args:  # global flags precede the subcommand
            args.remove("--json")
            args.insert(args.index("timeline"), "--json")
        return args

    def test_json_month_rows_carry_new_returning_split(self, timeline_dir, capsys):
        code, out, _ = run(capsys, self._argv(timeline_dir, "--json"))
        assert code == 0
        result = json.loads(out)
        assert result["name"] == "Catie's Bubbles - Tonsorium"
        assert result["baseline"]["prior_users"] == 1  # May's Glass_Procedure7497
        assert result["months"] == [
            {
                "month": "2026-06",
                "shaves": 1,
                "unique_users": 1,
                "new_users": 0,
                "returning_users": 1,
            },
            {
                "month": "2026-07",
                "shaves": 4,
                "unique_users": 3,
                "new_users": 2,
                "returning_users": 1,
            },
        ]

    def test_by_user_rows_carry_first_last_and_status(self, timeline_dir, capsys):
        code, out, _ = run(capsys, self._argv(timeline_dir, "--json", "--by-user"))
        assert code == 0
        rows = json.loads(out)["users"]
        by_author = {row["author"]: row for row in rows}
        assert by_author["Glass_Procedure7497"]["status"] == "returning"
        assert by_author["Glass_Procedure7497"]["first"] == "2026-05-02"
        assert by_author["Glass_Procedure7497"]["shaves"] == 4
        assert by_author["tsrblke"]["status"] == "new"
        assert by_author["tsrblke"]["first"] == "2026-07-04"
        assert by_author["tsrblke"]["last"] == "2026-07-04"

    def test_by_day_counts_per_date(self, timeline_dir, capsys):
        code, out, _ = run(capsys, self._argv(timeline_dir, "--json", "--by-day"))
        assert code == 0
        days = {row["date"]: row for row in json.loads(out)["by_day"]}
        assert days["2026-07-04"]["shaves"] == 2
        assert days["2026-07-04"]["users"] == 2
        assert days["2026-07-02"]["shaves"] == 1
        assert "2026-05-02" not in days  # outside the window

    def test_text_render_includes_month_table_and_baseline(self, timeline_dir, capsys):
        code, out, _ = run(capsys, self._argv(timeline_dir))
        assert code == 0
        assert "2026-06:2026-07" in out
        assert "prior user" in out
        lines = [" ".join(line.split()) for line in out.splitlines()]
        assert "2026-06 1 1 0 1" in lines
        assert "2026-07 4 3 2 1" in lines

    def test_single_month_window_allowed(self, timeline_dir, capsys):
        argv = [arg.format(data_dir=str(timeline_dir)) for arg in TIMELINE_BASE]
        argv[argv.index("--months") + 1] = "2026-07:2026-07"
        argv.insert(argv.index("timeline"), "--json")
        code, out, _ = run(capsys, argv)
        assert code == 0
        months = json.loads(out)["months"]
        assert [m["month"] for m in months] == ["2026-07"]
        assert months[0]["new_users"] == 2 and months[0]["returning_users"] == 1

    def test_no_matches_exits_1(self, timeline_dir, capsys):
        code, _, err = run(capsys, self._argv(timeline_dir, "--name", "Martin de Candre - Fougere"))
        assert code == 1
        assert "no soap entries matching" in err

    def test_months_without_colon_exits_1(self, timeline_dir, capsys):
        code, _, err = run(capsys, self._argv(timeline_dir, "--months", "2026-07"))
        assert code == 1
        assert "Window must be" in err

    def test_window_start_after_end_exits_1(self, timeline_dir, capsys):
        code, _, err = run(capsys, self._argv(timeline_dir, "--months", "2026-07:2026-06"))
        assert code == 1
        assert "after" in err

    def test_missing_month_in_window_is_skipped_with_note(self, timeline_dir, capsys):
        code, out, _ = run(
            capsys, self._argv(timeline_dir, "--months", "2026-04:2026-05", "--json")
        )
        assert code == 0
        result = json.loads(out)
        assert result["skipped"] == ["2026-04"]
        assert [m["month"] for m in result["months"]] == ["2026-05"]
