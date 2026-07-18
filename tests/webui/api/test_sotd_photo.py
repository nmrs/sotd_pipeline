"""Unit tests for SOTD header photo link extraction."""

from webui.api.analysis import MismatchItem
from webui.api.sotd_photo import extract_sotd_header_link, prefer_first_photo_url


class TestExtractSotdHeaderLink:
    def test_returns_url_when_header_has_markdown_link(self) -> None:
        body = (
            "[**SOTD: Jul 10, 2026**](https://i.ibb.co/Ps8ZgMCb/sotd-2026-07-10.jpg)\n"
            "**Razor:** Wade & Butcher\n"
        )
        assert extract_sotd_header_link(body) == "https://i.ibb.co/Ps8ZgMCb/sotd-2026-07-10.jpg"

    def test_returns_none_for_plain_header_without_link(self) -> None:
        body = "* **SOTD Jul 10**\n**Razor:** Some Razor\n"
        assert extract_sotd_header_link(body) is None

    def test_returns_none_for_empty_body(self) -> None:
        assert extract_sotd_header_link("") is None
        assert extract_sotd_header_link(None) is None  # type: ignore[arg-type]

    def test_returns_first_link_only_on_header_line(self) -> None:
        body = (
            "[SOTD](https://imgur.com/a/first) [extra](https://example.com/second)\n"
            "[later](https://example.com/third)\n"
        )
        assert extract_sotd_header_link(body) == "https://imgur.com/a/first"

    def test_skips_leading_blank_lines(self) -> None:
        body = "\n\n[SOTD 7/5](https://imgur.com/a/qWCciwm)\n**Razor:** X\n"
        assert extract_sotd_header_link(body) == "https://imgur.com/a/qWCciwm"

    def test_any_header_link_counts_not_just_image_hosts(self) -> None:
        body = "[SOTD](https://example.com/album/123)\n**Brush:** Foo\n"
        assert extract_sotd_header_link(body) == "https://example.com/album/123"


class TestPreferFirstPhotoUrl:
    def test_keeps_existing_when_set(self) -> None:
        assert (
            prefer_first_photo_url("https://first.example/a", "https://second.example/b")
            == "https://first.example/a"
        )

    def test_takes_new_when_existing_unset(self) -> None:
        assert (
            prefer_first_photo_url(None, "https://second.example/b") == "https://second.example/b"
        )

    def test_none_when_both_unset(self) -> None:
        assert prefer_first_photo_url(None, None) is None


class TestMismatchItemSotdPhotoUrl:
    def test_mismatch_item_includes_sotd_photo_url(self) -> None:
        item = MismatchItem(
            original="Test",
            matched={"brand": "B", "model": "M"},
            pattern="p",
            match_type="regex",
            count=1,
            examples=["ex"],
            comment_ids=["owperd6"],
            sotd_photo_url="https://i.ibb.co/Ps8ZgMCb/sotd-2026-07-10.jpg",
        )
        assert item.sotd_photo_url == "https://i.ibb.co/Ps8ZgMCb/sotd-2026-07-10.jpg"

    def test_mismatch_item_sotd_photo_url_defaults_to_none(self) -> None:
        item = MismatchItem(
            original="Test",
            matched={"brand": "B", "model": "M"},
            pattern="p",
            match_type="regex",
            count=1,
            examples=["ex"],
            comment_ids=["123"],
        )
        assert item.sotd_photo_url is None
