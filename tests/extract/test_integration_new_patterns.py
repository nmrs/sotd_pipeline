#!/usr/bin/env python3
"""
Integration tests for new extraction patterns using real examples from analysis data.
"""

import pytest
from sotd.extract.comment import parse_comment
from sotd.extract.fields import extract_field


class TestRealDataIntegration:
    """Test new patterns with real examples from analysis data."""

    def test_real_checkmark_format_examples(self):
        """Test checkmark format with real examples from analysis."""
        real_examples = [
            ("✓Brush: Kent Infinity", "brush", "Kent Infinity"),
            ("✓Razor: Kopparkant +", "razor", "Kopparkant +"),
            ("✓Blade: feather (1)", "blade", "feather (1)"),
            ("✓Lather: Cremo Citrus", "soap", "Cremo Citrus"),
        ]

        for line, field, expected_value in real_examples:
            result = extract_field(line, field)
            assert result is not None, f"Should extract from: {line}"
            assert result.strip() == expected_value, f"Expected '{expected_value}', got '{result}'"

    def test_real_emoji_bold_format_examples(self):
        """Test emoji bold format with real examples from analysis."""
        real_examples = [
            (
                "* **Straight Razor** - Fontani Scarperia - Lapis Lazuli - Barber's Notch - 7/8 - Near Wedge - Full Mirror Finish",
                "razor",
                "Fontani Scarperia - Lapis Lazuli - Barber's Notch - 7/8 - Near Wedge - Full Mirror Finish",
            ),
            (
                "* **Shaving Brush** - Leonidam - Horus - 26mm Fan (Silvertip Badger)",
                "brush",
                "Leonidam - Horus - 26mm Fan (Silvertip Badger)",
            ),
            (
                "* **Shaving Soap** - Saponificio Varesino - Dolomiti - Beta 4.3",
                "soap",
                "Saponificio Varesino - Dolomiti - Beta 4.3",
            ),
        ]

        for line, field, expected_value in real_examples:
            result = extract_field(line, field)
            assert result is not None, f"Should extract from: {line}"
            assert result.strip() == expected_value, f"Expected '{expected_value}', got '{result}'"

    def test_real_complete_comment_parsing(self):
        """Test parsing complete comments with new patterns."""
        # Real comment from analysis with checkmark format
        checkmark_comment = {
            "body": """19MAY25

✓Brush: Kent Infinity

✓Razor: Kopparkant +

✓Blade: feather (1)

✓Lather: Cremo Citrus

✓Post Shave: Thayer's & Nivea baum

Have a great start to your work week or retirement week for that matter!""",
            "id": "test_real_checkmark",
        }

        result = parse_comment(checkmark_comment)
        assert result is not None, "Should parse checkmark format comment"
        assert "brush" in result, "Should extract brush field"
        assert "razor" in result, "Should extract razor field"
        assert "blade" in result, "Should extract blade field"
        assert "soap" in result, "Should extract soap field"

        # Real comment from analysis with emoji bold format
        emoji_bold_comment = {
            "body": """####[SOTD Tuesday 16 March 2021](https://imgur.com/a/FmEkF3f)
* **Straight Razor** - Fontani Scarperia - Lapis Lazuli - Barber's Notch - 7/8 - Near Wedge - Full Mirror Finish
* **Shaving Brush** - Leonidam - Horus - 26mm Fan (Silvertip Badger)
* **Shaving Bowl** - Saponificio Varesino - Shaving Grail Bowl
* **Shaving Soap** - Saponificio Varesino - Dolomiti - Beta 4.3
* **After-Shave** - Saponificio Varesino - Dolomiti - Splash""",
            "id": "test_real_emoji_bold",
        }

        result = parse_comment(emoji_bold_comment)
        assert result is not None, "Should parse emoji bold format comment"
        assert "razor" in result, "Should extract razor field"
        assert "brush" in result, "Should extract brush field"
        assert "soap" in result, "Should extract soap field"

    def test_mixed_format_comment(self):
        """Test parsing comments with mixed formats (new + existing)."""
        mixed_comment = {
            "body": """**SOTD - 27.06.23**

* **Noble Otter - Orbit**
* **Dogwood - Arcane Abyss 26mm**
* **Swing - Swing Travel Razor**
* **Polsilver Stainless Steel**

✓Brush: Kent Infinity
✓Razor: Kopparkant +
✓Blade: feather (1)
✓Lather: Cremo Citrus

[Orbit]( https://imgur.com/a/aA300Kx)""",
            "id": "test_mixed_formats",
        }

        result = parse_comment(mixed_comment)
        assert result is not None, "Should parse mixed format comment"
        # Should extract both emoji bold and checkmark formats
        assert "brush" in result, "Should extract brush field"
        assert "razor" in result, "Should extract razor field"
        assert "blade" in result, "Should extract blade field"
        assert "soap" in result, "Should extract soap field"


