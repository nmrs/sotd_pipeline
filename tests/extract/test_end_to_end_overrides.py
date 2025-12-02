#!/usr/bin/env python3
"""End-to-end tests for the complete override workflow."""

import json
import tempfile
from pathlib import Path

import pytest

from sotd.extract.comment import run_extraction_for_month
from sotd.extract.override_manager import OverrideManager


class TestEndToEndOverrides:
    """End-to-end tests for the complete override workflow."""

    def test_complete_override_workflow_with_real_data_structure(self):
        """Test complete override workflow using realistic SOTD data structure."""
        # Create realistic SOTD comment data
        comments_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Ko\n✓Blade: Feather\n✓Soap: Declaration Grooming",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user_1",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f9/",
                },
                {
                    "id": "m99b8f0",
                    "body": "✓Blade: Gillette Minora\n✓Brush: Semogue",
                    "created_utc": "2025-01-16T10:00:00Z",
                    "author": "test_user_2",
                    "thread_id": "t124",
                    "thread_title": "SOTD January 16, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t124/sotd_january_16_2025/m99b8f0/",
                },
                {
                    "id": "m99b8f1",
                    "body": "✓Razor: Rockwell\n✓Soap: Declaration",
                    "created_utc": "2025-01-17T10:00:00Z",
                    "author": "test_user_3",
                    "thread_id": "t125",
                    "thread_title": "SOTD January 17, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t125/sotd_january_17_2025/m99b8f1/",
                },
            ]
        }

        # Create override file with corrections
        override_content = """
2025-01:
  m99b8f9:
    razor: "Koraat"  # Fix "Ko" -> "Koraat"
    soap: "Declaration Grooming - Seville"  # Add missing soap name
  m99b8f0:
    razor: "Feather Artist Club"  # Add missing razor field
    blade: "Gillette Minora Platinum"  # Fix blade name
  m99b8f1:
    razor: "Rockwell 6S"  # Fix razor model
    soap: "Declaration Grooming - Massacre of the Innocents"  # Fix soap name
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Create override file
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write(override_content)

            # Create override manager and load overrides
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Verify overrides were loaded correctly
            assert override_manager.has_overrides()
            summary = override_manager.get_override_summary()
            assert summary["total_overrides"] == 6
            assert summary["months_with_overrides"] == 1
            assert summary["month_counts"]["2025-01"] == 6

            # Run extraction with overrides
            result = run_extraction_for_month("2025-01", str(temp_path), override_manager)

            assert result is not None
            assert len(result["data"]) == 3

            # Verify first comment overrides
            comment1 = result["data"][0]
            assert comment1["id"] == "m99b8f9"
            assert comment1["razor"]["original"] == "Ko"  # Preserved
            assert comment1["razor"]["normalized"] == "Koraat"  # Overridden
            assert comment1["razor"]["overridden"] == "Normalized"
            assert comment1["soap"]["original"] == "Declaration Grooming"  # Preserved
            assert comment1["soap"]["normalized"] == "Declaration Grooming - Seville"  # Overridden
            assert comment1["soap"]["overridden"] == "Normalized"
            assert comment1["blade"]["normalized"] == "Feather"  # Unchanged
            assert "overridden" not in comment1["blade"]

            # Verify second comment overrides (missing field creation)
            comment2 = result["data"][1]
            assert comment2["id"] == "m99b8f0"
            assert comment2["razor"]["original"] == "Feather Artist Club"  # Created from override
            assert comment2["razor"]["normalized"] == "Feather Artist Club"  # Created from override
            assert comment2["razor"]["overridden"] == "Original,Normalized"
            assert comment2["blade"]["original"] == "Gillette Minora"  # Preserved
            assert comment2["blade"]["normalized"] == "Gillette Minora Platinum"  # Overridden
            assert comment2["blade"]["overridden"] == "Normalized"

            # Verify third comment overrides
            comment3 = result["data"][2]
            assert comment3["id"] == "m99b8f1"
            assert comment3["razor"]["original"] == "Rockwell"  # Preserved
            assert comment3["razor"]["normalized"] == "Rockwell 6S"  # Overridden
            assert comment3["razor"]["overridden"] == "Normalized"
            assert comment3["soap"]["original"] == "Declaration"  # Preserved
            assert (
                comment3["soap"]["normalized"] == "Declaration Grooming - Massacre of the Innocents"
            )  # Overridden
            assert comment3["soap"]["overridden"] == "Normalized"

    def test_override_workflow_without_overrides(self):
        """Test that extraction works normally when no overrides are present."""
        # Create realistic SOTD comment data
        comments_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Koraat\n✓Blade: Feather\n✓Soap: Declaration Grooming - Seville",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user_1",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f9/",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Run extraction without override manager
            result = run_extraction_for_month("2025-01", str(temp_path), None)

            assert result is not None
            assert len(result["data"]) == 1

            comment = result["data"][0]
            assert comment["id"] == "m99b8f9"
            assert comment["razor"]["normalized"] == "Koraat"
            assert comment["blade"]["normalized"] == "Feather"
            assert comment["soap"]["normalized"] == "Declaration Grooming - Seville"

            # Verify no override flags are present
            assert "overridden" not in comment["razor"]
            assert "overridden" not in comment["blade"]
            assert "overridden" not in comment["soap"]

    def test_override_workflow_with_empty_override_file(self):
        """Test that extraction works with an empty override file."""
        # Create realistic SOTD comment data
        comments_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Koraat\n✓Blade: Feather",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user_1",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f9/",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Create empty override file
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write("")  # Empty file

            # Create override manager and load overrides
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Verify no overrides were loaded
            assert not override_manager.has_overrides()

            # Run extraction with empty override manager
            result = run_extraction_for_month("2025-01", str(temp_path), override_manager)

            assert result is not None
            assert len(result["data"]) == 1

            comment = result["data"][0]
            assert comment["id"] == "m99b8f9"
            assert comment["razor"]["normalized"] == "Koraat"
            assert comment["blade"]["normalized"] == "Feather"

            # Verify no override flags are present
            assert "overridden" not in comment["razor"]
            assert "overridden" not in comment["blade"]

    def test_override_workflow_with_invalid_override_file(self):
        """Test that extraction fails gracefully with invalid override file."""
        # Create realistic SOTD comment data
        comments_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Koraat",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user_1",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f9/",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Create invalid override file
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write("invalid: yaml: content")

            # Create override manager and attempt to load overrides
            override_manager = OverrideManager(override_file)

            # Should raise ValueError due to invalid YAML
            with pytest.raises(ValueError, match="Invalid YAML syntax"):
                override_manager.load_overrides()

    def test_override_workflow_with_missing_comment_ids(self):
        """Test that validation fails when override references non-existent comment IDs."""
        # Create realistic SOTD comment data
        comments_data = {
            "data": [
                {
                    "id": "m99b8f9",
                    "body": "✓Razor: Koraat",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": "test_user_1",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": "https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f9/",
                }
            ]
        }

        # Create override file with non-existent comment ID
        override_content = """
