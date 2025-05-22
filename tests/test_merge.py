from datetime import datetime, timezone

from sotd.fetch.merge import merge_records


def iso(ts: str) -> str:
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).isoformat()


def test_merge_records_latest_wins() -> None:
    old = [
        {"id": "a", "created_utc": iso("2025-05-01T00:00:00Z"), "x": 1},
        {"id": "b", "created_utc": iso("2025-05-02T00:00:00Z"), "x": 2},
    ]
    new = [
        {"id": "b", "created_utc": iso("2025-05-02T01:00:00Z"), "x": 3},
        {"id": "c", "created_utc": iso("2025-05-03T00:00:00Z"), "x": 4},
    ]
    merged = merge_records(old, new)

    assert [r["id"] for r in merged] == ["a", "b", "c"]
    assert next(r for r in merged if r["id"] == "b")["x"] == 3