class TestEndToEndPipeline:
    """Test complete extraction → match → enrich flow with new patterns."""

    def test_extraction_output_format(self):
        """Test that extracted data structure matches existing format."""
        comment = {
            "body": "✓Brush: Kent Infinity\n✓Razor: Kopparkant +",
            "id": "test_format",
        }

        result = parse_comment(comment)
        assert result is not None, "Should parse comment"

        # Check that output structure matches existing format
        assert isinstance(result, dict), "Result should be a dictionary"

        # Check that fields have the expected structure
        for field in ["brush", "razor"]:
            if field in result:
                field_data = result[field]
                assert isinstance(field_data, dict), f"{field} should be a dictionary"
                assert "original" in field_data, f"{field} should have 'original' key"
                assert "normalized" in field_data, f"{field} should have 'normalized' key"

    def test_no_regression_in_existing_patterns(self):
        """Test that existing extraction patterns still work."""
        existing_pattern_comment = {
            "body": "**Brush**: Kent Infinity\n**Razor**: Kopparkant +",
            "id": "test_existing_patterns",
        }

        result = parse_comment(existing_pattern_comment)
        assert result is not None, "Should parse existing pattern comment"
        assert "brush" in result, "Should extract brush field"
        assert "razor" in result, "Should extract razor field"


class TestPerformanceIntegration:
    """Test performance with real data samples."""

    def test_large_real_data_performance(self):
        """Test performance with large real comment datasets."""
        # Create a large comment with real examples
        large_comment_body = []

        # Add real checkmark examples
        checkmark_examples = [
            "✓Brush: Kent Infinity",
            "✓Razor: Kopparkant +",
            "✓Blade: feather (1)",
            "✓Lather: Cremo Citrus",
        ]

        # Add real emoji bold examples
        emoji_bold_examples = [
            "* **Straight Razor** - Fontani Scarperia - Lapis Lazuli - Barber's Notch - 7/8 - Near Wedge - Full Mirror Finish",
            "* **Shaving Brush** - Leonidam - Horus - 26mm Fan (Silvertip Badger)",
            "* **Shaving Soap** - Saponificio Varesino - Dolomiti - Beta 4.3",
        ]

        # Add existing pattern examples
        existing_examples = [
            "**Brush**: Kent Infinity",
            "**Razor**: Kopparkant +",
            "**Blade**: feather (1)",
            "**Soap**: Cremo Citrus",
        ]

        # Combine all examples and repeat to create large dataset
        all_examples = checkmark_examples + emoji_bold_examples + existing_examples
        for _ in range(50):  # 50 repetitions = 400 lines
            large_comment_body.extend(all_examples)

        large_comment = {
            "body": "\n".join(large_comment_body),
            "id": "test_large_real_data",
        }

        import time

        start_time = time.time()
        result = parse_comment(large_comment)
        end_time = time.time()

        # Should complete in reasonable time (<5 seconds for 400 lines)
        duration = end_time - start_time
        assert duration < 5.0, f"Parsing took too long: {duration:.2f}s"
        assert result is not None, "Should parse large comment successfully"

        # Should extract multiple fields
        extracted_fields = list(result.keys())
        assert len(extracted_fields) > 0, "Should extract at least some fields"

    def test_memory_usage_with_real_data(self):
        """Test memory usage with real data samples."""
        # Create a realistic comment with real examples
        realistic_comment = {
            "body": """19MAY25

✓Brush: Kent Infinity

✓Razor: Kopparkant +

✓Blade: feather (1)

✓Lather: Cremo Citrus

✓Post Shave: Thayer's & Nivea baum

Have a great start to your work week or retirement week for that matter!

####[SOTD Tuesday 16 March 2021](https://imgur.com/a/FmEkF3f)
* **Straight Razor** - Fontani Scarperia - Lapis Lazuli - Barber's Notch - 7/8 - Near Wedge - Full Mirror Finish
* **Shaving Brush** - Leonidam - Horus - 26mm Fan (Silvertip Badger)
* **Shaving Bowl** - Saponificio Varesino - Shaving Grail Bowl
* **Shaving Soap** - Saponificio Varesino - Dolomiti - Beta 4.3
* **After-Shave** - Saponificio Varesino - Dolomiti - Splash""",
            "id": "test_realistic_comment",
        }

        import time

        start_time = time.time()
        result = parse_comment(realistic_comment)
        end_time = time.time()

        # Should complete quickly (<1 second for realistic comment)
        duration = end_time - start_time
        assert duration < 1.0, f"Parsing took too long: {duration:.2f}s"
        assert result is not None, "Should parse realistic comment successfully"

        # Should extract both checkmark and emoji bold formats
        assert "brush" in result, "Should extract brush from checkmark format"
        assert "razor" in result, "Should extract razor from emoji bold format"


if __name__ == "__main__":
    pytest.main([__file__])
