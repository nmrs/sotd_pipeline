"""Producer→consumer seam test for the community sidecar.

Exercises the real producer (sotd.fetch.community record builders + file
writer) against the real consumer (sotd.report.tools.community_query) through
a data/community/YYYY-MM.json file, using production praw shapes (bare comment
ids, ``t3_<id>``/``t1_<id>`` parent_id values). If either side changes shape,
this test fails: threads must list the record, thread must render the nested
reply via the parent_id walk, and search must surface the thread title on a
comment hit.
"""

from datetime import datetime, timezone

from sotd.fetch.community import (
    build_comment_record,
    build_post_record,
    write_community_file,
)
from sotd.report.tools.community_query import main


def ts(*parts: int) -> float:
    """Epoch seconds for a UTC datetime given as (year, month, day[, h, m, s])."""
    return datetime(*parts, tzinfo=timezone.utc).timestamp()


class FakeSub:
    """Duck-typed praw Submission with every field build_post_record reads."""

    def __init__(
        self,
        _id,
        title,
        created_utc,
        *,
        selftext="",
        author="tester",
        score=5,
        num_comments=0,
        flair=None,
        permalink="/p",
        locked=False,
        stickied=False,
    ):
        self.id = _id
        self.title = title
        self.created_utc = created_utc
        self.selftext = selftext
        self.author = author
        self.score = score
        self.num_comments = num_comments
        self.link_flair_text = flair
        self.permalink = permalink
        self.locked = locked
        self.stickied = stickied


class FakeComment:
    """Duck-typed praw Comment: bare id plus t3_/t1_-prefixed parent_id."""

    def __init__(
        self, _id, body, created_utc, *, parent_id, author="u1", score=1, is_submitter=False
    ):
        self.id = _id
        self.body = body
        self.created_utc = created_utc
        self.parent_id = parent_id
        self.author = author
        self.score = score
        self.is_submitter = is_submitter


def run_cli(capsys, argv):
    code = main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


class TestProducerConsumerSeam:
    def test_written_records_answer_queries(self, tmp_path, capsys):
        # --- producer side: real builders + writer, production praw shapes ---
        thread = FakeSub(
            "sotdx",
            "SOTD Thread - Aug 01, 2026",
            ts(2026, 8, 1, 6),
            author="AutoModerator",
            num_comments=2,
        )
        top = FakeComment("c1", "great lather today", ts(2026, 8, 1, 7), parent_id="t3_sotdx")
        reply = FakeComment("c2", "same here", ts(2026, 8, 1, 8), parent_id="t1_c1", author="u2")

        posts = [build_post_record(thread, in_pipeline=True)]
        comments = [
            build_comment_record(top, thread.id, thread.title),
            build_comment_record(reply, thread.id, thread.title),
        ]
        meta = {
            "month": "2026-08",
            "extracted_at": "2026-09-06T00:00:00Z",
            "post_count": len(posts),
            "comment_count": len(comments),
            "in_pipeline_post_count": 1,
            "discovery": {
                "strategies": ["new_listing"],
                "complete": True,
                "per_strategy": {"new_listing": 1},
            },
        }
        write_community_file(tmp_path / "community" / "2026-08.json", meta, posts, comments)

        base = ["--data-dir", str(tmp_path)]

        # --- consumer side: real CLI ---
        # threads lists the fetched thread (SOTD flag derived from in_pipeline)
        code, out, _ = run_cli(capsys, base + ["threads", "--month", "2026-08"])
        assert code == 0
        assert "sotdx" in out
        assert "SOTD Thread - Aug 01, 2026" in out

        # thread renders the nested reply: parent_id t1_<id> must key onto the
        # parent comment's bare id, seeded from t3_<thread id>
        code, out, _ = run_cli(capsys, base + ["thread", "--month", "2026-08", "--id", "sotdx"])
        assert code == 0
        assert "[c1]" in out and "[c2]" in out
        lines = out.splitlines()
        c1_line = next(line for line in lines if "[c1]" in line)
        c2_line = next(line for line in lines if "[c2]" in line)
        assert lines.index(c2_line) > lines.index(c1_line)
        assert c2_line.startswith("  ")  # nested under c1

        # search surfaces the comment hit with the thread title
        code, out, _ = run_cli(
            capsys, base + ["search", "--months", "2026-08:2026-08", "--query", "lather"]
        )
        assert code == 0
        assert "[comment]" in out
        assert "t3_sotdx" in out and "t1_c1" in out
        assert "thread: SOTD Thread - Aug 01, 2026" in out
