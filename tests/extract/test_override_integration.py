#!/usr/bin/env python3
"""Integration tests for override application in extract phase."""

import json
import tempfile
from pathlib import Path

from sotd.extract.comment import parse_comment, run_extraction_for_month
from sotd.extract.override_manager import OverrideManager


class TestOverrideIntegration:
    """Test override integration with extract phase."""

    def test_parse_comment_with_override_existing_field(self):
        """Test parsing comment with override for existing field."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "2025-01-15T10:00:00Z",
        }

        # Create override manager with override
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            result = parse_comment(comment, override_manager, processing_month="2025-01")

            assert result is not None
            assert isinstance(result, dict)
            assert "razor" in result
            assert result["razor"]["original"] == "Ko"  # Preserved
            assert result["razor"]["normalized"] == "Koraat"  # Overridden
            assert result["razor"]["overridden"] == "Normalized"
            assert "blade" in result
            assert result["blade"]["normalized"] == "Feather"  # Unchanged
            assert "overridden" not in result["blade"]  # No override flag

        finally:
            override_file.unlink()

    def test_parse_comment_with_override_missing_field(self):
        """Test parsing comment with override for missing field."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Blade: Feather",  # No razor field
            "created_utc": "2025-01-15T10:00:00Z",
        }

        # Create override manager with override for missing field
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            result = parse_comment(comment, override_manager, processing_month="2025-01")

            assert result is not None
            assert "razor" in result
            assert result["razor"]["original"] == "Koraat"  # Created from override
            assert result["razor"]["normalized"] == "Koraat"  # Created from override
            assert result["razor"]["overridden"] == "Original,Normalized"
            assert "blade" in result
            assert result["blade"]["normalized"] == "Feather"  # Unchanged

        finally:
            override_file.unlink()

    def test_parse_comment_without_override(self):
        """Test parsing comment without any overrides."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "2025-01-15T10:00:00Z",
        }

        result = parse_comment(comment, None)  # No override manager

        assert result is not None
        assert "razor" in result
        assert result["razor"]["original"] == "Ko"
        assert result["razor"]["normalized"] == "Ko"  # No normalization in test
        assert "overridden" not in result["razor"]
        assert "blade" in result
        assert result["blade"]["normalized"] == "Feather"

    def test_parse_comment_with_override_no_comment_id(self):
        """Test parsing comment without comment ID (should skip overrides)."""
        comment = {
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "2025-01-15T10:00:00Z",
            # Missing id field
        }

        # Create override manager
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            result = parse_comment(comment, override_manager)

            # Should process normally without applying overrides
            assert result is not None
            assert "razor" in result
            assert result["razor"]["original"] == "Ko"
            assert result["razor"]["normalized"] == "Ko"
            assert "overridden" not in result["razor"]

        finally:
            override_file.unlink()

    def test_parse_comment_with_override_invalid_timestamp(self):
        """Test parsing comment with invalid timestamp format but valid processing_month."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "invalid-timestamp",  # Invalid format
        }

        # Create override manager
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # With processing_month provided, override should apply despite invalid timestamp
            result = parse_comment(comment, override_manager, processing_month="2025-01")

            assert result is not None
            assert "razor" in result
            assert result["razor"]["original"] == "Ko"
            assert result["razor"]["normalized"] == "Koraat"  # Override applied
            assert result["razor"]["overridden"] == "Normalized"

        finally:
            override_file.unlink()

    def test_parse_comment_with_override_no_processing_month_invalid_timestamp(self):
        """Test parsing comment with invalid timestamp and no processing_month (fallback)."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "invalid-timestamp",  # Invalid format
        }

        # Create override manager
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Without processing_month and invalid timestamp, override should not apply
            result = parse_comment(comment, override_manager, processing_month=None)

            assert result is not None
            assert "razor" in result
            assert result["razor"]["original"] == "Ko"
            assert result["razor"]["normalized"] == "Ko"  # No override applied
            assert "overridden" not in result["razor"]

        finally:
            override_file.unlink()

    def test_override_uses_processing_month_not_created_utc(self):
        """Test that overrides use processing_month, not created_utc timestamp."""
        # This tests the bug where created_utc is from a different month than
        # the processing month (e.g., comment posted late in thread)
        comment = {
            "id": "n0y9seq",
            "body": "* **Lather:** Stirlingster and Mann - Roam Again",
            "created_utc": "2025-07-02T14:47:59Z",  # July timestamp
        }

        # Override is in 2025-06 section (processing month)
        override_content = """
