"""Tests for the community context fetch module."""

import json
import logging
from datetime import datetime, timezone

from sotd.fetch import community
from sotd.fetch.save import write_month_file


def ts(*parts: int) -> int:
    """Epoch seconds for a UTC datetime given as (year, month, day[, h, m, s])."""
    return int(datetime(*parts, tzinfo=timezone.utc).timestamp())


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
    def __init__(
        self, _id, body, created_utc, *, parent_id="t3_t1", author="u1", score=1, is_submitter=False
    ):
        self.id = _id
        self.body = body
        self.created_utc = created_utc
        self.parent_id = parent_id
        self.author = author
        self.score = score
        self.is_submitter = is_submitter


class TestBuildPostRecord:
    def test_full_record(self):
        sub = FakeSub(
            "abc123",
            "Hello",
            ts(2026, 9, 1, 6, 0, 9),
            selftext="body text",
            author="someone",
            score=12,
            num_comments=3,
            flair="Discussion",
            permalink="/r/wetshaving/comments/abc123/x/",
        )
        rec = community.build_post_record(sub, in_pipeline=False)
        assert rec == {
            "id": "abc123",
            "title": "Hello",
            "selftext": "body text",
            "author": "someone",
            "created_utc": "2026-09-01T06:00:09Z",
            "score": 12,
            "num_comments": 3,
            "flair": "Discussion",
            "url": "https://www.reddit.com/r/wetshaving/comments/abc123/x/",
            "locked": False,
            "stickied": False,
            "in_pipeline": False,
        }

    def test_deleted_author_and_no_flag_when_unknown(self):
        sub = FakeSub("abc", "T", ts(2026, 9, 1), author=None)
        rec = community.build_post_record(sub, in_pipeline=None)
        assert rec["author"] == "[deleted]"
        assert "in_pipeline" not in rec


class TestBuildCommentRecord:
    def test_full_record(self):
        c = FakeComment(
            "c1",
            "nice shave",
            ts(2026, 9, 2),
            parent_id="t3_abc",
            author="bob",
            score=2,
            is_submitter=True,
        )
        rec = community.build_comment_record(c, "abc", "Thread Title")
        assert rec == {
            "id": "c1",
            "thread_id": "abc",
            "thread_title": "Thread Title",
            "parent_id": "t3_abc",
            "author": "bob",
            "created_utc": "2026-09-02T00:00:00Z",
            "body": "nice shave",
            "score": 2,
            "is_submitter": True,
        }

    def test_deleted_comment_author(self):
        c = FakeComment("c2", "[removed]", ts(2026, 9, 2), author=None)
        assert community.build_comment_record(c, "abc", "T")["author"] == "[deleted]"


class TestCommunityFileRoundTrip:
    def test_write_then_load(self, tmp_path):
        path = tmp_path / "2026-09.json"
        meta = {"month": "2026-09", "post_count": 1, "comment_count": 1}
        posts = [{"id": "abc", "created_utc": "2026-09-01T00:00:00Z"}]
        comments = [{"id": "c1", "created_utc": "2026-09-01T00:00:01Z"}]
        community.write_community_file(path, meta, posts, comments)
        loaded = community.load_community_file(path)
        assert loaded is not None
        assert loaded[0]["month"] == "2026-09"
        assert loaded[1] == {"posts": posts, "comments": comments}
        # on-disk shape is {"meta": ..., "data": {"posts": [...], "comments": [...]}}
        raw = json.loads(path.read_text())
        assert set(raw["data"].keys()) == {"posts", "comments"}

    def test_load_missing_returns_none(self, tmp_path):
        assert community.load_community_file(tmp_path / "nope.json") is None


class TestLoadSotdIds:
    def test_ids_from_threads_file(self, tmp_path):
        write_month_file(
            tmp_path / "threads" / "2026-08.json",
            {"month": "2026-08"},
            [{"id": "t1"}, {"id": "t2"}],
        )
        ids = community.load_sotd_ids(tmp_path, 2026, 8)
        assert ids == {"t1", "t2"}

    def test_none_when_file_missing(self, tmp_path):
        assert community.load_sotd_ids(tmp_path, 2026, 8) is None


class FakeSubreddit:
    """new() yields submissions newest-first (Reddit listing order)."""

    def __init__(self, submissions):
        self._subs = submissions

    def new(self, *args, **kwargs):
        yield from self._subs


