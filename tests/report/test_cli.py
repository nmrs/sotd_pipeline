"""Tests for report phase CLI functionality."""

import pytest
from unittest.mock import patch
from sotd.report.run import parse_report_args, run_report


class TestReportCLI:
    """Test CLI argument parsing and validation."""

    def test_default_arguments(self):
        """Test default argument values."""
        args = parse_report_args([])
        assert args.type == "hardware"
        assert args.data_root == "data"
        assert args.out_dir == "data"
        assert not args.debug
        assert not args.force
        # Month should be current month
        assert args.month is not None

    def test_custom_arguments(self):
        """Test custom argument values."""
        args = parse_report_args(
            [
                "--month",
                "2025-01",
                "--type",
                "software",
                "--data-root",
                "/custom/data",
                "--out-dir",
                "/custom/output",
                "--debug",
                "--force",
            ]
        )
        assert args.month == "2025-01"
        assert args.type == "software"
        assert args.data_root == "/custom/data"
        assert args.out_dir == "/custom/output"
        assert args.debug
        assert args.force

    def test_invalid_report_type(self):
        """Test invalid report type raises error."""
        with pytest.raises(SystemExit):
            parse_report_args(["--type", "invalid"])

    def test_invalid_month_format(self):
        """Test invalid month format raises error."""
        with pytest.raises(ValueError, match="Invalid month format"):
            run_report(parse_report_args(["--month", "invalid"]))

    def test_missing_aggregated_data(self):
        """Test handling of missing aggregated data file."""
        args = parse_report_args(["--month", "2025-01"])

        with patch("sotd.report.load.get_aggregated_file_path") as mock_get_path:
            mock_get_path.return_value = "/nonexistent/file.json"

            with patch("sotd.report.load.load_aggregated_data") as mock_load:
                mock_load.side_effect = FileNotFoundError("File not found")

                with pytest.raises(FileNotFoundError, match="Aggregated data not found"):
                    run_report(args)

    def test_corrupted_json_data(self):
        """Test handling of corrupted JSON data."""
        args = parse_report_args(["--month", "2025-01"])

        with patch("sotd.report.load.load_aggregated_data") as mock_load:
            mock_load.side_effect = ValueError("Invalid JSON")

            with pytest.raises(RuntimeError, match="Failed to load aggregated data"):
                run_report(args)

    def test_report_generation_failure(self):
        """Test handling of report generation failure."""
        args = parse_report_args(["--month", "2025-01"])

        # Mock successful data loading
        mock_metadata = {"month": "2025-01", "total_shaves": 100, "unique_shavers": 10}
        mock_data = {"razors": []}

        with patch("sotd.report.load.load_aggregated_data") as mock_load:
            mock_load.return_value = (mock_metadata, mock_data)

            with patch("sotd.report.load.load_comparison_data") as mock_comp:
                mock_comp.return_value = {}

                with patch("sotd.report.process.generate_report_content") as mock_gen:
                    mock_gen.side_effect = RuntimeError("Generation failed")

                    with pytest.raises(RuntimeError, match="Failed to generate report content"):
                        run_report(args)

    def test_file_save_failure(self):
        """Test handling of file save failure."""
        args = parse_report_args(["--month", "2025-01"])

        # Mock successful data loading and report generation
        mock_metadata = {"month": "2025-01", "total_shaves": 100, "unique_shavers": 10}
        mock_data = {"razors": []}
        mock_report_content = "# Test Report\n\nTest content"

        with patch("sotd.report.load.load_aggregated_data") as mock_load:
            mock_load.return_value = (mock_metadata, mock_data)

            with patch("sotd.report.load.load_comparison_data") as mock_comp:
                mock_comp.return_value = {}

                with patch("sotd.report.process.generate_report_content") as mock_gen:
                    mock_gen.return_value = mock_report_content

                    with patch("sotd.report.save.generate_and_save_report") as mock_save:
                        mock_save.side_effect = OSError("Write failed")

                        with pytest.raises(RuntimeError, match="Failed to save report"):
                            run_report(args)

    def test_file_exists_without_force(self):
        """Test handling of existing file without force flag."""
        args = parse_report_args(["--month", "2025-01"])

        # Mock successful data loading and report generation
        mock_metadata = {"month": "2025-01", "total_shaves": 100, "unique_shavers": 10}
        mock_data = {"razors": []}
        mock_report_content = "# Test Report\n\nTest content"

        with patch("sotd.report.load.load_aggregated_data") as mock_load:
            mock_load.return_value = (mock_metadata, mock_data)

            with patch("sotd.report.load.load_comparison_data") as mock_comp:
                mock_comp.return_value = {}

                with patch("sotd.report.process.generate_report_content") as mock_gen:
                    mock_gen.return_value = mock_report_content

                    with patch("sotd.report.save.generate_and_save_report") as mock_save:
                        mock_save.side_effect = FileExistsError("File exists")

                        with pytest.raises(FileExistsError, match="Report file already exists"):
                            run_report(args)

    def test_successful_report_generation(self):
        """Test successful end-to-end report generation."""
        args = parse_report_args(["--month", "2025-01", "--type", "hardware"])

        # Mock all dependencies
        mock_metadata = {"month": "2025-01", "total_shaves": 100, "unique_shavers": 10}
        mock_data = {"razors": []}
        mock_report_content = "# Hardware Report - January 2025\n\nTest content"
        mock_output_path = "/output/2025-01-hardware.md"

        with patch("sotd.report.load.load_aggregated_data") as mock_load:
            mock_load.return_value = (mock_metadata, mock_data)

            with patch("sotd.report.load.load_comparison_data") as mock_comp:
                mock_comp.return_value = {}

                with patch("sotd.report.process.generate_report_content") as mock_gen:
                    mock_gen.return_value = mock_report_content

                    with patch("sotd.report.save.generate_and_save_report") as mock_save:
                        mock_save.return_value = mock_output_path

                        # Should not raise any exceptions
                        run_report(args)

                        # Verify all functions were called
                        mock_load.assert_called_once()
                        mock_comp.assert_called_once()
                        mock_gen.assert_called_once()
                        mock_save.assert_called_once()