2025-06:
  n0y9seq:
    soap: "100g of Barrister and Mann - Roam Two & 100g of Stirling Soap Co. - Texas on Fire"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Process as 2025-06 even though created_utc is 2025-07
            result = parse_comment(comment, override_manager, processing_month="2025-06")

            # Override should be applied because we're processing 2025-06
            assert result is not None
            assert "soap" in result
            assert (
                result["soap"]["normalized"]
                == "100g of Barrister and Mann - Roam Two & 100g of Stirling Soap Co. - Texas on Fire"
            )
            assert result["soap"]["overridden"] == "Normalized"

        finally:
            override_file.unlink()

    def test_run_extraction_for_month_with_overrides(self):
        """Test running extraction for month with overrides."""
        # Create temporary input file
        input_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Ko\n✓Blade: Feather",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(input_data, f)

            # Create override file
            override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write(override_content)

            # Create override manager
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Run extraction
            result = run_extraction_for_month("2025-01", str(temp_path), override_manager)

            assert result is not None
            assert len(result["data"]) == 1
            comment = result["data"][0]
            assert comment["razor"]["original"] == "Ko"
            assert comment["razor"]["normalized"] == "Koraat"
            assert comment["razor"]["overridden"] == "Normalized"
            assert comment["blade"]["normalized"] == "Feather"

    def test_run_extraction_for_month_without_overrides(self):
        """Test running extraction for month without overrides."""
        # Create temporary input file
        input_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Ko\n✓Blade: Feather",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(input_data, f)

            # Run extraction without override manager
            result = run_extraction_for_month("2025-01", str(temp_path), None)

            assert result is not None
            assert len(result["data"]) == 1
            comment = result["data"][0]
            assert comment["razor"]["original"] == "Ko"
            assert comment["razor"]["normalized"] == "Ko"
            assert "overridden" not in comment["razor"]
            assert comment["blade"]["normalized"] == "Feather"

    def test_override_multiple_fields_same_comment(self):
        """Test overriding multiple fields for the same comment."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "2025-01-15T10:00:00Z",
        }

        # Create override manager with multiple field overrides
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
    blade: "Gillette Minora Platinum"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            result = parse_comment(comment, override_manager, processing_month="2025-01")

            assert result is not None
            # Razor override
            assert result["razor"]["original"] == "Ko"
            assert result["razor"]["normalized"] == "Koraat"
            assert result["razor"]["overridden"] == "Normalized"
            # Blade override
            assert result["blade"]["original"] == "Feather"
            assert result["blade"]["normalized"] == "Gillette Minora Platinum"
            assert result["blade"]["overridden"] == "Normalized"

        finally:
            override_file.unlink()

    def test_override_different_month(self):
        """Test that overrides only apply to the correct month."""
        comment = {
            "id": "m99b8f9",
            "body": "✓Razor: Ko\n✓Blade: Feather",
            "created_utc": "2025-02-15T10:00:00Z",  # February, not January
        }

        # Create override manager with January overrides
        override_content = """
2025-01:
  m99b8f9:
    razor: Koraat
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(override_content)
            override_file = Path(f.name)

        try:
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Process as February, override is in January
            result = parse_comment(comment, override_manager, processing_month="2025-02")

            # Should not apply overrides since processing month is February, not January
            assert result is not None
            assert result["razor"]["original"] == "Ko"
            assert result["razor"]["normalized"] == "Ko"
            assert "overridden" not in result["razor"]

        finally:
            override_file.unlink()
