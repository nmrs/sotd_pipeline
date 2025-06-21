"""Integration tests for match CLI functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from sotd.match.cli import get_parser
from sotd.match.run import main


class TestMatchCLI:
    """Test match CLI argument parsing and validation."""

    def test_get_parser_creates_parser(self):
        """Test that get_parser returns a valid ArgumentParser."""
        parser = get_parser()
        assert parser is not None
        assert (
            parser.description
            == "Match razors, blades, soaps, and brushes from extracted SOTD data"
        )

    def test_month_argument_validation_valid(self):
        """Test valid month argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.month == "2023-01"
        assert args.year is None
        assert args.range is None

    def test_month_argument_validation_invalid_format(self):
        """Test invalid month format raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023/01"])

    def test_month_argument_validation_invalid_month(self):
        """Test invalid month value raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-13"])

    def test_year_argument_validation_valid(self):
        """Test valid year argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2023"])
        assert args.year == "2023"
        assert args.month is None
        assert args.range is None

    def test_year_argument_validation_invalid(self):
        """Test invalid year format raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--year", "23"])

    def test_range_argument_validation_valid(self):
        """Test valid range argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2023-01:2023-03"])
        assert args.range == "2023-01:2023-03"
        assert args.month is None
        assert args.year is None

    def test_range_argument_validation_invalid_format(self):
        """Test invalid range format raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--range", "2023-01-2023-03"])

    def test_range_argument_validation_invalid_month(self):
        """Test invalid month in range raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--range", "2023-13:2023-03"])

    def test_start_end_arguments_valid(self):
        """Test valid start/end argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2023-01", "--end", "2023-03"])
        assert args.start == "2023-01"
        assert args.end == "2023-03"
        assert args.month is None
        assert args.year is None
        assert args.range is None

    def test_start_end_arguments_missing_start(self):
        """Test missing start argument raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--end", "2023-03"])

    def test_start_end_arguments_missing_end(self):
        """Test missing end argument raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--start", "2023-01"])

    def test_mutually_exclusive_date_arguments(self):
        """Test that date arguments are mutually exclusive."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--year", "2023"])

    def test_no_date_arguments_sets_default(self):
        """Test that no date arguments sets default month."""
        parser = get_parser()
        args = parser.parse_args([])
        # Should not raise any exception, should set default month
        assert args.month is not None
        assert "-" in args.month

    def test_out_dir_argument_default(self):
        """Test out-dir argument default value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.out_dir == Path("data")

    def test_out_dir_argument_custom(self):
        """Test custom out-dir argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--out-dir", "/custom/path"])
        assert args.out_dir == Path("/custom/path")

    def test_debug_argument(self):
        """Test debug argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--debug"])
        assert args.debug is True

    def test_force_argument(self):
        """Test force argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--force"])
        assert args.force is True

    def test_mode_argument_default(self):
        """Test mode argument default value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.mode == "match"

    def test_mode_argument_custom(self):
        """Test custom mode argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--mode", "analyze_unmatched_razors"])
        assert args.mode == "analyze_unmatched_razors"

    def test_mode_argument_invalid(self):
        """Test invalid mode argument raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--mode", "invalid_mode"])

    def test_parallel_processing_arguments(self):
        """Test parallel processing argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--parallel"])
        assert args.parallel is True
        assert args.sequential is False

    def test_sequential_processing_arguments(self):
        """Test sequential processing argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--sequential"])
        assert args.sequential is True
        assert args.parallel is False

    def test_max_workers_argument_default(self):
        """Test max-workers argument default value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.max_workers == 4

    def test_max_workers_argument_custom(self):
        """Test custom max-workers argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--max-workers", "8"])
        assert args.max_workers == 8

    def test_parallel_sequential_mutually_exclusive(self):
        """Test that parallel and sequential are mutually exclusive."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--parallel", "--sequential"])


class TestMatchMain:
    """Test match main function integration."""

    @patch("sotd.match.run.run_match")
    def test_main_with_match_mode(self, mock_run_match):
        """Test main function with match mode."""
        with patch("sys.argv", ["match", "--month", "2023-01"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_analysis")
    def test_main_with_analyze_mode(self, mock_run_analysis):
        """Test main function with analyze mode."""
        with patch(
            "sys.argv", ["match", "--month", "2023-01", "--mode", "analyze_unmatched_razors"]
        ):
            main()

        mock_run_analysis.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_year(self, mock_run_match):
        """Test main function with year argument."""
        with patch("sys.argv", ["match", "--year", "2023"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_range(self, mock_run_match):
        """Test main function with range argument."""
        with patch("sys.argv", ["match", "--range", "2023-01:2023-03"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_start_end(self, mock_run_match):
        """Test main function with start/end arguments."""
        with patch("sys.argv", ["match", "--start", "2023-01", "--end", "2023-03"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_debug_and_force(self, mock_run_match):
        """Test main function with debug and force flags."""
        with patch("sys.argv", ["match", "--month", "2023-01", "--debug", "--force"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_parallel_processing(self, mock_run_match):
        """Test main function with parallel processing."""
        with patch("sys.argv", ["match", "--month", "2023-01", "--parallel", "--max-workers", "8"]):
            main()

        mock_run_match.assert_called_once()

    @patch("sotd.match.run.run_match")
    def test_main_with_sequential_processing(self, mock_run_match):
        """Test main function with sequential processing."""
        with patch("sys.argv", ["match", "--month", "2023-01", "--sequential"]):
            main()

        mock_run_match.assert_called_once()