2025-01:
  nonexistent_id:
    razor: "Koraat"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Create override file
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write(override_content)

            # Create override manager and load overrides
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Validation should fail when checking against actual data
            with pytest.raises(ValueError, match="non-existent comment IDs"):
                override_manager.validate_overrides(comments_data["data"])

    def test_override_workflow_performance_impact(self):
        """Test that overrides don't significantly impact extraction performance."""
        import time

        # Create realistic SOTD comment data with multiple comments
        comments_data = {
            "data": [
                {
                    "id": f"m99b8f{i:02d}",
                    "body": f"✓Razor: Test Razor {i}\n✓Blade: Test Blade {i}",
                    "created_utc": "2025-01-15T10:00:00Z",
                    "author": f"test_user_{i}",
                    "thread_id": "t123",
                    "thread_title": "SOTD January 15, 2025",
                    "url": f"https://reddit.com/r/wetshaving/comments/t123/sotd_january_15_2025/m99b8f{i:02d}/",
                }
                for i in range(100)  # 100 comments
            ]
        }

        # Create override file with some overrides
        override_content = """
2025-01:
  m99b8f00:
    razor: "Corrected Razor 0"
  m99b8f50:
    blade: "Corrected Blade 50"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create input data directory structure
            comments_dir = temp_path / "comments"
            comments_dir.mkdir()

            # Create input file
            input_file = comments_dir / "2025-01.json"
            with open(input_file, "w") as f:
                json.dump(comments_data, f, indent=2)

            # Create override file
            override_file = temp_path / "overrides.yaml"
            with open(override_file, "w") as f:
                f.write(override_content)

            # Create override manager
            override_manager = OverrideManager(override_file)
            override_manager.load_overrides()

            # Time extraction without overrides
            start_time = time.time()
            result_no_overrides = run_extraction_for_month("2025-01", str(temp_path), None)
            time_no_overrides = time.time() - start_time

            # Time extraction with overrides
            start_time = time.time()
            result_with_overrides = run_extraction_for_month(
                "2025-01", str(temp_path), override_manager
            )
            time_with_overrides = time.time() - start_time

            # Verify both extractions produced the same number of results
            assert result_no_overrides is not None
            assert result_with_overrides is not None
            assert result_no_overrides.get("data") is not None
            assert result_with_overrides.get("data") is not None
            assert len(result_no_overrides["data"]) == 100
            assert len(result_with_overrides["data"]) == 100

            # Performance impact should be reasonable (< 50% overhead for small datasets)
            # For larger datasets, the overhead would be proportionally smaller
            performance_ratio = time_with_overrides / time_no_overrides
            assert performance_ratio < 1.5, f"Performance impact too high: {performance_ratio:.2f}x"

            # Verify overrides were applied correctly
            assert result_with_overrides is not None
            data = result_with_overrides.get("data")
            assert data is not None
            comment0 = data[0]
            assert isinstance(comment0, dict)
            assert comment0.get("razor") is not None
            assert isinstance(comment0["razor"], dict)
            assert comment0["razor"]["normalized"] == "Corrected Razor 0"
            assert comment0["razor"]["overridden"] == "Normalized"

            comment50 = data[50]
            assert isinstance(comment50, dict)
            assert comment50.get("blade") is not None
            assert isinstance(comment50["blade"], dict)
            assert comment50["blade"]["normalized"] == "Corrected Blade 50"
            assert comment50["blade"]["overridden"] == "Normalized"
