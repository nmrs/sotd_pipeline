"""Unit tests for override loader + apply logic."""

from pathlib import Path

from praw.models import Submission
from sotd.fetch.overrides import apply_overrides, load_overrides


class FakeSubmission(Submission):
    """Minimal stub with .id, .title, .permalink."""

    def __init__(self, sid: str, title: str):
        super().__init__(None, sid)  # type: ignore[arg-type, call-arg]
        self.title = title
        self.permalink = f"/x/{sid}/"


class FakeReddit:
    """Stub reddit client returning predefined submissions."""

    def __init__(self, returned):
        self._returned = returned

    def submission(self, submission_id: str):  # type: ignore[no-untyped-def]
        return self._returned[submission_id]


def test_load_overrides(tmp_path: Path) -> None:
    file = tmp_path / "ovr.json"
    file.write_text('{"include":[{"id":"inc"}],"exclude":[{"id":"exc"}]}')

    inc, exc = load_overrides(file)
    assert list(inc) == ["inc"]
    assert list(exc) == ["exc"]


def test_apply_overrides_add_and_remove() -> None:
    base = [FakeSubmission("keep", "Sat SOTD - May 3, 2025"), FakeSubmission("exc", "dummy")]
    include = {"inc": {"id": "inc"}}
    exclude = {"exc": {"id": "exc"}}

    reddit = FakeReddit({"inc": FakeSubmission("inc", "SOTD Thread May 1, 2025")})

    final = apply_overrides(
        base,
        include,
        exclude,
        reddit=reddit,  # type: ignore[arg-type]
        year=2025,
        month=5,
        debug=False,
    )  # type: ignore[arg-type]
    assert [s.id for s in final] == ["inc", "keep"]  # sorted by date
