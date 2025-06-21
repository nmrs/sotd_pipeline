"""Integration tests for aggregate CLI functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from sotd.aggregate.cli import get_parser, main
from sotd.aggregate.run import run


class TestAggregateCLI:
    """Test aggregate CLI argument parsing and validation."""

    def test_get_parser_creates_parser(self):
        """Test that get_parser returns a valid ArgumentParser."""
        parser = get_parser()
        assert parser is not None
        assert (
            parser.description == "Aggregate enriched SOTD data to generate statistical summaries."
        )

    def test_month_argument_validation_valid(self):
        """Test valid month argument parsing."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.month == "2023-01"
        assert args.year is None
        assert args.range is None
        assert args.annual is False

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
        assert args.annual is False

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
        assert args.annual is False

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
        assert args.annual is False

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

    def test_no_date_arguments_raises_error(self):
        """Test that no date arguments raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

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

    # Annual aggregation tests
    def test_annual_argument_default_false(self):
        """Test that annual flag defaults to False."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])
        assert args.annual is False

    def test_annual_argument_enabled(self):
        """Test that annual flag can be enabled."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])
        assert args.annual is True
        assert args.year == "2023"

    def test_annual_with_month_raises_error(self):
        """Test that annual flag with month raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--month", "2023-01"])

    def test_annual_with_range_raises_error(self):
        """Test that annual flag with range raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "2023-01:2023-03"])

    def test_annual_with_start_end_raises_error(self):
        """Test that annual flag with start/end raises error."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--start", "2023-01", "--end", "2023-03"])

    def test_annual_requires_year_argument(self):
        """Test that annual flag requires year argument."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual"])

    def test_annual_with_year_valid(self):
        """Test that annual flag with year is valid."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])
        assert args.annual is True
        assert args.year == "2023"

    def test_annual_range_support_valid(self):
        """Test that annual flag supports year ranges."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021:2024"])
        assert args.annual is True
        assert args.range == "2021:2024"

    def test_annual_range_validation_invalid_format(self):
        """Test that annual range validation works for invalid formats."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "2021-2024"])

    def test_annual_range_validation_invalid_year(self):
        """Test that annual range validation works for invalid years."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "2021-13:2024-01"])

    def test_help_text_includes_annual_option(self):
        """Test that help text includes annual option."""
        parser = get_parser()
        help_text = parser.format_help()
        assert "--annual" in help_text
        assert "annual" in help_text.lower()


class TestAggregateRun:
    """Test aggregate run function integration."""

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_month(self, mock_process_months):
        """Test run function with month argument."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        assert call_args[0][0] == ["2023-01"]  # months
        assert call_args[0][1] == Path("data")  # out_dir
        assert call_args[1]["debug"] is False  # debug

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_year(self, mock_process_months):
        """Test run function with year argument."""
        parser = get_parser()
        args = parser.parse_args(["--year", "2023"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        # Should process all 12 months of 2023
        expected_months = [f"2023-{month:02d}" for month in range(1, 13)]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_range(self, mock_process_months):
        """Test run function with range argument."""
        parser = get_parser()
        args = parser.parse_args(["--range", "2023-01:2023-03"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        expected_months = ["2023-01", "2023-02", "2023-03"]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_start_end(self, mock_process_months):
        """Test run function with start/end arguments."""
        parser = get_parser()
        args = parser.parse_args(["--start", "2023-01", "--end", "2023-03"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        expected_months = ["2023-01", "2023-02", "2023-03"]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_debug(self, mock_process_months):
        """Test run function with debug flag."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--debug"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        assert call_args[0][0] == ["2023-01"]
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is True

    @patch("sotd.aggregate.run.process_months")
    def test_run_with_custom_out_dir(self, mock_process_months):
        """Test run function with custom output directory."""
        parser = get_parser()
        args = parser.parse_args(["--month", "2023-01", "--out-dir", "/custom/path"])

        run(args)

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        assert call_args[0][0] == ["2023-01"]
        assert call_args[0][1] == Path("/custom/path")
        assert call_args[1]["debug"] is False

    # Annual aggregation run tests
    @patch("sotd.aggregate.run.process_annual")
    def test_run_with_annual_year(self, mock_process_annual):
        """Test run function with annual year argument."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023"])

        run(args)

        mock_process_annual.assert_called_once()
        call_args = mock_process_annual.call_args
        assert call_args[0][0] == "2023"  # year
        assert call_args[0][1] == Path("data")  # out_dir
        assert call_args[1]["debug"] is False  # debug

    @patch("sotd.aggregate.run.process_annual_range")
    def test_run_with_annual_range(self, mock_process_annual_range):
        """Test run function with annual range argument."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021:2024"])

        run(args)

        mock_process_annual_range.assert_called_once()
        call_args = mock_process_annual_range.call_args
        assert call_args[0][0] == ["2021", "2022", "2023", "2024"]  # years
        assert call_args[0][1] == Path("data")  # out_dir
        assert call_args[1]["debug"] is False  # debug

    @patch("sotd.aggregate.run.process_annual")
    def test_run_with_annual_debug(self, mock_process_annual):
        """Test run function with annual and debug flags."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023", "--debug"])

        run(args)

        mock_process_annual.assert_called_once()
        call_args = mock_process_annual.call_args
        assert call_args[0][0] == "2023"
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is True

    @patch("sotd.aggregate.run.process_annual")
    def test_run_with_annual_force(self, mock_process_annual):
        """Test run function with annual and force flags."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--year", "2023", "--force"])

        run(args)

        mock_process_annual.assert_called_once()
        call_args = mock_process_annual.call_args
        assert call_args[0][0] == "2023"
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False
        assert call_args[1]["force"] is True


class TestAggregateMain:
    """Test aggregate main function integration."""

    @patch("sotd.aggregate.run.process_months")
    def test_main_with_month(self, mock_process_months):
        """Test main function with month argument."""
        with patch("sys.argv", ["aggregate", "--month", "2023-01"]):
            main()

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        assert call_args[0][0] == ["2023-01"]
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_main_with_year(self, mock_process_months):
        """Test main function with year argument."""
        with patch("sys.argv", ["aggregate", "--year", "2023"]):
            main()

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        expected_months = [f"2023-{month:02d}" for month in range(1, 13)]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_main_with_range(self, mock_process_months):
        """Test main function with range argument."""
        with patch("sys.argv", ["aggregate", "--range", "2023-01:2023-03"]):
            main()

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        expected_months = ["2023-01", "2023-02", "2023-03"]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_main_with_start_end(self, mock_process_months):
        """Test main function with start/end arguments."""
        with patch("sys.argv", ["aggregate", "--start", "2023-01", "--end", "2023-03"]):
            main()

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        expected_months = ["2023-01", "2023-02", "2023-03"]
        assert call_args[0][0] == expected_months
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_months")
    def test_main_with_debug_and_force(self, mock_process_months):
        """Test main function with debug and force flags."""
        with patch("sys.argv", ["aggregate", "--month", "2023-01", "--debug", "--force"]):
            main()

        mock_process_months.assert_called_once()
        call_args = mock_process_months.call_args
        assert call_args[0][0] == ["2023-01"]
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is True

    # Annual aggregation main tests
    @patch("sotd.aggregate.run.process_annual")
    def test_main_with_annual_year(self, mock_process_annual):
        """Test main function with annual year argument."""
        with patch("sys.argv", ["aggregate", "--annual", "--year", "2023"]):
            main()

        mock_process_annual.assert_called_once()
        call_args = mock_process_annual.call_args
        assert call_args[0][0] == "2023"
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_annual_range")
    def test_main_with_annual_range(self, mock_process_annual_range):
        """Test main function with annual range argument."""
        with patch("sys.argv", ["aggregate", "--annual", "--range", "2021:2024"]):
            main()

        mock_process_annual_range.assert_called_once()
        call_args = mock_process_annual_range.call_args
        assert call_args[0][0] == ["2021", "2022", "2023", "2024"]
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is False

    @patch("sotd.aggregate.run.process_annual")
    def test_main_with_annual_debug_force(self, mock_process_annual):
        """Test main function with annual, debug, and force flags."""
        with patch("sys.argv", ["aggregate", "--annual", "--year", "2023", "--debug", "--force"]):
            main()

        mock_process_annual.assert_called_once()
        call_args = mock_process_annual.call_args
        assert call_args[0][0] == "2023"
        assert call_args[0][1] == Path("data")
        assert call_args[1]["debug"] is True
        assert call_args[1]["force"] is True