class TestDiscoverMonthPosts:
    def test_filters_to_month_and_stops_at_boundary(self):
        subs = [
            FakeSub("sep2", "Later", ts(2026, 9, 20)),
            FakeSub("sep1", "First", ts(2026, 9, 1, 0, 0, 5)),
            FakeSub("aug31", "Before", ts(2026, 8, 31, 23, 59, 59)),
        ]
        subreddit = FakeSubreddit(subs)
        in_month, reached = community.discover_month_posts(subreddit, 2026, 9)
        assert [s.id for s in in_month] == ["sep2", "sep1"]
        assert reached is True

    def test_exhausted_listing_counts_as_boundary(self):
        # a young sub whose entire history is inside the month
        subreddit = FakeSubreddit([FakeSub("a", "A", ts(2026, 9, 5))])
        in_month, reached = community.discover_month_posts(subreddit, 2026, 9)
        assert len(in_month) == 1
        assert reached is True

    def test_cap_before_boundary_is_incomplete(self, monkeypatch):
        monkeypatch.setattr(community, "PAGINATION_CAP", 3)
        subs = [FakeSub(f"p{i:03d}", f"P{i}", ts(2026, 9, 15)) for i in range(5)]
        in_month, reached = community.discover_month_posts(FakeSubreddit(subs), 2026, 9)
        assert len(in_month) == 3
        assert reached is False


class NotComment:
    """Stand-in for praw's MoreComment stubs that survive a failed replace_more."""


class FakeCommentForest:
    def __init__(self, items):
        self._items = items
        self.replace_called = False

    def replace_more(self, limit=None):
        self.replace_called = True

    def list(self):
        return self._items


class TestFetchAllComments:
    def test_walks_full_tree_and_drops_non_comments(self, monkeypatch):
        monkeypatch.setattr(community, "Comment", FakeComment)
        c1 = FakeComment("t1_a", "root", ts(2026, 9, 2), parent_id="t3_abc")
        c2 = FakeComment("t1_b", "reply", ts(2026, 9, 2, 1), parent_id="t1_a")
        more = NotComment()
        sub = FakeSub("abc", "T", ts(2026, 9, 1))
        sub.comments = FakeCommentForest([c1, more, c2])
        result = community.fetch_all_comments(sub)
        assert [c.id for c in result] == ["t1_a", "t1_b"]

    def test_removed_bodies_preserved(self, monkeypatch):
        monkeypatch.setattr(community, "Comment", FakeComment)
        c = FakeComment("t1_x", "[removed]", ts(2026, 9, 2), author=None)
        sub = FakeSub("abc", "T", ts(2026, 9, 1))
        sub.comments = FakeCommentForest([c])
        result = community.fetch_all_comments(sub)
        assert result[0].body == "[removed]"


def write_threads_fixture(tmp_path, month_ids):
    (tmp_path / "threads").mkdir(exist_ok=True)
    (tmp_path / "threads" / "2026-08.json").write_text(
        json.dumps({"meta": {"month": "2026-08"}, "data": [{"id": i} for i in month_ids]})
    )


class FakeArgs:
    def __init__(self, data_dir, force=True, debug=False, verbose=False):
        self.data_dir = str(data_dir)
        self.force = force
        self.debug = debug
        self.verbose = verbose


class FakeReddit:
    def subreddit(self, _name):
        return FakeSubreddit([])


