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
        "razor": {"original": "Blackbird", "normalized": "Blackbird"},
        "blade": {"original": "Feather", "normalized": "Feather"},
        "brush": {"original": "Simpson", "normalized": "Simpson"},
        "soap": {"original": "Tabac", "normalized": "Tabac"},
    }


def test_parse_comment_partial():
    comment = {"body": "\n".join(["* **Brush:** Omega", "* **Soap:** Cella"])}
    assert parse_comment(comment) == {
        "body": "* **Brush:** Omega\n* **Soap:** Cella",
        "brush": {"original": "Omega", "normalized": "Omega"},
        "soap": {"original": "Cella", "normalized": "Cella"},
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
        "razor": {"original": "Game Changer", "normalized": "Game Changer"},
        "blade": {"original": "Nacet", "normalized": "Nacet"},
        "soap": {"original": "Arko", "normalized": "Arko"},
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
        "razor": {"original": "Blackland Blackbird", "normalized": "Blackland Blackbird"},
        "blade": {"original": "Feather", "normalized": "Feather"},
        "brush": {"original": "Simpson", "normalized": "Simpson"},
        "soap": {"original": "Tabac", "normalized": "Tabac"},
    }


def test_parse_comment_with_competition_tags():
    """Test that competition tags are normalized correctly."""
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** Blackbird $DOORKNOB",
                "* **Blade:** Feather (3x)",
                "* **Brush:** Simpson",
                "* **Soap:** Tabac (sample)",
            ]
        )
    }
    result = parse_comment(comment)
    assert result == {
        "body": (
            "* **Razor:** Blackbird $DOORKNOB\n"
            "* **Blade:** Feather (3x)\n"
            "* **Brush:** Simpson\n"
            "* **Soap:** Tabac (sample)"
        ),
        "razor": {"original": "Blackbird $DOORKNOB", "normalized": "Blackbird"},
        "blade": {"original": "Feather (3x)", "normalized": "Feather"},
        "brush": {"original": "Simpson", "normalized": "Simpson"},
        "soap": {"original": "Tabac (sample)", "normalized": "Tabac"},
    }


def test_parse_comment_with_usage_counts():
    """Test that usage counts are normalized correctly."""
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** Karve Overlander Nickel Plated Brass w/ 90mm Overlander handle",
                "* **Blade:** Gillette Nacet (5)",
                "* **Brush:** Elite handle w/ Declaration knot",
                "* **Soap:** Barrister and Mann Seville",
            ]
        )
    }
    result = parse_comment(comment)
    assert result == {
        "body": (
            "* **Razor:** Karve Overlander Nickel Plated Brass w/ 90mm Overlander handle\n"
            "* **Blade:** Gillette Nacet (5)\n"
            "* **Brush:** Elite handle w/ Declaration knot\n"
            "* **Soap:** Barrister and Mann Seville"
        ),
        "razor": {
            "original": "Karve Overlander Nickel Plated Brass w/ 90mm Overlander handle",
            "normalized": "Karve Overlander Nickel Plated Brass w/ 90mm Overlander handle",
        },
        "blade": {"original": "Gillette Nacet (5)", "normalized": "Gillette Nacet"},
        "brush": {
            "original": "Elite handle w/ Declaration knot",
            "normalized": "Elite handle w/ Declaration knot",
        },
        "soap": {
            "original": "Barrister and Mann Seville",
            "normalized": "Barrister and Mann Seville",
        },
    }


def test_parse_comment_with_special_characters():
    """Test that special characters are handled correctly."""
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** Merkur 37c $ZAMAC $SLANT",
                "* **Blade:** Personna Blue (new)",
                "* **Brush:** Omega 10049",
                "* **Soap:** Stirling Soap Co. Executive Man",
            ]
        )
    }
    result = parse_comment(comment)
    assert result == {
        "body": (
            "* **Razor:** Merkur 37c $ZAMAC $SLANT\n"
            "* **Blade:** Personna Blue (new)\n"
            "* **Brush:** Omega 10049\n"
            "* **Soap:** Stirling Soap Co. Executive Man"
        ),
        "razor": {"original": "Merkur 37c $ZAMAC $SLANT", "normalized": "Merkur 37c"},
        "blade": {"original": "Personna Blue (new)", "normalized": "Personna Blue"},
        "brush": {"original": "Omega 10049", "normalized": "Omega 10049"},
        "soap": {
            "original": "Stirling Soap Co. Executive Man",
            "normalized": "Stirling Soap Co. Executive Man",
        },
    }


