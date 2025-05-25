import pytest
from sotd.utils.text import preprocess_body
from sotd.utils.text import preprocess_body


def test_preprocess_body_splits_into_lines():
    body = "* **Razor:** Blackbird\n* **Blade:** Feather\n* **Brush:** Simpson\n* **Soap:** Tabac"
    processed = preprocess_body(body)
    lines = processed.splitlines()
    assert len(lines) == 4
    assert lines[0] == "* **Razor:** Blackbird"
    assert lines[1] == "* **Blade:** Feather"
    assert lines[2] == "* **Brush:** Simpson"
    assert lines[3] == "* **Soap:** Tabac"


def test_removes_invisible_unicode():
    assert preprocess_body("test\u200bstring") == "teststring"
    assert preprocess_body("\u2060test\u200c") == "test"


def test_strips_whitespace():
    assert preprocess_body("  padded line  ") == "padded line"


def test_unicode_normalization():
    assert preprocess_body("①") == "1"


def test_replaces_smart_quotes():
    assert preprocess_body("‘smart’ “quotes”") == "'smart' \"quotes\""


def test_dash_normalization():
    assert preprocess_body("long–dash —test") == "long-dash -test"


def test_unescapes_common_markdown():
    assert preprocess_body(r"\*escaped\*") == "*escaped*"
    assert preprocess_body(r"\_escaped\_") == "_escaped_"
    assert preprocess_body(r"\`escaped\`") == "`escaped`"
    assert preprocess_body(r"\\backslash") == r"\backslash"


def test_collapses_whitespace():
    assert preprocess_body("A   B\tC\nD") == "A B C\nD"
