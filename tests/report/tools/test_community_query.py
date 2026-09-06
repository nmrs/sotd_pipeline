"""Tests for the community_query CLI tool."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sotd.report.tools.community_query import main


def make_community_file(path, month, posts, comments, discovery=None):
    meta = {
        "month": month,
        "extracted_at": "2026-09-06T00:00:00Z",
        "post_count": len(posts),
        "comment_count": len(comments),
        "in_pipeline_post_count": sum(1 for p in posts if p.get("in_pipeline")),
        "discovery": discovery or {"strategies": ["new_listing"], "complete": True},
    }
    doc = {"meta": meta, "data": {"posts": posts, "comments": comments}}
    path.write_text(json.dumps(doc), encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    comm = tmp_path / "community"
    comm.mkdir()
    make_community_file(
        comm / "2026-08.json",
        "2026-08",
        posts=[
            {
                "id": "sotd",
                "title": "Saturday SOTD Thread - Aug 01, 2026",
                "selftext": "",
                "author": "AutoModerator",
                "created_utc": "2026-08-01T06:00:00Z",
                "score": 10,
                "num_comments": 2,
                "flair": "SOTD",
                "url": "u1",
                "locked": False,
                "stickied": True,
                "in_pipeline": True,
            },
            {
                "id": "disc",
                "title": "Lather Games wrap-up",
                "selftext": "the final standings",
                "author": "bigcheese",
                "created_utc": "2026-08-05T10:00:00Z",
                "score": 88,
                "num_comments": 40,
                "flair": "Discussion",
                "url": "u2",
                "locked": False,
                "stickied": False,
                "in_pipeline": False,
            },
            {
                "id": "quiet",
                "title": "Quiet question",
                "selftext": "",
                "author": "newbie",
                "created_utc": "2026-08-10T10:00:00Z",
                "score": 2,
                "num_comments": 1,
                "flair": None,
                "url": "u3",
                "locked": False,
                "stickied": False,
                "in_pipeline": False,
            },
        ],
        comments=[
            {
                "id": "c1",
                "thread_id": "sotd",
                "thread_title": "Saturday SOTD Thread - Aug 01, 2026",
                "parent_id": "t3_sotd",
                "author": "shaver1",
                "created_utc": "2026-08-01T07:00:00Z",
                "body": "great lather",
                "score": 3,
                "is_submitter": False,
            },
            {
                "id": "c4",
                "thread_id": "disc",
                "thread_title": "Lather Games wrap-up",
                "parent_id": "t3_disc",
                "author": "judge1",
                "created_utc": "2026-08-05T11:00:00Z",
                "body": "final verdict posted",
                "score": 5,
                "is_submitter": False,
            },
            {
                "id": "c5",
                "thread_id": "disc",
                "thread_title": "Lather Games wrap-up",
                "parent_id": "t1_c4",
                "author": "bigcheese",
                "created_utc": "2026-08-05T12:00:00Z",
                "body": "thanks judges",
                "score": 2,
                "is_submitter": True,
            },
            {
                "id": "c6",
                "thread_id": "disc",
                "thread_title": "Lather Games wrap-up",
                "parent_id": "t1_c4",
                "author": "rival",
                "created_utc": "2026-08-05T13:00:00Z",
                "body": "rematch next year?",
                "score": 1,
                "is_submitter": False,
            },
            {
                "id": "c2",
                "thread_id": "quiet",
                "thread_title": "Quiet question",
                "parent_id": "t3_quiet",
                "author": "bigcheese",
                "created_utc": "2026-08-10T11:00:00Z",
                "body": "good question",
                "score": 1,
                "is_submitter": False,
            },
            {
                "id": "c3",
                "thread_id": "quiet",
                "thread_title": "Quiet question",
                "parent_id": "t1_c2",
                "author": "newbie",
                "created_utc": "2026-08-10T12:00:00Z",
                "body": "thanks",
                "score": 0,
                "is_submitter": True,
            },
        ],
    )
    return tmp_path


def run(capsys, argv):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestMeta:
    def test_meta(self, data_dir, capsys):
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "meta", "--month", "2026-08"])
        assert code == 0
        assert "post_count" in out

    def test_meta_json(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "--json", "meta", "--month", "2026-08"]
        )
        assert code == 0
        assert '"discovery"' in out

    def test_meta_missing_month_exits_1(self, capsys):
        code, _, err = run(capsys, ["--data-dir", "/nonexistent", "meta", "--month", "2025-01"])
        assert code == 1
        assert "No community file" in err


class TestThreads:
    def test_lists_all_sorted_by_comments_desc(self, data_dir, capsys):
        # counts: disc=3 (c4,c5,c6), quiet=2 (c2,c3), sotd=1 (c1)
        code, out, _ = run(capsys, ["--data-dir", str(data_dir), "threads", "--month", "2026-08"])
        assert code == 0
        assert out.index("disc") < out.index("quiet") < out.index("sotd")

    def test_filter_non_sotd(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "threads", "--month", "2026-08", "--filter", "non-sotd"],
        )
        assert code == 0
        assert "Lather Games wrap-up" in out
        assert "Saturday SOTD Thread" not in out

    def test_filter_sotd(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "threads", "--month", "2026-08", "--filter", "sotd"],
        )
        assert code == 0
        assert "Saturday SOTD Thread" in out
        assert "Lather Games wrap-up" not in out

    def test_min_comments(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "threads", "--month", "2026-08", "--min-comments", "3"],
        )
        assert code == 0
        assert "Lather Games wrap-up" in out
        assert "Quiet question" not in out

    def test_author_filter(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "threads", "--month", "2026-08", "--author", "newbie"],
        )
        assert code == 0
        assert "Quiet question" in out
        assert "Lather Games wrap-up" not in out

    def test_top_limit(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "threads", "--month", "2026-08", "--top", "1"]
        )
        assert code == 0
        assert "Lather Games wrap-up" in out
        assert "Saturday SOTD Thread" not in out

    def test_json_output_hides_internal_comment_key(self, data_dir, capsys):
        code, out, _ = run(
            capsys, ["--data-dir", str(data_dir), "--json", "threads", "--month", "2026-08"]
        )
        assert code == 0
        rows = json.loads(out)
        assert rows
        assert all("_comments" not in r for r in rows)

    def test_missing_month_exits_1(self, capsys):
        code, _, err = run(capsys, ["--data-dir", "/nonexistent", "threads", "--month", "2025-01"])
        assert code == 1


class TestThread:
    def test_renders_tree_indented(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "thread", "--month", "2026-08", "--id", "quiet"],
        )
        assert code == 0
        assert "Quiet question" in out
        lines = out.splitlines()
        c2_line = next(line for line in lines if "[c2]" in line)
        c3_line = next(line for line in lines if "[c3]" in line)
        assert lines.index(c3_line) > lines.index(c2_line)
        assert c3_line.startswith("  ") and not c2_line.startswith(" ")
        assert "(OP)" in c3_line  # c3 has is_submitter=True

    def test_accepts_t3_prefix(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            ["--data-dir", str(data_dir), "thread", "--month", "2026-08", "--id", "t3_quiet"],
        )
        assert code == 0

    def test_unknown_id_exits_1(self, data_dir, capsys):
        code, _, err = run(
            capsys, ["--data-dir", str(data_dir), "thread", "--month", "2026-08", "--id", "nope"]
        )
        assert code == 1
        assert "Unknown thread" in err

    def test_max_comments_caps_render(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "thread",
                "--month",
                "2026-08",
                "--id",
                "quiet",
                "--max-comments",
                "1",
            ],
        )
        assert code == 0
        assert "[c3]" not in out
        assert "not shown" in out

    def test_json_output(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "--json",
                "thread",
                "--month",
                "2026-08",
                "--id",
                "quiet",
            ],
        )
        assert code == 0
        doc = json.loads(out)
        assert doc["post"]["id"] == "quiet"
        assert len(doc["comments"]) == 2

    def test_json_output_caps_comments_and_marks_truncated(self, data_dir, capsys):
        # disc has 3 comments; cap to 1 and expect the truncated marker
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "--json",
                "thread",
                "--month",
                "2026-08",
                "--id",
                "disc",
                "--max-comments",
                "1",
            ],
        )
        assert code == 0
        doc = json.loads(out)
        assert [c["id"] for c in doc["comments"]] == ["c4"]
        assert doc["truncated"] is True


class TestSearch:
    def test_finds_post_and_comment_across_window(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "question",
            ],
        )
        assert code == 0
        assert "[post]" in out and "[comment]" in out

    def test_author_filter(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "verdict",
                "--author",
                "judge1",
            ],
        )
        assert code == 0
        assert "[comment]" in out
        assert "[post]" not in out  # the disc post is authored by bigcheese

    def test_no_hits_reports(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "zzznotfound",
            ],
        )
        assert code == 0
        assert "No matches" in out

    def test_skips_missing_months_with_note(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-07:2026-08",
                "--query",
                "question",
            ],
        )
        assert code == 0
        assert "no community file" in out.lower()

    def test_window_start_after_end_exits_1(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-07",
                "--query",
                "x",
            ],
        )
        assert code == 1

    def test_comment_hit_shows_thread_title(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "verdict",
            ],
        )
        assert code == 0
        assert "[comment]" in out
        assert "thread: Lather Games wrap-up" in out

    def test_json_hits_carry_titles(self, data_dir, capsys):
        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "--json",
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "verdict",
            ],
        )
        assert code == 0
        doc = json.loads(out)
        comment_hits = [m for m in doc["matches"] if m["kind"] == "comment"]
        assert comment_hits
        assert comment_hits[0]["thread_title"] == "Lather Games wrap-up"

        code, out, _ = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "--json",
                "search",
                "--months",
                "2026-08:2026-08",
                "--query",
                "quiet question",
            ],
        )
        assert code == 0
        doc = json.loads(out)
        post_hits = [m for m in doc["matches"] if m["kind"] == "post"]
        assert post_hits
        assert post_hits[0]["title"] == "Quiet question"

    def test_months_without_colon_exits_1(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08",
                "--query",
                "x",
            ],
        )
        assert code == 1
        assert "YYYY-MM:YYYY-MM" in err

    def test_months_with_extra_colons_exits_1(self, data_dir, capsys):
        code, _, err = run(
            capsys,
            [
                "--data-dir",
                str(data_dir),
                "search",
                "--months",
                "2026-08:2026-08:2026-08",
                "--query",
                "x",
            ],
        )
        assert code == 1
        assert "YYYY-MM:YYYY-MM" in err


class TestMonthIter:
    def test_december_rolls_over_into_next_year(self):
        from sotd.report.tools.community_query import month_iter

        assert month_iter("2026-12", "2027-01") == ["2026-12", "2027-01"]


class TestModuleEntrypoint:
    def test_python_m_invocation_exits_1_on_missing_month(self, tmp_path):
        """Pins the documented `python -m sotd.report.tools.community_query` invocation."""
        repo_root = Path(__file__).resolve().parents[3]
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sotd.report.tools.community_query",
                "--data-dir",
                str(tmp_path),
                "meta",
                "--month",
                "2099-01",
            ],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert proc.returncode == 1
        assert "No community file" in proc.stderr
