from pathlib import Path

from sotd.fetch.save import load_month_file, write_month_file


def test_write_load_roundtrip(tmp_path: Path) -> None:
    meta = {"month": "2025-04"}
    data = [{"id": "x", "created_utc": "2025-04-01T00:00:00Z"}]

    p = tmp_path / "m.json"
    write_month_file(p, meta, data)

    loaded_meta, loaded_data = load_month_file(p)  # type: ignore
    assert loaded_meta == meta
    assert loaded_data == data