class TestProcessMonth:
    def test_writes_month_file_with_in_pipeline_flags(self, tmp_path, monkeypatch):
        write_threads_fixture(tmp_path, ["sotd1"])
        posts = [
            FakeSub("sotd1", "SOTD Thread", ts(2026, 8, 1)),
            FakeSub("other1", "Discussion", ts(2026, 8, 2)),
        ]

        def fake_discover(subreddit, year, month):
            return posts, True

        def fake_comments(sub):
            return [
                FakeComment("c1", "body", ts(2026, 8, 2), parent_id=f"t3_{sub.id}"),
                FakeComment("c2", "[removed]", ts(2026, 8, 2, 1), parent_id="t1_c1", author=None),
            ]

        monkeypatch.setattr(community, "discover_month_posts", fake_discover)
        monkeypatch.setattr(community, "fetch_all_comments", fake_comments)
        result = community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        assert result == {"year": 2026, "month": 8, "posts": 2, "comments": 4, "complete": True}
        meta, data = community.load_community_file(tmp_path / "community" / "2026-08.json")
        assert meta["month"] == "2026-08"
        assert meta["post_count"] == 2
        assert meta["comment_count"] == 4
        assert meta["in_pipeline_post_count"] == 1
        assert meta["discovery"] == {
            "strategies": ["new_listing"],
            "complete": True,
            "per_strategy": {"new_listing": 2},
        }
        flags = {p["id"]: p["in_pipeline"] for p in data["posts"]}
        assert flags == {"sotd1": True, "other1": False}

    def test_missing_threads_file_warns_and_omits_flag(self, tmp_path, monkeypatch, caplog):
        posts = [FakeSub("solo", "Solo", ts(2026, 8, 3))]
        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: (posts, True))
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        with caplog.at_level(logging.WARNING):
            community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        assert "threads file" in caplog.text
        _, data = community.load_community_file(tmp_path / "community" / "2026-08.json")
        assert "in_pipeline" not in data["posts"][0]

    def test_incomplete_boundary_recorded(self, tmp_path, monkeypatch):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(
            community,
            "discover_month_posts",
            lambda s, y, m: ([FakeSub("x", "X", ts(2026, 8, 5))], False),
        )
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        meta, _ = community.load_community_file(tmp_path / "community" / "2026-08.json")
        assert meta["discovery"]["complete"] is False

    def test_empty_month_writes_no_file(self, tmp_path, monkeypatch):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: ([], True))
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        result = community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        assert result["posts"] == 0
        assert not (tmp_path / "community" / "2026-08.json").exists()

    def test_rerun_without_force_merges(self, tmp_path, monkeypatch):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        monkeypatch.setattr(
            community,
            "discover_month_posts",
            lambda s, y, m: ([FakeSub("a", "A", ts(2026, 8, 1))], True),
        )
        community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        # second run: post "a" moved to a later timestamp, plus new post "b"
        posts = [FakeSub("a", "A edited", ts(2026, 8, 1, 12)), FakeSub("b", "B", ts(2026, 8, 2))]
        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: (posts, True))
        community._process_month(2026, 8, FakeArgs(tmp_path, force=False), reddit=FakeReddit())
        _, data = community.load_community_file(tmp_path / "community" / "2026-08.json")
        by_id = {p["id"]: p for p in data["posts"]}
        assert set(by_id) == {"a", "b"}
        assert by_id["a"]["title"] == "A edited"


class TestMain:
    def test_main_runs_months(self, tmp_path, monkeypatch):
        calls = []

        def fake_process(y, m, args, *, reddit):
            calls.append((y, m))
            return {"year": y, "month": m, "posts": 1, "comments": 0, "complete": True}

        monkeypatch.setattr(community, "_process_month", fake_process)
        monkeypatch.setattr(community, "get_reddit", lambda: FakeReddit())
        code = community.main(["--month", "2026-08", "--force", "--data-dir", str(tmp_path)])
        assert code == 0
        assert calls == [(2026, 8)]


class FakeRedditor:
    def __init__(self, submissions):
        self.submissions = self  # exposes .submissions.new(limit=...)
        self._subs = submissions

    def new(self, limit=None):
        yield from self._subs


class SearchSubreddit(FakeSubreddit):
    """search() parses the lucene timestamp: query and filters by it."""

    def search(self, query, sort=None, syntax=None, time_filter=None):
        import re

        m = re.search(r"timestamp:(\d+)\.\.(\d+)", query)
        lo, hi = int(m.group(1)), int(m.group(2))
        for s in self._subs:
            if lo <= s.created_utc <= hi:
                yield s


class BadSub:
    def search(self, *a, **k):
        raise RuntimeError("unsupported")


class TestDiscoverViaSearch:
    def test_timestamp_window_query(self):
        subs = [
            FakeSub("in1", "In", ts(2025, 7, 10)),
            FakeSub("out", "Out", ts(2025, 6, 10)),
        ]
        subreddit = SearchSubreddit(subs)
        result = community.discover_via_search(subreddit, ts(2025, 7, 1), ts(2025, 8, 1))
        assert [s.id for s in result] == ["in1"]

    def test_empty_on_unsupported_syntax(self):
        # safe_call swallows RuntimeError -> None -> []
        assert community.discover_via_search(BadSub(), 0, 1) == []


class TestEraAuthors:
    def test_ranks_by_comment_count(self, tmp_path):
        (tmp_path / "comments").mkdir()
        comments = [
            {"id": "x1", "author": "busy", "created_utc": "2025-07-01T00:00:00Z"},
            {"id": "x2", "author": "busy", "created_utc": "2025-07-02T00:00:00Z"},
            {"id": "x3", "author": "quiet", "created_utc": "2025-07-03T00:00:00Z"},
            {"id": "x4", "author": "[deleted]", "created_utc": "2025-07-04T00:00:00Z"},
        ]
        (tmp_path / "comments" / "2025-07.json").write_text(
            json.dumps({"meta": {"month": "2025-07"}, "data": comments})
        )
        authors = community.era_authors(tmp_path, ["2025-07"])
        assert authors == ["busy", "quiet"]


