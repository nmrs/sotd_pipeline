from sotd.extract.comment import parse_comment


def test_parse_comment_all_fields():
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** Blackbird",
                "* **Blade:** Feather",
                "* **Brush:** Simpson",
                "* **Soap:** Tabac",
            ]
        )
    }
    ss = parse_comment(comment)
    assert ss == {
        "body": (
            "* **Razor:** Blackbird\n"
            "* **Blade:** Feather\n"
            "* **Brush:** Simpson\n"
            "* **Soap:** Tabac"
        ),
        "razor": "Blackbird",
        "blade": "Feather",
        "brush": "Simpson",
        "soap": "Tabac",
    }


def test_parse_comment_partial():
    comment = {"body": "\n".join(["* **Brush:** Omega", "* **Soap:** Cella"])}
    assert parse_comment(comment) == {
        "body": "* **Brush:** Omega\n* **Soap:** Cella",
        "brush": "Omega",
        "soap": "Cella",
    }


def test_parse_comment_none():
    comment = {"body": "Great shave today, no product mentioned."}
    assert parse_comment(comment) is None


def test_parse_comment_mixed_lines():
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** Game Changer",
                "Blade: Nacet",  # invalid
                "* **Blade:** Nacet",
                "* **Blade:** Feather",  # should be ignored
                "* **Soap:** Arko",
            ]
        )
    }
    assert parse_comment(comment) == {
        "body": (
            "* **Razor:** Game Changer\n"
            "Blade: Nacet\n"
            "* **Blade:** Nacet\n"
            "* **Blade:** Feather\n"
            "* **Soap:** Arko"
        ),
        "razor": "Game Changer",
        "blade": "Nacet",
        "soap": "Arko",
    }


def test_parse_comment_key_order():
    comment = {
        "author": "test_user",
        "body": (
            "* **Razor:** Blackbird\n"
            "* **Blade:** Feather\n"
            "* **Brush:** Simpson\n"
            "* **Soap:** Tabac"
        ),
        "created_utc": "2025-04-01T08:00:00Z",
        "id": "abc123",
        "thread_id": "thread456",
        "thread_title": "Example Title",
        "url": "https://example.com",
    }
    result = parse_comment(comment)
    assert result is not None, "parse_comment returned None"
    keys = list(result.keys())
    assert keys[:7] == [
        "author",
        "body",
        "created_utc",
        "id",
        "thread_id",
        "thread_title",
        "url",
    ], "Comment metadata keys missing or out of order"
    assert keys[7:] == ["razor", "blade", "brush", "soap"], "Extracted keys missing or out of order"


def test_parse_comment_with_markdown_links():
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** [Blackland Blackbird](https://example.com/razor)",
                "* **Blade:** [Feather](https://example.com/blade)",
                "* **Brush:** [Simpson](https://example.com/brush)",
                "* **Soap:** [Tabac](https://example.com/soap)",
            ]
        )
    }
    assert parse_comment(comment) == {
        "body": (
            "* **Razor:** [Blackland Blackbird](https://example.com/razor)\n"
            "* **Blade:** [Feather](https://example.com/blade)\n"
            "* **Brush:** [Simpson](https://example.com/brush)\n"
            "* **Soap:** [Tabac](https://example.com/soap)"
        ),
        "razor": "Blackland Blackbird",
        "blade": "Feather",
        "brush": "Simpson",
        "soap": "Tabac",
    }
