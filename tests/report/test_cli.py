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

    # Annual report CLI tests
    def test_annual_argument_parsing(self):
        """Test annual argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])
        assert args.annual is True
        assert args.year == "2023"
        assert args.month is None
        assert args.range is None

    def test_annual_with_year_argument_validation(self):
        """Test annual with year argument validation."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])
        assert args.annual is True
        assert args.year == "2023"

    def test_annual_with_range_argument_validation(self):
        """Test annual with range argument validation."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021-01:2023-12"])
        assert args.annual is True
        assert args.range == "2021-01:2023-12"

    def test_annual_without_year_or_range_raises_error(self):
        """Test annual without year or range raises error."""
        parser = get_parser()
        # This should not raise SystemExit because validation happens in validate_args
        args = parser.parse_args(["--annual"])
        with pytest.raises(ValueError, match="Annual reports require --year or --range"):
            validate_args(args)

    def test_annual_with_month_raises_error(self):
        """Test annual with month raises error."""
        parser = get_parser()
        # This should not raise SystemExit because validation happens in validate_args
        args = parser.parse_args(["--annual", "--month", "2023-01"])
        with pytest.raises(ValueError, match="Annual reports cannot be combined with monthly"):
            validate_args(args)

    def test_annual_with_year_and_range_raises_error(self):
        """Test annual with both year and range raises error."""
        parser = get_parser()
        # This should raise SystemExit because argparse handles mutually exclusive arguments
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--year", "2023", "--range", "2021-01:2023-12"])

    def test_annual_help_text_includes_annual_options(self):
        """Test that help text includes annual options."""
        parser = get_parser()
        help_text = parser.format_help()
        assert "--annual" in help_text
        assert "annual report" in help_text.lower()

    def test_annual_backward_compatibility_monthly(self):
        """Test that annual flag doesn't break monthly functionality."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.month == "2023-01"
        assert args.annual is False