def test_parse_comment_empty_strings():
    """Test that empty strings are handled correctly."""
    comment = {
        "body": "\n".join(
            [
                "* **Razor:** ",
                "* **Blade:** Feather",
                "* **Brush:** ",
                "* **Soap:** Tabac",
            ]
        )
    }
    result = parse_comment(comment)
    # Should only include fields that have actual values (empty fields are excluded)
    assert result == {
        "body": ("* **Razor:**\n" "* **Blade:** Feather\n" "* **Brush:**\n" "* **Soap:** Tabac"),
        "blade": {"original": "Feather", "normalized": "Feather"},
        "soap": {"original": "Tabac", "normalized": "Tabac"},
    }


def test_parse_comment_razor_test_exclusion():
    """Test that 'Razor Test' lines are excluded and actual 'Razor:' lines are extracted."""
    # Simulate the exact comment from 2025-07 that had the bug
    comment = {
        "body": "\n".join(
            [
                "Monday 7/28 Shave",
                "",
                "GEM JULY",
                "",
                "MDC MONDAY",
                "",
                "MICROMATIC MONDAY",
                "",
                "",
                "",
                "Razor Test - Received Edge with CrOx Stropping",
                "",
                "It shaved OK on WTG and Across the Chin",
                "",
                "Against the Grain was a bit tuggy",
                "",
                "It's to the stones for a Bevel set",
                "",
                "GEM Bullet Tip took it to a nice BBS result",
                "",
                "",
                "",
                'Razor: Portland Cutlery Steinmetz "Salamander"',
                "",
                "Blade: Original Edge Stropped on Green CrOx",
                "",
                "Clean Up: GEM MicroMatic Bullet Point",
                "",
                "Lather: Martin de Candre Absinthe Sample",
                "",
                "Brush: Stirling PRO Synthetic",
            ]
        )
    }
    result = parse_comment(comment)
    assert result is not None
    assert "razor" in result
    # Should extract the correct razor, not the "Razor Test" line
    assert result["razor"]["original"] == 'Portland Cutlery Steinmetz "Salamander"'
    assert result["razor"]["normalized"] == 'Portland Cutlery Steinmetz "Salamander"'


def test_parse_comment_razor_test_exclusion_2025_06():
    """Test the other affected comment from 2025-06."""
    comment = {
        "body": "\n".join(
            [
                "Sunday 6/22 Shave",
                "",
                "",
                "",
                "Razor Test - 20 Laps on Green CrOx - 50 on Leather",
                "",
                "Not too bad but probably needs a bevel set",
                "",
                "It will eventually turn out to be a cute little shaver",
                "",
                "Parker Semi Slant finished up in one pass",
                "",
                "Overall a pretty decent BBS Sunday shave",
                "",
                "",
                "",
                "Razor: Lee Manufacturing Co. - Lee's Warranted",
                "",
                "Blade: Carbon Steel",
                "",
                "Clean Up: Parker Semi-Slant",
                "",
                "Lather: Abbate Y La Mantia Blue Tobacco",
                "",
                "Brush: Ever-Ready Vintage 150 Boar Knot",
            ]
        )
    }
    result = parse_comment(comment)
    assert result is not None
    assert "razor" in result
    # Should extract the correct razor, not the "Razor Test" line
    assert result["razor"]["original"] == "Lee Manufacturing Co. - Lee's Warranted"
    assert result["razor"]["normalized"] == "Lee Manufacturing Co. - Lee's Warranted"
