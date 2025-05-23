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
    assert parse_comment(comment) == {
        "razor": "Blackbird",
        "blade": "Feather",
        "brush": "Simpson",
        "soap": "Tabac",
    }


def test_parse_comment_partial():
    comment = {"body": "\n".join(["* **Brush:** Omega", "* **Soap:** Cella"])}
    assert parse_comment(comment) == {"brush": "Omega", "soap": "Cella"}


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
    assert parse_comment(comment) == {"razor": "Game Changer", "blade": "Nacet", "soap": "Arko"}
