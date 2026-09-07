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

    def test_exhausted_listing_without_boundary_is_incomplete(self):
        # the listing ended while still inside the month: we did NOT get every
        # post, even if the SOTD threads all showed up — archives must confirm
        subreddit = FakeSubreddit([FakeSub("a", "A", ts(2026, 9, 5))])
        in_month, reached = community.discover_month_posts(subreddit, 2026, 9)
        assert len(in_month) == 1
        assert reached is False

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
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: [])
        monkeypatch.setattr(community, "_pullpush_get", lambda url: [])
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


class LazyIterFailSub:
    """search() succeeds but iteration raises (praw's ListingGenerator is lazy)."""

    def search(self, *a, **k):
        class FailingGen:
            def __iter__(self):
                raise RuntimeError("rate limit mid-iteration")

        return FailingGen()


class FakeForbidden(Exception):
    """Stand-in for prawcore errors outside safe_call's except tuple."""


class ForbiddenSub:
    def search(self, *a, **k):
        raise FakeForbidden("forbidden")


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

    def test_iteration_failure_returns_empty(self):
        # praw's search() is lazy: the HTTP call happens during iteration, so the
        # list() must run inside safe_call, not after it
        assert community.discover_via_search(LazyIterFailSub(), 0, 1) == []

    def test_exception_outside_safe_call_tuple_returns_empty(self, caplog):
        with caplog.at_level(logging.WARNING):
            assert community.discover_via_search(ForbiddenSub(), 0, 1) == []
        assert "timestamp search unavailable" in caplog.text