class TestReportCLIValidation:
    """Test report CLI argument validation."""

    def test_validate_args_with_month(self):
        """Test validation with valid month argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        # Should not raise any exceptions
        validate_args(args)
        assert args.month == "2023-01"

    def test_validate_args_no_date_sets_default(self):
        """Test validation sets default month when no date provided."""
        parser = get_parser()
        args = parser.parse_args([])
        # Should not raise any exceptions
        validate_args(args)
        assert args.month is not None

    def test_validate_args_multiple_date_arguments_raises_error(self):
        """Test validation raises error for multiple date arguments."""
        parser = get_parser()
        # This should raise SystemExit because argparse handles mutually exclusive arguments
        with pytest.raises(SystemExit):
            parser.parse_args(["--month", "2023-01", "--year", "2023"])

    def test_validate_args_year_not_supported(self):
        """Test validation raises error for year without annual."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2023"])
        with pytest.raises(ValueError, match="Report phase only supports single month processing"):
            validate_args(args)

    def test_validate_args_range_not_supported(self):
        """Test validation raises error for range without annual."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2023-01:2023-03"])
        with pytest.raises(ValueError, match="Report phase only supports single month processing"):
            validate_args(args)

    def test_validate_args_start_end_not_supported(self):
        """Test validation raises error for start/end without annual."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2023-01", "--end", "2023-03"])
        with pytest.raises(ValueError, match="Report phase only supports single month processing"):
            validate_args(args)

    def test_validate_args_annual_with_year_valid(self):
        """Test validation with valid annual and year arguments."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])
        # Should not raise any exceptions
        validate_args(args)
        assert args.annual is True
        assert args.year == "2023"

    def test_validate_args_annual_with_range_valid(self):
        """Test validation with valid annual and range arguments."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021-01:2023-12"])
        # Should not raise any exceptions
        validate_args(args)
        assert args.annual is True
        assert args.range == "2021-01:2023-12"

    def test_validate_args_annual_without_year_or_range_raises_error(self):
        """Test validation raises error for annual without year or range."""
        parser = get_parser()
        args = parser.parse_args(["--annual"])
        with pytest.raises(ValueError, match="Annual reports require --year or --range"):
            validate_args(args)

    def test_validate_args_annual_with_month_raises_error(self):
        """Test validation raises error for annual with month."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--month", "2023-01"])
        with pytest.raises(ValueError, match="Annual reports cannot be combined with monthly"):
            validate_args(args)

    def test_validate_args_annual_with_year_and_range_raises_error(self):
        """Test validation raises error for annual with both year and range."""
        parser = get_parser()
        # This should raise SystemExit because argparse handles mutually exclusive arguments
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--year", "2023", "--range", "2021-01:2023-12"])


class TestReportCLIUtilities:
    """Test report CLI utility functions."""

    def test_get_default_month_format(self):
        """Test get_default_month returns correct format."""
        month = get_default_month()
        assert len(month) == 7
        assert month[4] == "-"
        assert month[:4].isdigit()
        assert month[5:].isdigit()

    def test_get_default_month_current_month(self):
        """Test get_default_month returns current month."""
        import datetime

        now = datetime.datetime.now()
        expected = f"{now.year:04d}-{now.month:02d}"
        month = get_default_month()
        assert month == expected


class TestReportMain:
    """Test report main function."""

    @patch("sotd.report.run.run_report")
    def test_main_with_month(self, mock_run_report):
        """Test main function with month argument."""
        main(["--month", "2023-01"])
        mock_run_report.assert_called_once()
        # Check that the function was called with the right arguments
        call_args = mock_run_report.call_args[0][0]  # First positional argument
        assert call_args.month == "2023-01"

    @patch("sotd.report.run.run_report")
    def test_main_with_type(self, mock_run_report):
        """Test main function with type argument."""
        main(["--month", "2023-01", "--type", "software"])
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args[0][0]  # First positional argument
        assert call_args.type == "software"

    @patch("sotd.report.run.run_report")
    def test_main_with_debug_and_force(self, mock_run_report):
        """Test main function with debug and force flags."""
        main(["--month", "2023-01", "--debug", "--force"])
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args[0][0]  # First positional argument
        assert call_args.debug is True
        assert call_args.force is True

    @patch("sotd.report.run.run_report")
    def test_main_with_data_root_and_out_dir(self, mock_run_report):
        """Test main function with data root and output directory."""
        main(["--month", "2023-01", "--data-root", "/data", "--out-dir", "/output"])
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args[0][0]  # First positional argument
        assert call_args.data_root == Path("/data")
        assert call_args.out_dir == Path("/output")

    @patch("sotd.report.run.run_report")
    def test_main_no_arguments_sets_default_month(self, mock_run_report):
        """Test main function sets default month when no arguments provided."""
        main([])
        mock_run_report.assert_called_once()
        call_args = mock_run_report.call_args[0][0]  # First positional argument
        assert call_args.month is not None

    def test_main_invalid_year_argument_raises_error(self):
        """Test main function raises error for invalid year argument."""
        with pytest.raises(SystemExit):
            main(["--year", "23"])

    def test_main_invalid_range_argument_raises_error(self):
        """Test main function raises error for invalid range argument."""
        with pytest.raises(SystemExit):
            main(["--range", "2023-01-2023-03"])

    @patch("sotd.report.run.run_annual_report")
    def test_main_annual_with_year(self, mock_run_annual_report):
        """Test main function with annual and year arguments."""
        main(["--annual", "--year", "2023"])
        mock_run_annual_report.assert_called_once()
        call_args = mock_run_annual_report.call_args[0][0]  # First positional argument
        assert call_args.annual is True
        assert call_args.year == "2023"

    @patch("sotd.report.run.run_annual_report")
    def test_main_annual_with_range(self, mock_run_annual_report):
        """Test main function with annual and range arguments."""
        main(["--annual", "--range", "2021-01:2023-12"])
        mock_run_annual_report.assert_called_once()
        call_args = mock_run_annual_report.call_args[0][0]  # First positional argument
        assert call_args.annual is True
        assert call_args.range == "2021-01:2023-12"

    @patch("sotd.report.run.run_annual_report")
    def test_main_annual_with_type(self, mock_run_annual_report):
        """Test main function with annual and type arguments."""
        main(["--annual", "--year", "2023", "--type", "software"])
        mock_run_annual_report.assert_called_once()
        call_args = mock_run_annual_report.call_args[0][0]  # First positional argument
        assert call_args.type == "software"

    def test_main_annual_without_year_or_range_raises_error(self, capsys):
        """Test main function raises error for annual without year or range."""
        main(["--annual"])
        captured = capsys.readouterr()
        assert "Annual reports require --year or --range" in captured.out

    def test_main_annual_with_month_raises_error(self, capsys):
        """Test main function raises error for annual with month."""
        main(["--annual", "--month", "2023-01"])
        captured = capsys.readouterr()
        assert "Annual reports cannot be combined with monthly" in captured.out