class TestDiscoverViaAuthors:
    def test_filters_window_and_dedupes(self):
        a1 = FakeSub("a1", "A1", ts(2025, 7, 5))
        a2 = FakeSub("a2", "A2", ts(2025, 7, 20))
        old = FakeSub("old", "Old", ts(2025, 5, 1))

        class FakeReddit:
            def __init__(self):
                self._people = {"alice": FakeRedditor([a1, old]), "bob": FakeRedditor([a2])}

            def redditor(self, name):
                return self._people[name]

        reddit = FakeReddit()
        result = community.discover_via_authors(
            reddit, ["alice", "alice", "bob"], ts(2025, 7, 1), ts(2025, 8, 1)
        )
        assert sorted(s.id for s in result) == ["a1", "a2"]


class TestBackfillPosts:
    def test_union_seeds_search_and_authors(self, monkeypatch, tmp_path):
        sotd_sub = FakeSub("sotd1", "SOTD Thread", ts(2025, 7, 4))
        search_hit = FakeSub("sr1", "From search", ts(2025, 7, 11))
        author_hit = FakeSub("au1", "From author", ts(2025, 7, 21))

        write_threads_fixture(tmp_path, ["sotd1"])

        class FakeReddit:
            def submission(self, **kwargs):
                assert kwargs.get("id") == "sotd1"
                return sotd_sub

            def subreddit(self, _name):
                return SearchSubreddit([search_hit])

            def redditor(self, name):
                return FakeRedditor([author_hit])

        monkeypatch.setattr(community, "era_authors", lambda d, months, top_n=100: ["alice"])
        posts, strategies, per_strategy = community._backfill_posts(
            FakeReddit(), SearchSubreddit([search_hit]), 2025, 7, {"sotd1"}, tmp_path
        )
        assert {s.id for s in posts} == {"sotd1", "sr1", "au1"}
        assert strategies == ["thread_seed", "timestamp_search", "author_histories"]
        assert per_strategy == {"thread_seed": 1, "timestamp_search": 1, "author_histories": 1}

    def test_strategy_omitted_when_empty(self, monkeypatch, tmp_path):
        write_threads_fixture(tmp_path, [])

        class EmptyReddit:
            def submission(self, **kwargs):
                raise RuntimeError("none")

            def subreddit(self, _name):
                return SearchSubreddit([])

            def redditor(self, name):
                return FakeRedditor([])

        monkeypatch.setattr(community, "era_authors", lambda d, m, top_n=100: [])
        posts, strategies, per_strategy = community._backfill_posts(
            EmptyReddit(), FakeSubreddit([]), 2025, 7, set(), tmp_path
        )
        assert posts == []
        assert strategies == []
        assert per_strategy == {"timestamp_search": 0, "author_histories": 0}


class TestProcessMonthBackfill:
    def test_backfill_path_used_when_boundary_unreached(self, tmp_path, monkeypatch):
        # brief's write_threads_fixture pins 2026-08; this month needs threads/2025-07.json
        (tmp_path / "threads").mkdir()
        (tmp_path / "threads" / "2025-07.json").write_text(
            json.dumps({"meta": {"month": "2025-07"}, "data": [{"id": "sotd1"}]})
        )
        sotd_sub = FakeSub("sotd1", "SOTD Thread", ts(2025, 7, 4))

        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: ([], False))

        class FakeReddit:
            def submission(self, **kwargs):
                return sotd_sub

            def subreddit(self, _name):
                return SearchSubreddit([FakeSub("sr1", "S", ts(2025, 7, 11))])

            def redditor(self, name):
                return FakeRedditor([])

        monkeypatch.setattr(community, "era_authors", lambda d, m, top_n=100: [])
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        result = community._process_month(2025, 7, FakeArgs(tmp_path), reddit=FakeReddit())
        assert result["posts"] == 2 and result["complete"] is False
        meta, data = community.load_community_file(tmp_path / "community" / "2025-07.json")
        assert set(meta["discovery"]["strategies"]) == {
            "new_listing",
            "thread_seed",
            "timestamp_search",
        }
        assert data["posts"][0]["in_pipeline"] is True