class TestBackfillLadder:
    """Listing first; when unconfirmed: thread_seed, timestamp search (2026+
    only), then the archive ladder — Arctic Shift, PullPush — ending complete
    the moment the archive results contain every known SOTD thread."""

    @staticmethod
    def _seed_reddit(subs):
        class SeedReddit:
            def submission(self, **kwargs):
                sub = subs.get(kwargs["id"])
                if sub is None:
                    raise RuntimeError("gone")
                return sub

            def subreddit(self, _name):
                return FakeSubreddit([])

        return SeedReddit()

    def test_arctic_containment_ends_ladder(self, monkeypatch, tmp_path, caplog):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "discover_via_search", lambda s, a, b: [])
        monkeypatch.setattr(
            community,
            "discover_via_arctic_shift",
            lambda r, y, m: [
                FakeSub("sotd1", "A", ts(2026, 8, 10)),
                FakeSub("extra", "E", ts(2026, 8, 12)),
            ],
        )

        def pullpush_must_not_run(r, y, m):
            raise AssertionError("pullpush ran despite arctic containment")

        monkeypatch.setattr(community, "discover_via_pullpush", pullpush_must_not_run)
        with caplog.at_level(logging.INFO):
            posts, strategies, per_strategy, confident = community._backfill_posts(
                self._seed_reddit({"sotd1": FakeSub("sotd1", "S", ts(2026, 8, 5))}),
                FakeSubreddit([]),
                2026,
                8,
                {"sotd1"},
                tmp_path,
            )
        assert confident is True
        assert strategies == ["thread_seed", "arctic_shift"]
        assert per_strategy == {"thread_seed": 1, "timestamp_search": 0, "arctic_shift": 2}
        assert {s.id for s in posts} == {"sotd1", "extra"}
        assert "archive containment: all 1 known SOTD threads present" in caplog.text
        assert (
            "backfill discovery: 2 unique posts via strategies: thread_seed, arctic_shift"
            in caplog.text
        )

    def test_pullpush_fallback_completes_containment(self, monkeypatch, tmp_path, caplog):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "discover_via_search", lambda s, a, b: [])
        monkeypatch.setattr(community, "discover_via_arctic_shift", lambda r, y, m: [])
        monkeypatch.setattr(
            community,
            "discover_via_pullpush",
            lambda r, y, m: [
                FakeSub("sotd1", "P1", ts(2026, 8, 3)),
                FakeSub("sotd2", "P2", ts(2026, 8, 9)),
            ],
        )
        with caplog.at_level(logging.INFO):
            posts, strategies, per_strategy, confident = community._backfill_posts(
                self._seed_reddit(
                    {
                        "sotd1": FakeSub("sotd1", "S1", ts(2026, 8, 5)),
                        "sotd2": FakeSub("sotd2", "S2", ts(2026, 8, 6)),
                    }
                ),
                FakeSubreddit([]),
                2026,
                8,
                {"sotd1", "sotd2"},
                tmp_path,
            )
        assert confident is True
        assert strategies == ["thread_seed", "pullpush"]
        assert "archive containment: 0 of 2 known SOTD threads present" in caplog.text
        assert "engaging pullpush fallback" in caplog.text
        assert "archive containment: all 2 known SOTD threads present" in caplog.text
        assert {s.id for s in posts} == {"sotd1", "sotd2"}

    def test_ladder_exhausted_stays_incomplete(self, monkeypatch, tmp_path, caplog):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "discover_via_search", lambda s, a, b: [])
        monkeypatch.setattr(community, "discover_via_arctic_shift", lambda r, y, m: [])
        monkeypatch.setattr(community, "discover_via_pullpush", lambda r, y, m: [])
        with caplog.at_level(logging.INFO):
            posts, strategies, per_strategy, confident = community._backfill_posts(
                self._seed_reddit({"sotd1": FakeSub("sotd1", "S", ts(2026, 8, 5))}),
                FakeSubreddit([]),
                2026,
                8,
                {"sotd1"},
                tmp_path,
            )
        assert confident is False
        assert "archive containment: 0 of 1 known SOTD threads present" in caplog.text
        assert "month incomplete" in caplog.text
        assert per_strategy == {
            "thread_seed": 1,
            "timestamp_search": 0,
            "arctic_shift": 0,
            "pullpush": 0,
        }

    def test_timestamp_search_skipped_before_floor(self, monkeypatch, tmp_path, caplog):
        def search_must_not_run(s, a, b):
            raise AssertionError("timestamp search ran below the floor")

        monkeypatch.setattr(community, "discover_via_search", search_must_not_run)
        monkeypatch.setattr(community, "discover_via_arctic_shift", lambda r, y, m: [])
        monkeypatch.setattr(community, "discover_via_pullpush", lambda r, y, m: [])
        with caplog.at_level(logging.INFO):
            _posts, _strategies, per_strategy, _confident = community._backfill_posts(
                self._seed_reddit({}), FakeSubreddit([]), 2025, 7, set(), tmp_path
            )
        assert "timestamp_search" not in per_strategy
        assert "timestamp_search: skipped" in caplog.text

    def test_timestamp_search_runs_from_floor(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            community, "discover_via_search", lambda s, a, b: [FakeSub("srch", "S", ts(2026, 8, 6))]
        )
        monkeypatch.setattr(community, "discover_via_arctic_shift", lambda r, y, m: [])
        monkeypatch.setattr(community, "discover_via_pullpush", lambda r, y, m: [])
        _posts, _strategies, per_strategy, _confident = community._backfill_posts(
            self._seed_reddit({}), FakeSubreddit([]), 2026, 8, set(), tmp_path
        )
        assert per_strategy["timestamp_search"] == 1

    def test_author_strategy_removed(self):
        assert not hasattr(community, "era_authors")
        assert not hasattr(community, "discover_via_authors")


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

        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: [])
        monkeypatch.setattr(community, "_pullpush_get", lambda url: [])
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        result = community._process_month(2025, 7, FakeArgs(tmp_path), reddit=FakeReddit())
        # 2025-07 is below the timestamp-search floor: only the seed contributes
        assert result["posts"] == 1 and result["complete"] is False
        meta, data = community.load_community_file(tmp_path / "community" / "2025-07.json")
        assert set(meta["discovery"]["strategies"]) == {"thread_seed"}
        assert data["posts"][0]["in_pipeline"] is True


