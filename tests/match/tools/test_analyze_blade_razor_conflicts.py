"""Tests for blade-razor conflict analysis tool."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from sotd.match.tools.analyzers.analyze_blade_razor_conflicts import (
    get_conflict_type,
    is_incompatible_format,
    main,
    process_file,
)


class TestBladeRazorConflictAnalysis:
    """Test blade-razor conflict analysis functionality."""

    def test_is_incompatible_format(self):
        """Test format incompatibility detection."""
        # Test incompatible combinations
        assert is_incompatible_format("DE", "AC") is True
        assert is_incompatible_format("AC", "DE") is True
        assert is_incompatible_format("GEM", "DE") is True
        assert is_incompatible_format("DE", "GEM") is True
        assert is_incompatible_format("DE", "CARTRIDGE") is True
        assert is_incompatible_format("INJECTOR", "DE") is True

        # Test compatible combinations (should return False)
        assert is_incompatible_format("DE", "DE") is False
        assert is_incompatible_format("AC", "AC") is False
        assert is_incompatible_format("GEM", "GEM") is False

        # Test unknown formats (should return False)
        assert is_incompatible_format("UNKNOWN", "DE") is False
        assert is_incompatible_format("DE", "UNKNOWN") is False
        assert is_incompatible_format("", "DE") is False
        assert is_incompatible_format("DE", "") is False

    def test_get_conflict_type(self):
        """Test conflict type description generation."""
        assert get_conflict_type("DE", "AC") == "DE blade with AC razor"
        assert get_conflict_type("GEM", "DE") == "GEM blade with DE razor"
        assert get_conflict_type("AC", "GEM") == "AC blade with GEM razor"

    def test_process_file_with_conflicts(self):
        """Test processing a file with format conflicts."""
        # Create test data with conflicts
        test_data = {
            "data": [
                {
                    "id": "test123",
                    "url": "https://reddit.com/r/wetshaving/comments/test123",
                    "author": "test_user1",
                    "blade": {
                        "original": "Feather AC blade",
                        "matched": {
                            "brand": "Feather",
                            "model": "AC",
                            "format": "AC",
                        },
                        "pattern": "feather.*ac",
                        "match_type": "regex",
                    },
                    "razor": {
                        "original": "Gillette Super Speed",
                        "matched": {
                            "brand": "Gillette",
                            "model": "Super Speed",
                            "format": "DE",
                        },
                        "pattern": "gillette.*super",
                        "match_type": "exact",
                    },
                },
                {
                    "id": "test456",
                    "url": "https://reddit.com/r/wetshaving/comments/test456",
                    "author": "test_user2",
                    "blade": {
                        "original": "Personna GEM PTFE",
                        "matched": {
                            "brand": "Personna",
                            "model": "GEM PTFE",
                            "format": "GEM",
                        },
                        "pattern": "personna.*gem",
                        "match_type": "exact",
                    },
                    "razor": {
                        "original": "Schick Injector",
                        "matched": {
                            "brand": "Schick",
                            "model": "Injector",
                            "format": "INJECTOR",
                        },
                        "pattern": "schick.*injector",
                        "match_type": "regex",
                    },
                },
                {
                    "id": "test789",
                    "url": "https://reddit.com/r/wetshaving/comments/test789",
                    "author": "test_user3",
                    "blade": {
                        "original": "Astra SP",
                        "matched": {
                            "brand": "Astra",
                            "model": "Superior Platinum",
                            "format": "DE",
                        },
                        "pattern": "astra.*sp",
                        "match_type": "exact",
                    },
                    "razor": {
                        "original": "Merkur 34C",
                        "matched": {
                            "brand": "Merkur",
                            "model": "34C",
                            "format": "DE",
                        },
                        "pattern": "merkur.*34c",
                        "match_type": "exact",
                    },
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            # Import the module to access global variables
            import sotd.match.tools.analyzers.analyze_blade_razor_conflicts as module

            # Reset global variables
            module.stats = {
                "total_records": 0,
                "records_with_blade": 0,
                "records_with_razor": 0,
                "records_with_both": 0,
                "conflicts_found": 0,
                "conflicts_by_type": {},
            }
            module.conflict_examples = []

            # Process the file
            process_file(temp_file)

            # Check results
            assert module.stats["total_records"] == 3
            assert module.stats["records_with_blade"] == 3
            assert module.stats["records_with_razor"] == 3
            assert module.stats["records_with_both"] == 3
            assert module.stats["conflicts_found"] == 2

            # Check conflict types
            assert "AC blade with DE razor" in module.stats["conflicts_by_type"]
            assert "GEM blade with INJECTOR razor" in module.stats["conflicts_by_type"]
            assert module.stats["conflicts_by_type"]["AC blade with DE razor"] == 1
            assert module.stats["conflicts_by_type"]["GEM blade with INJECTOR razor"] == 1

            # Check examples
            assert len(module.conflict_examples) == 2
            assert module.conflict_examples[0]["conflict_type"] == "AC blade with DE razor"
            assert module.conflict_examples[1]["conflict_type"] == "GEM blade with INJECTOR razor"

            # Check new fields for first example
            first_example = module.conflict_examples[0]
            assert first_example["comment_id"] == "test123"
            assert (
                first_example["comment_url"] == "https://reddit.com/r/wetshaving/comments/test123"
            )
            assert first_example["author"] == "test_user1"
            assert first_example["blade_pattern"] == "feather.*ac"
            assert first_example["blade_match_type"] == "regex"
            assert first_example["razor_pattern"] == "gillette.*super"
            assert first_example["razor_match_type"] == "exact"

            # Check new fields for second example
            second_example = module.conflict_examples[1]
            assert second_example["comment_id"] == "test456"
            assert (
                second_example["comment_url"] == "https://reddit.com/r/wetshaving/comments/test456"
            )
            assert second_example["author"] == "test_user2"
            assert second_example["blade_pattern"] == "personna.*gem"
            assert second_example["blade_match_type"] == "exact"
            assert second_example["razor_pattern"] == "schick.*injector"
            assert second_example["razor_match_type"] == "regex"

        finally:
            temp_file.unlink()

    def test_process_file_without_conflicts(self):
        """Test processing a file without format conflicts."""
        # Create test data without conflicts
        test_data = {
            "data": [
                {
                    "id": "test999",
                    "url": "https://reddit.com/r/wetshaving/comments/test999",
                    "author": "test_user4",
                    "blade": {
                        "original": "Astra SP",
                        "matched": {
                            "brand": "Astra",
                            "model": "Superior Platinum",
                            "format": "DE",
                        },
                        "pattern": "astra.*sp",
                        "match_type": "exact",
                    },
                    "razor": {
                        "original": "Merkur 34C",
                        "matched": {
                            "brand": "Merkur",
                            "model": "34C",
                            "format": "DE",
                        },
                        "pattern": "merkur.*34c",
                        "match_type": "exact",
                    },
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = Path(f.name)

        try:
            # Import the module to access global variables
            import sotd.match.tools.analyzers.analyze_blade_razor_conflicts as module

            # Reset global variables
            module.stats = {
                "total_records": 0,
                "records_with_blade": 0,
                "records_with_razor": 0,
                "records_with_both": 0,
                "conflicts_found": 0,
                "conflicts_by_type": {},
            }
            module.conflict_examples = []

            # Process the file
            process_file(temp_file)

            # Check results
            assert module.stats["total_records"] == 1
            assert module.stats["records_with_blade"] == 1
            assert module.stats["records_with_razor"] == 1
            assert module.stats["records_with_both"] == 1
            assert module.stats["conflicts_found"] == 0
            assert len(module.conflict_examples) == 0

        finally:
            temp_file.unlink()

    @patch("sotd.match.tools.analyzers.analyze_blade_razor_conflicts.month_span")
    @patch("sotd.match.tools.analyzers.analyze_blade_razor_conflicts.get_files_for_months")
    @patch("sotd.match.tools.analyzers.analyze_blade_razor_conflicts.process_file")
    def test_main_with_valid_args(self, mock_process_file, mock_get_files, mock_month_span):
        """Test main function with valid arguments."""
        # Mock return values
        mock_month_span.return_value = [(2024, 1)]
        mock_get_files.return_value = [Path("test.json")]

        # Test with --month argument
        with patch("sys.argv", ["script", "--month", "2024-01"]):
            main()

        # Verify calls
        mock_month_span.assert_called_once()
        mock_get_files.assert_called_once_with([(2024, 1)])
        mock_process_file.assert_called_once_with(Path("test.json"))

    @patch("sotd.match.tools.analyzers.analyze_blade_razor_conflicts.month_span")
    def test_main_with_invalid_args(self, mock_month_span):
        """Test main function with invalid arguments."""
        # Mock ValueError
        mock_month_span.side_effect = ValueError("Invalid date format")

        # Test with invalid --month argument
        with patch("sys.argv", ["script", "--month", "invalid"]):
            with patch("builtins.print") as mock_print:
                main()
                mock_print.assert_called_with("Error: Invalid date format")
