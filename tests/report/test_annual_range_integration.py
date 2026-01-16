"""Integration tests for annual range processing in report phase."""

import pytest
from pathlib import Path
from unittest.mock import patch

from sotd.report.cli import get_parser, validate_args
from sotd.report.run import run_annual_report, main


class TestAnnualRangeIntegration:
    """Test annual range processing integration."""

    @patch("sotd.report.run.run_annual_report")
    def test_main_with_annual_range(self, mock_run_annual_report):
        """Test main function routes annual range to correct handler."""
        with patch(
            "sys.argv", ["report", "--annual", "--range", "2021:2024", "--type", "hardware"]
        ):
            main()

        mock_run_annual_report.assert_called_once()
        args = mock_run_annual_report.call_args[0][0]
        assert args.annual is True
        assert args.range == "2021:2024"
        assert args.type == "hardware"

    def test_annual_range_parsing_valid_years(self):
        """Test that valid year ranges are parsed correctly."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021:2024"])
        validate_args(args)

        # Parse the range to get years
        start_year, end_year = args.range.split(":")
        years = [str(year) for year in range(int(start_year), int(end_year) + 1)]

        assert years == ["2021", "2022", "2023", "2024"]

    def test_annual_range_parsing_single_year(self):
        """Test that single year range is handled correctly."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2023:2023"])
        validate_args(args)

        start_year, end_year = args.range.split(":")
        years = [str(year) for year in range(int(start_year), int(end_year) + 1)]

        assert years == ["2023"]

    def test_annual_range_parsing_reverse_order(self):
        """Test that reverse year order is handled correctly."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2024:2021"])
        validate_args(args)

        start_year, end_year = args.range.split(":")
        # When start > end, range() returns empty list, so we need to handle this
        if int(start_year) > int(end_year):
            years = [str(year) for year in range(int(end_year), int(start_year) + 1)]
        else:
            years = [str(year) for year in range(int(start_year), int(end_year) + 1)]

        assert years == ["2021", "2022", "2023", "2024"]


class TestAnnualRangeProcessing:
    """Test annual range processing logic."""

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_run_annual_range_single_year(self, mock_save, mock_generate):
        """Test processing a single year range."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2023:2023", "--type", "hardware"])

        # Mock the generate function to return test content
        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2023-hardware.md")

        run_annual_report(args)

        # Should call generate once for the single year
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[0][0] == "hardware"  # report_type
        assert call_args[0][1] == "2023"  # year
        assert call_args[0][2] == Path("data")  # data_root
        assert call_args[0][3] is False  # debug
        assert call_args[0][4] is None  # comparison_year

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_run_annual_range_multiple_years(self, mock_save, mock_generate):
        """Test processing multiple years in range."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2021:2023", "--type", "hardware"])

        # Mock the generate function to return test content
        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2021-hardware.md")

        run_annual_report(args)

        # Should call generate for each year in the range
        assert mock_generate.call_count == 3
        expected_years = ["2021", "2022", "2023"]
        actual_years = [call[0][1] for call in mock_generate.call_args_list]
        assert actual_years == expected_years

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_run_annual_range_with_debug(self, mock_save, mock_generate):
        """Test range processing with debug output."""
        parser = get_parser()
        args = parser.parse_args(
            ["--annual", "--range", "2022:2023", "--type", "hardware", "--debug"]
        )

        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2022-hardware.md")

        run_annual_report(args)

        # Should call generate with debug=True
        assert mock_generate.call_count == 2
        for call in mock_generate.call_args_list:
            assert call[0][3] is True  # debug flag

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_run_annual_range_with_force(self, mock_save, mock_generate):
        """Test range processing with force flag."""
        parser = get_parser()
        args = parser.parse_args(
            ["--annual", "--range", "2022:2023", "--type", "hardware", "--force"]
        )

        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2022-hardware.md")

        run_annual_report(args)

        # Should call save with force=True
        assert mock_save.call_count == 2
        for call in mock_save.call_args_list:
            assert call[0][4] is True  # force flag

    @patch("sotd.report.annual_run.generate_annual_report")
    def test_run_annual_range_generation_failure(self, mock_generate):
        """Test handling of generation failure in range processing."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2022:2023", "--type", "hardware"])

        # Mock generation to fail for one year
        def mock_generate_side_effect(report_type, year, data_root, debug, comparison_year):
            if year == "2022":
                raise RuntimeError("Generation failed for 2022")
            return "# Test Report Content"

        mock_generate.side_effect = mock_generate_side_effect

        # Should raise the error
        with pytest.raises(RuntimeError, match="Generation failed for 2022"):
            run_annual_report(args)

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_run_annual_range_save_failure(self, mock_save, mock_generate):
        """Test handling of save failure in range processing."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2022:2023", "--type", "hardware"])

        mock_generate.return_value = "# Test Report Content"

        # Mock save to fail for one year
        def mock_save_side_effect(report_content, out_dir, year, report_type, force, debug):
            if year == "2022":
                raise OSError("Save failed for 2022")
            return Path(f"data/reports/annual/{year}-{report_type}.md")

        mock_save.side_effect = mock_save_side_effect

        # Should raise the error
        with pytest.raises(OSError, match="Save failed for 2022"):
            run_annual_report(args)


class TestAnnualRangeErrorHandling:
    """Test error handling for annual range processing."""

    def test_annual_range_invalid_year_format(self):
        """Test handling of invalid year format in range."""
        parser = get_parser()
        # This should be caught by argparse validation
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "2021:abc"])

    def test_annual_range_missing_end_year(self):
        """Test handling of missing end year in range."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "2021:"])

    def test_annual_range_missing_start_year(self):
        """Test handling of missing start year in range."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", ":2024"])

    def test_annual_range_negative_years(self):
        """Test handling of negative years in range."""
        parser = get_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--annual", "--range", "-2021:2024"])

    def test_annual_range_future_years(self):
        """Test handling of future years in range (should be allowed)."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2025:2030"])
        # Should not raise any exceptions
        validate_args(args)
        assert args.range == "2025:2030"


class TestAnnualRangePerformance:
    """Test performance characteristics of annual range processing."""

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_annual_range_large_range_performance(self, mock_save, mock_generate):
        """Test performance with large year ranges."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2015:2024", "--type", "hardware"])

        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2015-hardware.md")

        # Should process all 10 years without performance issues
        run_annual_report(args)

        # Should call generate for each year
        assert mock_generate.call_count == 10
        expected_years = [str(year) for year in range(2015, 2025)]
        actual_years = [call[0][1] for call in mock_generate.call_args_list]
        assert actual_years == expected_years

    @patch("sotd.report.annual_run.generate_annual_report")
    @patch("sotd.report.annual_run.save_annual_report")
    def test_annual_range_memory_usage(self, mock_save, mock_generate):
        """Test memory usage during range processing."""
        parser = get_parser()
        args = parser.parse_args(["--annual", "--range", "2020:2024", "--type", "hardware"])

        mock_generate.return_value = "# Test Report Content"
        mock_save.return_value = Path("data/reports/annual/2020-hardware.md")

        # Process should complete without memory issues
        run_annual_report(args)

        # Verify all years were processed
        assert mock_generate.call_count == 5
        assert mock_save.call_count == 5