class TestDepthCappedListing:
    """A .new() listing that ends without reaching the month boundary is not
    proof of completeness: Reddit serves only ~1000 items, so for months older
    than ~8 listings-worth the listing dies mid-history. The known SOTD thread
    IDs are the cross-check: any missing -> not complete -> backfill engages."""

    def test_listing_boundary_claim_contradicted_engages_backfill(self, tmp_path, monkeypatch):
        # within the horizon, a claimed boundary missing known SOTD threads is
        # downgraded and backfill engages (defense against listing gaps)
        write_threads_fixture(tmp_path, ["sotd1", "sotd2"])
        monkeypatch.setattr(
            community,
            "discover_month_posts",
            lambda s, y, m: ([FakeSub("sotd1", "S", ts(2026, 8, 31))], True),
        )
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: [])
        monkeypatch.setattr(community, "_pullpush_get", lambda url: [])
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])

        class SeedReddit:
            def submission(self, **kwargs):
                return FakeSub(kwargs["id"], "S", ts(2026, 8, 5))

            def subreddit(self, _name):
                return FakeSubreddit([])

        result = community._process_month(2026, 8, FakeArgs(tmp_path), reddit=SeedReddit())
        assert result["complete"] is False
        assert result["posts"] == 2
        meta, data = community.load_community_file(tmp_path / "community" / "2026-08.json")
        assert meta["discovery"]["complete"] is False
        assert set(meta["discovery"]["strategies"]) == {"new_listing", "thread_seed"}
        assert {p["id"] for p in data["posts"]} == {"sotd1", "sotd2"}

    def test_full_sotd_coverage_keeps_listing_verdict(self, tmp_path, monkeypatch):
        # boundary claimed True and every known SOTD thread present: no downgrade,
        # no backfill (the 2026-01-style month that genuinely enumerated).
        (tmp_path / "threads").mkdir(exist_ok=True)
        (tmp_path / "threads" / "2026-01.json").write_text(
            json.dumps({"meta": {"month": "2026-01"}, "data": [{"id": "sotd1"}, {"id": "sotd2"}]})
        )
        monkeypatch.setattr(
            community,
            "discover_month_posts",
            lambda s, y, m: (
                [FakeSub("sotd1", "S", ts(2026, 1, 3)), FakeSub("sotd2", "S2", ts(2026, 1, 20))],
                True,
            ),
        )
        monkeypatch.setattr(community, "_backfill_posts", lambda *a, **k: ([], [], {}, False))
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        result = community._process_month(2026, 1, FakeArgs(tmp_path), reddit=FakeReddit())
        assert result["complete"] is True
        meta, data = community.load_community_file(tmp_path / "community" / "2026-01.json")
        assert meta["discovery"]["complete"] is True
        assert meta["discovery"]["strategies"] == ["new_listing"]
        assert {p["id"] for p in data["posts"]} == {"sotd1", "sotd2"}


