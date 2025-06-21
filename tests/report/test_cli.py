"""Integration tests for report CLI functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from sotd.report.cli import get_parser, get_default_month, validate_args
from sotd.report.run import main


class TestReportCLI:
    """Test report CLI argument parsing and validation."""

    def test_get_parser_creates_parser(self):
        """Test that get_parser returns a valid ArgumentParser."""
        parser = get_parser()
        assert parser is not None
        assert (
            parser.description == "Generate statistical analysis reports from aggregated SOTD data"
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

    def test_data_root_argument_default(self):
        """Test data-root argument default value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.data_root == Path("data")

    def test_data_root_argument_custom(self):
        """Test custom data-root argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--data-root", "/custom/data"])
        assert args.data_root == Path("/custom/data")

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

    def test_type_argument_default(self):
        """Test type argument default value."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.type == "hardware"

    def test_type_argument_hardware(self):
        """Test hardware type argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--type", "hardware"])
        assert args.type == "hardware"

    def test_type_argument_software(self):
        """Test software type argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--type", "software"])
        assert args.type == "software"

    def test_type_argument_invalid(self):
        """Test invalid type argument raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--type", "invalid"])


class TestReportCLIValidation:
    """Test report CLI validation logic."""

    def test_validate_args_with_month(self):
        """Test validation with valid month argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        # Should not raise any exception
        validate_args(args)
        assert args.month == "2023-01"

    def test_validate_args_no_date_sets_default(self):
        """Test validation sets default month when no date provided."""
        parser = get_parser()
        args = parser.parse_args([])
        # Should not raise any exception, should set default month
        assert args.month is not None
        assert "-" in args.month

    def test_validate_args_multiple_date_arguments_raises_error(self):
        """Test validation raises error with multiple date arguments."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--year", "2023"])

    def test_validate_args_year_not_supported(self):
        """Test validation raises error for year argument (not supported in report)."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2023"])
        with pytest.raises(ValueError, match="Report phase only supports single month"):
            validate_args(args)

    def test_validate_args_range_not_supported(self):
        """Test validation raises error for range argument (not supported in report)."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2023-01:2023-03"])
        with pytest.raises(ValueError, match="Report phase only supports single month"):
            validate_args(args)

    def test_validate_args_start_end_not_supported(self):
        """Test validation raises error for start/end arguments (not supported in report)."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2023-01", "--end", "2023-03"])
        with pytest.raises(ValueError, match="Report phase only supports single month"):
            validate_args(args)


class TestReportCLIUtilities:
    """Test report CLI utility functions."""

    def test_get_default_month_format(self):
        """Test get_default_month returns correct format."""
        default_month = get_default_month()
        assert isinstance(default_month, str)
        assert "-" in default_month
        assert len(default_month) == 7  # YYYY-MM format

    def test_get_default_month_current_month(self):
        """Test get_default_month returns current month."""
        import datetime

        now = datetime.datetime.now()
        expected = f"{now.year:04d}-{now.month:02d}"
        default_month = get_default_month()
        assert default_month == expected


class TestReportMain:
    """Test report main function integration."""

    @patch("sotd.report.run.run_report")
    def test_main_with_month(self, mock_run_report):
        """Test main function with month argument."""
        with patch("sys.argv", ["report", "--month", "2023-01"]):
            main()

        mock_run_report.assert_called_once()
        args = mock_run_report.call_args[0][0]
        assert args.month == "2023-01"
        assert args.type == "hardware"

    @patch("sotd.report.run.run_report")
    def test_main_with_type(self, mock_run_report):
        """Test main function with type argument."""
        with patch("sys.argv", ["report", "--month", "2023-01", "--type", "software"]):
            main()

        mock_run_report.assert_called_once()
        args = mock_run_report.call_args[0][0]
        assert args.type == "software"

    @patch("sotd.report.run.run_report")
    def test_main_with_debug_and_force(self, mock_run_report):
        """Test main function with debug and force arguments."""
        with patch("sys.argv", ["report", "--month", "2023-01", "--debug", "--force"]):
            main()

        mock_run_report.assert_called_once()
        args = mock_run_report.call_args[0][0]
        assert args.debug is True
        assert args.force is True

    @patch("sotd.report.run.run_report")
    def test_main_with_data_root_and_out_dir(self, mock_run_report):
        """Test main function with data-root and out-dir arguments."""
        with patch(
            "sys.argv",
            ["report", "--month", "2023-01", "--data-root", "/data", "--out-dir", "/output"],
        ):
            main()

        mock_run_report.assert_called_once()
        args = mock_run_report.call_args[0][0]
        assert args.data_root == Path("/data")
        assert args.out_dir == Path("/output")

    @patch("sotd.report.run.run_report")
    def test_main_no_arguments_sets_default_month(self, mock_run_report):
        """Test main function with no arguments sets default month."""
        with patch("sys.argv", ["report"]):
            main()

        mock_run_report.assert_called_once()
        args = mock_run_report.call_args[0][0]
        assert args.month is not None
        assert "-" in args.month

    def test_main_invalid_year_argument_raises_error(self):
        """Test main function raises error for invalid year argument."""
        with patch("sys.argv", ["report", "--year", "2023"]):
            with patch("builtins.print") as mock_print:
                main()
                # Should print error message about report phase only supporting single month
                expected_error = (
                    "[ERROR] Report generation failed: Report phase only supports single month "
                    "processing. Use --month YYYY-MM to specify a single month."
                )
                mock_print.assert_called_with(expected_error)

    def test_main_invalid_range_argument_raises_error(self):
        """Test main function raises error for invalid range argument."""
        with patch("sys.argv", ["report", "--range", "2023-01:2023-03"]):
            with patch("builtins.print") as mock_print:
                main()
                # Should print error message about report phase only supporting single month
                expected_error = (
                    "[ERROR] Report generation failed: Report phase only supports single month "
                    "processing. Use --month YYYY-MM to specify a single month."
                )
                mock_print.assert_called_with(expected_error)
