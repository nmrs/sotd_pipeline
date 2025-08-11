"""Test brush CLI validation interface."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import io

from sotd.match.brush_validation_cli import (
    BrushValidationCLI,
    setup_validation_cli,
    main as cli_main,
)
from sotd.match.brush_user_actions import BrushUserActionsManager


class TestBrushValidationCLI:
    """Test BrushValidationCLI class."""

    def setup_method(self):
        """Set up test directory and CLI instance."""
        self.test_dir = tempfile.mkdtemp()
        self.cli = BrushValidationCLI(data_path=Path(self.test_dir))

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test CLI initialization with entry point integration."""
        assert self.cli.data_path == Path(self.test_dir)
        assert isinstance(self.cli.user_actions_manager, BrushUserActionsManager)
        assert hasattr(self.cli, "brush_entry_point")

    @patch("sotd.match.brush_validation_cli.load_json_data")
    def test_load_month_data_legacy_system(self, mock_load_json):
        """Test loading monthly data for legacy system."""
        # Mock data structure - records with brush field
        mock_data = {
            "data": [
                {
                    "id": "comment1",
                    "brush": {
                        "original": "Test Brush 1",
                        "matched": {"brand": "Test", "model": "Brush1"},
                        "match_type": "regex",
                    },
                },
                {
                    "id": "comment2",
                    "brush": {
                        "original": "Test Brush 2",
                        "matched": None,
                        "match_type": "no_match",
                    },
                },
            ]
        }
        mock_load_json.return_value = mock_data

        result = self.cli.load_month_data("2025-08", "legacy")

        assert len(result) == 2
        assert result[0]["input_text"] == "Test Brush 1"
        assert result[0]["system_used"] == "legacy"
        assert result[0]["matched"] == {"brand": "Test", "model": "Brush1"}

        mock_load_json.assert_called_once()

    @patch("sotd.match.brush_validation_cli.load_json_data")
    def test_load_month_data_scoring_system(self, mock_load_json):
        """Test loading monthly data for scoring system."""
        # Mock data structure - records with brush field
        mock_data = {
            "data": [
                {
                    "id": "comment1",
                    "brush": {
                        "original": "Test Brush 1",
                        "normalized": "test brush 1",
                        "matched": {
                            "strategy": "dual_component",
                            "score": 85,
                            "result": {"brand": "Test", "model": "Brush1"},
                        },
                        "all_strategies": [
                            {"strategy": "complete_brush", "score": 45, "result": {}},
                            {"strategy": "dual_component", "score": 85, "result": {}},
                        ],
                    },
                }
            ]
        }
        mock_load_json.return_value = mock_data

        result = self.cli.load_month_data("2025-08", "scoring")

        assert len(result) == 1
        assert result[0]["input_text"] == "Test Brush 1"
        assert result[0]["system_used"] == "scoring"
        assert result[0]["matched"]["strategy"] == "dual_component"
        assert result[0]["matched"]["score"] == 85

    def test_sort_entries_by_unvalidated(self):
        """Test sorting entries by unvalidated status."""
        # Create mock entries with some validated actions
        entries = [
            {"input_text": "Validated Brush", "system_used": "scoring"},
            {"input_text": "Unvalidated Brush 1", "system_used": "scoring"},
            {"input_text": "Unvalidated Brush 2", "system_used": "legacy"},
        ]

        # Mock some existing validations
        with patch.object(self.cli.user_actions_manager, "get_monthly_actions") as mock_get_actions:
            mock_actions = [Mock(input_text="Validated Brush", action="validated")]
            mock_get_actions.return_value = mock_actions

            sorted_entries = self.cli.sort_entries(entries, "2025-08", "unvalidated")

            # Unvalidated should come first
            assert len(sorted_entries) == 3
            assert sorted_entries[0]["input_text"] == "Unvalidated Brush 1"
            assert sorted_entries[1]["input_text"] == "Unvalidated Brush 2"
            assert sorted_entries[2]["input_text"] == "Validated Brush"

    def test_sort_entries_by_validated(self):
        """Test sorting entries by validated status."""
        entries = [
            {"input_text": "Unvalidated Brush", "system_used": "scoring"},
            {"input_text": "Validated Brush", "system_used": "scoring"},
        ]

        with patch.object(self.cli.user_actions_manager, "get_monthly_actions") as mock_get_actions:
            mock_actions = [Mock(input_text="Validated Brush", action="validated")]
            mock_get_actions.return_value = mock_actions

            sorted_entries = self.cli.sort_entries(entries, "2025-08", "validated")

            # Validated should come first
            assert sorted_entries[0]["input_text"] == "Validated Brush"
            assert sorted_entries[1]["input_text"] == "Unvalidated Brush"

    def test_sort_entries_by_ambiguity(self):
        """Test sorting entries by ambiguity (score difference)."""
        entries = [
            {
                "input_text": "Clear Winner",
                "system_used": "scoring",
                "all_strategies": [
                    {"strategy": "complete_brush", "score": 95},
                    {"strategy": "dual_component", "score": 45},
                ],
            },
            {
                "input_text": "Ambiguous Case",
                "system_used": "scoring",
                "all_strategies": [
                    {"strategy": "complete_brush", "score": 75},
                    {"strategy": "dual_component", "score": 70},
                ],
            },
        ]

        sorted_entries = self.cli.sort_entries(entries, "2025-08", "ambiguity")

        # Most ambiguous (smallest score difference) should come first
        assert sorted_entries[0]["input_text"] == "Ambiguous Case"
        assert sorted_entries[1]["input_text"] == "Clear Winner"

    def test_display_entry(self):
        """Test displaying entry information."""
        entry = {
            "input_text": "Test Brush",
            "system_used": "scoring",
            "best_result": {
                "strategy": "dual_component",
                "score": 85,
                "result": {
                    "brand": "Test",
                    "model": "Brush",
                    "handle": {"brand": "Test", "model": "Handle"},
                    "knot": {"brand": "Test", "model": "Knot"},
                },
            },
            "all_strategies": [
                {"strategy": "complete_brush", "score": 45, "result": {}},
                {"strategy": "dual_component", "score": 85, "result": {}},
            ],
        }

        # Capture output
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            self.cli.display_entry(entry, 1, 10)

        output = captured_output.getvalue()
        assert "Entry 1/10" in output
        assert "Test Brush" in output
        assert "dual_component" in output
        assert "Score: 85" in output

    def test_get_user_choice_validate(self):
        """Test user choice validation."""
        entry = {
            "input_text": "Test Brush",
            "system_used": "scoring",
            "best_result": {"strategy": "dual_component", "score": 85, "result": {}},
        }

        with patch("builtins.input", return_value="v"):
            action, choice = self.cli.get_user_choice(entry)

            assert action == "validate"
            assert choice == entry["best_result"]

    def test_get_user_choice_override(self):
        """Test user choice override."""
        entry = {
            "input_text": "Test Brush",
            "system_used": "scoring",
            "best_result": {"strategy": "dual_component", "score": 85, "result": {}},
            "all_strategies": [
                {"strategy": "complete_brush", "score": 45, "result": {"brand": "Override"}},
                {"strategy": "dual_component", "score": 85, "result": {"brand": "Original"}},
            ],
        }

        # Mock user selecting option 1 (complete_brush)
        with patch("builtins.input", side_effect=["o", "1"]):
            action, choice = self.cli.get_user_choice(entry)

            assert action == "override"
            assert choice["strategy"] == "complete_brush"
            assert choice["result"]["brand"] == "Override"

    def test_record_user_action_validation(self):
        """Test recording user validation action."""
        entry = {
            "input_text": "Test Brush",
            "system_used": "scoring",
            "best_result": {"strategy": "dual_component", "score": 85, "result": {}},
            "all_strategies": [],
            "comment_ids": [],
        }

        with patch.object(self.cli.user_actions_manager, "record_validation") as mock_record:
            self.cli.record_user_action(entry, "validate", entry["best_result"], "2025-08")

            mock_record.assert_called_once_with(
                input_text="Test Brush",
                month="2025-08",
                system_used="scoring",
                system_choice=entry["best_result"],
                user_choice=entry["best_result"],
                all_brush_strategies=[],
                comment_ids=[],
            )

    def test_record_user_action_override(self):
        """Test recording user override action."""
        entry = {
            "input_text": "Test Brush",
            "system_used": "scoring",
            "best_result": {"strategy": "dual_component", "score": 85, "result": {}},
            "all_strategies": [],
            "comment_ids": [],
        }

        override_choice = {"strategy": "complete_brush", "score": 45, "result": {}}

        with patch.object(self.cli.user_actions_manager, "record_override") as mock_record:
            self.cli.record_user_action(entry, "override", override_choice, "2025-08")

            mock_record.assert_called_once_with(
                input_text="Test Brush",
                month="2025-08",
                system_used="scoring",
                system_choice=entry["best_result"],
                user_choice=override_choice,
                all_brush_strategies=[],
                comment_ids=[],
            )

    def test_get_validation_statistics(self):
        """Test getting validation statistics."""
        # Mock the load_month_data method to return specific data
        with patch.object(self.cli, "load_month_data") as mock_load:
            # Mock scoring system data with some duplicate brush strings
            mock_load.return_value = [
                {"input_text": "Brush A", "normalized_text": "brush a"},
                {"input_text": "Brush B", "normalized_text": "brush b"},
                {"input_text": "Brush A", "normalized_text": "brush a"},  # Duplicate
                {"input_text": "Brush C", "normalized_text": "brush c"},
            ]

            # Mock user actions
            with patch.object(self.cli.user_actions_manager, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_actions": 2,
                    "validated_count": 1,
                    "overridden_count": 1,
                    "validation_rate": 0.5,
                }

                stats = self.cli.get_validation_statistics("2025-08")

                # Should count unique brush strings (3 unique, not 4 total)
                assert stats["total_entries"] == 3  # 3 unique brush strings
                assert stats["validated_count"] == 1
                assert stats["overridden_count"] == 1
                assert stats["unvalidated_count"] == 1  # 3 total - 2 actions
                assert stats["validation_rate"] == 2 / 3  # 2 actions / 3 entries

    def test_get_validation_statistics_no_matcher(self):
        """Test getting validation statistics without matcher."""
        # Mock the load_month_data method to return specific data
        with patch.object(self.cli, "load_month_data") as mock_load:
            # Mock scoring system data with some duplicate brush strings
            mock_load.return_value = [
                {"input_text": "Brush A", "normalized_text": "brush a"},
                {"input_text": "Brush B", "normalized_text": "brush b"},
                {"input_text": "Brush A", "normalized_text": "brush a"},  # Duplicate
                {"input_text": "Brush C", "normalized_text": "brush c"},
            ]

            # Mock user actions
            with patch.object(self.cli.user_actions_manager, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_actions": 2,
                    "validated_count": 1,
                    "overridden_count": 1,
                    "validation_rate": 0.5,
                }

                stats = self.cli.get_validation_statistics_no_matcher("2025-08")

                # Should count unique brush strings (3 unique, not 4 total)
                assert stats["total_entries"] == 3  # 3 unique brush strings
                assert stats["validated_count"] == 1
                assert stats["overridden_count"] == 1
                assert stats["unvalidated_count"] == 1  # 3 total - 2 actions
                assert stats["validation_rate"] == 2 / 3  # 2 actions / 3 entries

    def test_get_validation_statistics_unique_strings_only(self):
        """Test that statistics only count unique brush strings."""
        with patch.object(self.cli, "load_month_data") as mock_load:
            # Mock data with many duplicates but only 2 unique strings
            mock_load.return_value = [
                {"input_text": "Same Brush", "normalized_text": "same brush"},
                {"input_text": "Same Brush", "normalized_text": "same brush"},  # Duplicate
                {"input_text": "Same Brush", "normalized_text": "same brush"},  # Duplicate
                {"input_text": "Another Brush", "normalized_text": "another brush"},
                {"input_text": "Same Brush", "normalized_text": "same brush"},  # Duplicate
            ]

            with patch.object(self.cli.user_actions_manager, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_actions": 0,
                    "validated_count": 0,
                    "overridden_count": 0,
                    "validation_rate": 0.0,
                }

                stats = self.cli.get_validation_statistics("2025-08")

                # Should only count 2 unique brush strings, not 5 total entries
                assert stats["total_entries"] == 2
                assert stats["unvalidated_count"] == 2

    def test_get_validation_statistics_case_insensitive(self):
        """Test that statistics handle case-insensitive unique counting."""
        with patch.object(self.cli, "load_month_data") as mock_load:
            # Mock data with same brush in different cases
            mock_load.return_value = [
                {"input_text": "Test Brush", "normalized_text": "test brush"},
                {"input_text": "TEST BRUSH", "normalized_text": "TEST BRUSH"},
                {"input_text": "Test brush", "normalized_text": "Test brush"},
            ]

            with patch.object(self.cli.user_actions_manager, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_actions": 0,
                    "validated_count": 0,
                    "overridden_count": 0,
                    "validation_rate": 0.0,
                }

                stats = self.cli.get_validation_statistics("2025-08")

                # Should count as 1 unique brush string (case-insensitive)
                assert stats["total_entries"] == 1
                assert stats["unvalidated_count"] == 1

    def test_get_validation_statistics_fallback_to_input_text(self):
        """Test that statistics fallback to input_text when normalized_text is missing."""
        with patch.object(self.cli, "load_month_data") as mock_load:
            # Mock data with missing normalized_text
            mock_load.return_value = [
                {"input_text": "Brush A"},  # No normalized_text
                {"input_text": "Brush B", "normalized_text": "brush b"},
                {"input_text": "Brush A"},  # No normalized_text, duplicate
            ]

            with patch.object(self.cli.user_actions_manager, "get_statistics") as mock_stats:
                mock_stats.return_value = {
                    "total_actions": 0,
                    "validated_count": 0,
                    "overridden_count": 0,
                    "validation_rate": 0.0,
                }

                stats = self.cli.get_validation_statistics("2025-08")

                # Should count 2 unique brush strings
                assert stats["total_entries"] == 2
                assert stats["unvalidated_count"] == 2

    @patch.object(BrushValidationCLI, "load_month_data")
    @patch.object(BrushValidationCLI, "sort_entries")
    @patch.object(BrushValidationCLI, "get_validation_statistics")
    def test_run_validation_workflow(self, mock_stats, mock_sort, mock_load):
        """Test running complete validation workflow."""
        # Mock data
        mock_entries = [{"input_text": "Test Brush", "system_used": "scoring"}]
        mock_load.return_value = mock_entries
        mock_sort.return_value = mock_entries
        mock_stats.return_value = {
            "total_entries": 1,
            "validated_count": 0,
            "overridden_count": 0,
            "total_actions": 0,
            "unvalidated_count": 1,
            "validation_rate": 0.0,
        }

        # Mock user input to quit immediately
        with patch("builtins.input", return_value="q"):
            with patch("sys.stdout", io.StringIO()):
                result = self.cli.run_validation_workflow("2025-08", "scoring", "unvalidated")

                assert result == {"completed": False, "entries_processed": 0}
                mock_load.assert_called_once_with("2025-08", "scoring")
                mock_sort.assert_called_once_with(mock_entries, "2025-08", "unvalidated")