class TestPullpushSubmissionIds:
    def test_paginates_until_short_page(self, monkeypatch):
        pages = [
            [{"id": f"a{i:02d}", "created_utc": ts(2025, 1, 20)} for i in range(100)],
            [{"id": "b1", "created_utc": ts(2025, 1, 10)}],
        ]
        monkeypatch.setattr(community, "_pullpush_get", lambda url: pages.pop(0))
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        ids = community.pullpush_submission_ids(2025, 1)
        assert ids == {f"a{i:02d}" for i in range(100)} | {"b1"}

    def test_drops_ids_outside_month_window(self, monkeypatch):
        page = [
            {"id": "in1", "created_utc": ts(2025, 1, 5)},
            {"id": "future", "created_utc": ts(2025, 2, 5)},
        ]
        monkeypatch.setattr(community, "_pullpush_get", lambda url: page)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        assert community.pullpush_submission_ids(2025, 1) == {"in1"}

    def test_archive_failure_yields_empty(self, monkeypatch):
        monkeypatch.setattr(community, "_pullpush_get", lambda url: None)
        assert community.pullpush_submission_ids(2025, 1) == set()

    def test_repeating_page_stops_without_looping(self, monkeypatch):
        # archive serves the same full-size page twice: the loop guard must stop it
        page = [{"id": "same", "created_utc": ts(2025, 1, 10)} for _ in range(100)]
        monkeypatch.setattr(community, "_pullpush_get", lambda url: page)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        assert community.pullpush_submission_ids(2025, 1) == {"same"}


