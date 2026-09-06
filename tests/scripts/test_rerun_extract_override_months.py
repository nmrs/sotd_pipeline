"""Tests for one-shot extract-override month rematch script."""

from pathlib import Path

from scripts.rerun_extract_override_months import months_with_overrides


def test_months_with_overrides_sorted_counts(tmp_path: Path) -> None:
    override_file = tmp_path / "extract_overrides.yaml"
    override_file.write_text(
        """
2026-08:
  p47tzgo:
    razor: "Gillette Tech"
2025-01:
  m99b8f9:
    razor: Koraat
  m68avhv:
    razor: Jenes
    blade: Feather
""",
        encoding="utf-8",
    )

    rows = months_with_overrides(override_file)
    assert [m for m, _, _ in rows] == ["2025-01", "2026-08"]
    assert rows[0] == ("2025-01", 2, 3)
    assert rows[1] == ("2026-08", 1, 1)


def test_months_with_overrides_missing_file(tmp_path: Path) -> None:
    assert months_with_overrides(tmp_path / "missing.yaml") == []