class TestBrushValidationCLISetup:
    """Test CLI setup and argument parsing."""

    def test_setup_validation_cli(self):
        """Test CLI parser setup."""
        parser = setup_validation_cli()

        # Test default arguments
        args = parser.parse_args(["--month", "2025-08"])
        assert args.system == "both"
        assert args.sort_by == "unvalidated"
        assert args.month == "2025-08"

        # Test custom arguments
        args = parser.parse_args(
            ["--month", "2025-07", "--system", "scoring", "--sort-by", "ambiguity"]
        )
        assert args.system == "scoring"
        assert args.sort_by == "ambiguity"
        assert args.month == "2025-07"

    def test_invalid_system_choice(self):
        """Test invalid system choice handling."""
        parser = setup_validation_cli()

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-08", "--system", "invalid"])

    def test_invalid_sort_choice(self):
        """Test invalid sort choice handling."""
        parser = setup_validation_cli()

        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2025-08", "--sort-by", "invalid"])

    def test_missing_month_argument(self):
        """Test missing required month argument."""
        parser = setup_validation_cli()

        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestBrushValidationCLIMain:
    """Test CLI main function."""

    @patch("sotd.match.brush_validation_cli.BrushValidationCLI")
    def test_main_function_scoring_system(self, mock_cli_class):
        """Test main function with scoring system."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        mock_cli.run_validation_workflow.return_value = {"completed": True, "entries_processed": 5}

        test_args = ["--month", "2025-08", "--system", "scoring", "--sort-by", "ambiguity"]

        with patch("sys.argv", ["brush_validation_cli.py"] + test_args):
            with patch("sys.stdout", io.StringIO()):
                cli_main()

        mock_cli.run_validation_workflow.assert_called_once_with("2025-08", "scoring", "ambiguity")

    @patch("sotd.match.brush_validation_cli.BrushValidationCLI")
    def test_main_function_both_systems(self, mock_cli_class):
        """Test main function with both systems."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        mock_cli.run_validation_workflow.return_value = {"completed": True, "entries_processed": 3}

        test_args = ["--month", "2025-08", "--system", "both"]

        with patch("sys.argv", ["brush_validation_cli.py"] + test_args):
            with patch("sys.stdout", io.StringIO()):
                cli_main()

        # Should be called twice for both systems
        assert mock_cli.run_validation_workflow.call_count == 2

    @patch("sotd.match.brush_validation_cli.BrushValidationCLI")
    def test_main_function_exception_handling(self, mock_cli_class):
        """Test main function exception handling."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        mock_cli.run_validation_workflow.side_effect = Exception("Test error")

        test_args = ["--month", "2025-08"]

        with patch("sys.argv", ["brush_validation_cli.py"] + test_args):
            with patch("sys.stderr", io.StringIO()) as captured_stderr:
                with pytest.raises(SystemExit):
                    cli_main()

                assert "Error" in captured_stderr.getvalue()