class TestPullpushGet:
    def test_429_then_success(self, monkeypatch):
        from urllib.error import HTTPError

        class FakeResp:
            def __init__(self, payload):
                self._p = json.dumps(payload).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return self._p

        calls = []

        def fake_urlopen(req, timeout=None):
            calls.append(req)
            if len(calls) == 1:
                raise HTTPError("u", 429, "Too Many Requests", None, None)
            return FakeResp({"data": [{"id": "x", "created_utc": ts(2025, 1, 1)}]})

        monkeypatch.setattr(community.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        result = community._pullpush_get("https://api.pullpush.io/x")
        assert result == [{"id": "x", "created_utc": ts(2025, 1, 1)}]
        assert len(calls) == 2

    def test_persistent_429_returns_none(self, monkeypatch):
        from urllib.error import HTTPError

        def fake_urlopen(req, timeout=None):
            raise HTTPError("u", 429, "Too Many Requests", None, None)

        monkeypatch.setattr(community.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        assert community._pullpush_get("https://api.pullpush.io/x") is None


class TestDiscoverViaPullpush:
    def test_ids_become_fresh_submissions_dead_seed_skipped(self, monkeypatch):
        monkeypatch.setattr(community, "pullpush_submission_ids", lambda y, m: {"good1", "dead"})
        good = FakeSub("good1", "Good", ts(2025, 1, 5))

        class DeadSub:
            id = "dead"

            @property
            def title(self):
                raise RuntimeError("gone")

        class FakeReddit:
            def submission(self, *, id):
                return good if id == "good1" else DeadSub()

        posts = community.discover_via_pullpush(FakeReddit(), 2025, 1)
        assert [s.id for s in posts] == ["good1"]


class TestProgressNarration:
    """Runtime narration: strategies log what they are doing at INFO."""

    def test_backfill_logs_ladder_and_containment(self, monkeypatch, tmp_path, caplog):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(
            community,
            "discover_via_search",
            lambda s, a, b: [FakeSub("srch", "S3", ts(2026, 8, 15))],
        )
        monkeypatch.setattr(
            community,
            "discover_via_arctic_shift",
            lambda r, y, m: [
                FakeSub("sotd1", "A", ts(2026, 8, 10)),
                FakeSub("sotd2", "A2", ts(2026, 8, 11)),
            ],
        )

        def pullpush_must_not_run(r, y, m):
            raise AssertionError("pullpush ran despite arctic containment")

        monkeypatch.setattr(community, "discover_via_pullpush", pullpush_must_not_run)

        class SeedReddit:
            def submission(self, **kwargs):
                return FakeSub(kwargs["id"], "S", ts(2026, 8, 5))

            def subreddit(self, _name):
                return FakeSubreddit([])

        with caplog.at_level(logging.INFO):
            posts, strategies, per_strategy, confident = community._backfill_posts(
                SeedReddit(), FakeSubreddit([]), 2026, 8, {"sotd1", "sotd2"}, tmp_path
            )
        assert {s.id for s in posts} == {"sotd1", "sotd2", "srch"}
        assert "thread_seed: resolving 2 known SOTD threads" in caplog.text
        assert "thread_seed: resolved 2 of 2" in caplog.text
        assert "timestamp_search: found 1 posts" in caplog.text
        assert "archive containment: all 2 known SOTD threads present" in caplog.text
        assert (
            "backfill discovery: 3 unique posts via strategies: thread_seed, timestamp_search, arctic_shift"
            in caplog.text
        )

    def test_pullpush_paging_logs_pages_and_summary(self, monkeypatch, caplog):
        pages = [
            [{"id": f"a{i:02d}", "created_utc": ts(2025, 1, 20)} for i in range(100)],
            [{"id": "b1", "created_utc": ts(2025, 1, 10)}],
        ]
        monkeypatch.setattr(community, "_pullpush_get", lambda url: pages.pop(0))
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        with caplog.at_level(logging.INFO):
            ids = community.pullpush_submission_ids(2025, 1)
        assert len(ids) == 101
        assert "pullpush: page 1: 100 ids (oldest 2025-01-20)" in caplog.text
        assert "pullpush: page 2: 1 ids (oldest 2025-01-10)" in caplog.text
        assert "pullpush: 101 archive ids across 2 pages" in caplog.text

    def test_process_month_narrates_without_verbose(self, tmp_path, monkeypatch, caplog):
        write_threads_fixture(tmp_path, ["sotd1"])
        posts = [
            FakeSub("sotd1", "SOTD Thread", ts(2026, 8, 1)),
            FakeSub("other1", "Discussion", ts(2026, 8, 2)),
        ]
        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: (posts, True))
        monkeypatch.setattr(
            community, "fetch_all_comments", lambda s: [FakeComment("c1", "b", ts(2026, 8, 2))]
        )
        with caplog.at_level(logging.INFO):
            community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        assert "fetching comment trees for 2 threads" in caplog.text
        assert "wrote 2 posts / 2 comments (discovery: new_listing, complete)" in caplog.text

    def test_listing_logs_progress_and_discovery(self, caplog):
        subs = [FakeSub(f"p{i:03d}", f"P{i}", ts(2026, 9, 15)) for i in range(1001)]
        with caplog.at_level(logging.INFO):
            in_month, reached = community.discover_month_posts(FakeSubreddit(subs), 2026, 9)
        assert len(in_month) == 1001
        assert reached is False
        assert "listing pulled 1000 items" in caplog.text
        assert "listing discovered 1001 posts (boundary not reached)" in caplog.text

    def test_listing_progress_silent_below_1000(self, caplog):
        subs = [FakeSub(f"p{i:03d}", f"P{i}", ts(2026, 9, 15)) for i in range(3)]
        with caplog.at_level(logging.INFO):
            community.discover_month_posts(FakeSubreddit(subs), 2026, 9)
        assert "listing pulled" not in caplog.text
        assert "listing discovered 3 posts" in caplog.text


class TestArcticShiftSubmissionIds:
    def test_paginates_until_short_page(self, monkeypatch):
        pages = [
            [{"id": f"a{i:02d}", "created_utc": ts(2025, 1, 20)} for i in range(100)],
            [{"id": "b1", "created_utc": ts(2025, 1, 10)}],
        ]
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: pages.pop(0))
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        ids = community.arctic_shift_submission_ids(2025, 1)
        assert ids == {f"a{i:02d}" for i in range(100)} | {"b1"}

    def test_drops_ids_outside_month_window(self, monkeypatch):
        page = [
            {"id": "in1", "created_utc": ts(2025, 1, 5)},
            {"id": "future", "created_utc": ts(2025, 2, 5)},
        ]
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: page)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        assert community.arctic_shift_submission_ids(2025, 1) == {"in1"}

    def test_archive_failure_yields_empty(self, monkeypatch):
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: None)
        assert community.arctic_shift_submission_ids(2025, 1) == set()

    def test_repeating_page_stops_without_looping(self, monkeypatch):
        page = [{"id": "same", "created_utc": ts(2025, 1, 10)} for _ in range(100)]
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: page)
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        assert community.arctic_shift_submission_ids(2025, 1) == {"same"}

    def test_logs_page_progress_and_summary(self, monkeypatch, caplog):
        pages = [
            [{"id": f"a{i:02d}", "created_utc": ts(2025, 1, 20)} for i in range(100)],
            [{"id": "b1", "created_utc": ts(2025, 1, 10)}],
        ]
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: pages.pop(0))
        monkeypatch.setattr(community.time, "sleep", lambda *_: None)
        with caplog.at_level(logging.INFO):
            ids = community.arctic_shift_submission_ids(2025, 1)
        assert len(ids) == 101
        assert "arctic_shift: page 1: 100 ids (oldest 2025-01-20)" in caplog.text
        assert "arctic_shift: page 2: 1 ids (oldest 2025-01-10)" in caplog.text
        assert "arctic_shift: 101 archive ids across 2 pages" in caplog.text

    def test_discover_resolves_ids_on_reddit(self, monkeypatch):
        class ArchiveReddit:
            def __init__(self):
                self.n = 0

            def submission(self, **kwargs):
                if kwargs["id"] == "dead":
                    raise RuntimeError("gone")
                return FakeSub(kwargs["id"], "T", ts(2025, 1, 5))

        reddit = ArchiveReddit()
        monkeypatch.setattr(
            community,
            "_arctic_shift_get",
            lambda url: [
                {"id": "a1", "created_utc": ts(2025, 1, 5)},
                {"id": "dead", "created_utc": ts(2025, 1, 6)},
            ],
        )
        posts = community.discover_via_arctic_shift(reddit, 2025, 1)
        assert [s.id for s in posts] == ["a1"]


class TestRedditHorizonSkip:
    """Months older than the listing horizon skip Reddit discovery entirely:
    no /new walk (it cannot reach them — the 1000-item window ends inside
    Dec 2025) and no timestamp search; backfill starts at thread_seed."""

    def test_listing_walk_skipped_for_2025(self, tmp_path, monkeypatch, caplog):
        (tmp_path / "threads").mkdir(exist_ok=True)
        (tmp_path / "threads" / "2025-12.json").write_text(
            json.dumps({"meta": {"month": "2025-12"}, "data": [{"id": "sotd1"}]})
        )

        def walk_must_not_run(s, y, m):
            raise AssertionError("listing walk ran below the horizon floor")

        monkeypatch.setattr(community, "discover_month_posts", walk_must_not_run)
        monkeypatch.setattr(community, "_arctic_shift_get", lambda url: [])
        monkeypatch.setattr(community, "_pullpush_get", lambda url: [])
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])

        class SeedReddit:
            def submission(self, **kwargs):
                return FakeSub(kwargs["id"], "S", ts(2025, 12, 5))

            def subreddit(self, _name):
                return FakeSubreddit([])

        with caplog.at_level(logging.INFO):
            result = community._process_month(2025, 12, FakeArgs(tmp_path), reddit=SeedReddit())
        assert result["complete"] is False
        meta, _data = community.load_community_file(tmp_path / "community" / "2025-12.json")
        assert set(meta["discovery"]["strategies"]) == {"thread_seed"}
        assert "new_listing" not in meta["discovery"]["per_strategy"]
        assert "listing skipped" in caplog.text

    def test_listing_walk_runs_within_horizon(self, tmp_path, monkeypatch):
        write_threads_fixture(tmp_path, [])
        monkeypatch.setattr(community, "discover_month_posts", lambda s, y, m: ([], True))
        monkeypatch.setattr(community, "fetch_all_comments", lambda s: [])
        result = community._process_month(2026, 8, FakeArgs(tmp_path), reddit=FakeReddit())
        assert result["complete"] is True
