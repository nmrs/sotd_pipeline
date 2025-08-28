"""Integration tests for annual report generation."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sotd.report import annual_run


class TestAnnualReportIntegration:
    """Test integration of annual report components."""

    @pytest.fixture
    def mock_annual_data(self):
        """Mock annual aggregated data."""
        return {
            "metadata": {
                "year": "2024",
                "total_shaves": 12000,
                "unique_shavers": 150,
                "included_months": ["2024-01", "2024-02", "2024-03"],
                "missing_months": ["2024-04"]},
            "razors": [
                {"brand": "Rockwell", "model": "6C", "count": 500},
                {"brand": "Merkur", "model": "34C", "count": 300}],
            "blades": [
                {"brand": "Astra", "model": "Superior Platinum", "count": 800},
                {"brand": "Feather", "model": "Hi-Stainless", "count": 600}],
            "brushes": [
                {"brand": "Simpson", "model": "Chubby 2", "count": 400},
                {"brand": "Omega", "model": "10049", "count": 300}],
            "soaps": [
                {"brand": "Barrister and Mann", "model": "Seville", "count": 700},
                {"brand": "Stirling", "model": "Executive Man", "count": 500}]}

    @pytest.fixture
    def mock_args(self, tmp_path):
        """Mock CLI arguments for annual report generation."""
        args = Mock()
        args.annual = True
        args.year = "2024"
        args.range = None
        args.type = "hardware"
        args.data_root = tmp_path / "data"
        args.out_dir = tmp_path / "data" / "reports"
        args.debug = False
        args.force = False
        return args

    def test_run_annual_report_success(self, mock_args, mock_annual_data, tmp_path):
        """Test successful annual report generation workflow."""
        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        # Mock the annual generator to return a simple report
        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = Path("data/reports/2024-hardware.md")

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify generator was called correctly
            mock_generator.assert_called_once_with("hardware", "2024", data_root, False, None)

            # Verify saver was called correctly
            mock_saver.assert_called_once_with(
                mock_report_content, mock_args.out_dir, "2024", "hardware", False, False
            )

    def test_run_annual_report_with_debug(self, mock_args, mock_annual_data, tmp_path):
        """Test annual report generation with debug logging."""
        mock_args.debug = True

        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
            patch("builtins.print") as mock_print,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = Path("data/reports/2024-hardware.md")

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify debug output was printed
            debug_calls = [
                call for call in mock_print.call_args_list if call[0][0].startswith("[DEBUG]")
            ]
            assert len(debug_calls) > 0

            # Verify generator was called with debug=True
            mock_generator.assert_called_once_with("hardware", "2024", data_root, True, None)

    def test_run_annual_report_missing_data(self, mock_args, tmp_path):
        """Test annual report generation with missing data file."""
        # Setup empty data directory
        data_root = tmp_path / "data"
        data_root.mkdir()

        with patch("sotd.report.annual_run.generate_annual_report") as mock_generator:
            mock_generator.side_effect = FileNotFoundError("Annual data file not found")

            # Run the annual report generation
            with pytest.raises(FileNotFoundError, match="Annual data not found for 2024"):
                annual_run.run_annual_report(mock_args)

    def test_run_annual_report_generator_error(self, mock_args, mock_annual_data, tmp_path):
        """Test annual report generation with generator error."""
        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        with patch("sotd.report.annual_run.generate_annual_report") as mock_generator:
            mock_generator.side_effect = ValueError("Invalid report type")

            # Run the annual report generation
            with pytest.raises(
                RuntimeError, match="Failed to generate annual hardware report content"
            ):
                annual_run.run_annual_report(mock_args)

    def test_run_annual_report_save_error(self, mock_args, mock_annual_data, tmp_path):
        """Test annual report generation with save error."""
        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.side_effect = PermissionError("Permission denied")

            # Run the annual report generation
            with pytest.raises(PermissionError, match="Permission denied"):
                annual_run.run_annual_report(mock_args)

    def test_run_annual_report_software_type(self, mock_args, mock_annual_data, tmp_path):
        """Test annual report generation for software type."""
        mock_args.type = "software"

        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Software Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = Path("data/reports/2024-software.md")

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify generator was called with software type
            mock_generator.assert_called_once_with("software", "2024", data_root, False, None)

            # Verify saver was called with software type
            mock_saver.assert_called_once_with(
                mock_report_content, mock_args.out_dir, "2024", "software", False, False
            )

    def test_run_annual_report_with_force(self, mock_args, mock_annual_data, tmp_path):
        """Test annual report generation with force flag."""
        mock_args.force = True

        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = Path("data/reports/2024-hardware.md")

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify saver was called with force=True
            mock_saver.assert_called_once_with(
                mock_report_content, mock_args.out_dir, "2024", "hardware", True, False
            )

    def test_run_annual_report_performance_monitoring(self, mock_args, mock_annual_data, tmp_path):
        """Test that performance monitoring is used during annual report generation."""
        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
            patch("sotd.report.annual_run.PerformanceMonitor") as mock_monitor_class,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = Path("data/reports/2024-hardware.md")

            # Create a proper mock monitor with the required attributes
            mock_monitor = Mock()
            mock_monitor.metrics = Mock()
            mock_monitor.metrics.record_count = 0
            mock_monitor.metrics.total_processing_time = 0.0
            mock_monitor.metrics.file_io_time = 0.0
            mock_monitor.metrics.peak_memory_mb = 0.0

            mock_monitor_class.return_value = mock_monitor

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify performance monitor was used
            mock_monitor_class.assert_called_once()

    def test_run_annual_report_success_message(self, mock_args, mock_annual_data, tmp_path):
        """Test that success message is printed after successful generation."""
        # Setup test data
        data_root = tmp_path / "data"
        data_root.mkdir()
        annual_data_dir = data_root / "aggregated" / "annual"
        annual_data_dir.mkdir(parents=True)

        annual_file = annual_data_dir / "2024.json"
        with open(annual_file, "w") as f:
            json.dump(mock_annual_data, f, ensure_ascii=False)

        mock_report_content = "# Annual Hardware Report 2024\n\nTest report content"
        output_path = Path("data/reports/2024-hardware.md")

        with (
            patch("sotd.report.annual_run.generate_annual_report") as mock_generator,
            patch("sotd.report.annual_run.save_annual_report") as mock_saver,
            patch("builtins.print") as mock_print,
        ):

            mock_generator.return_value = mock_report_content
            mock_saver.return_value = output_path

            # Run the annual report generation
            annual_run.run_annual_report(mock_args)

            # Verify success messages were printed
            success_calls = [
                call for call in mock_print.call_args_list if call[0][0].startswith("[INFO]")
            ]
            assert len(success_calls) >= 1

            # Check for specific success message
            success_messages = [call[0][0] for call in success_calls]
            assert any(
                "Annual report generation completed for 2024" in msg for msg in success_messages
            )


class TestAnnualReportCLIIntegration:
    """Test CLI integration for annual report generation."""

    @pytest.fixture
    def mock_args(self, tmp_path):
        """Mock CLI arguments for annual report generation."""
        args = Mock()
        args.annual = True
        args.year = "2024"
        args.range = None
        args.type = "hardware"
        args.data_root = tmp_path / "data"
        args.out_dir = tmp_path / "data" / "reports"
        args.debug = False
        args.force = False
        return args

    def test_main_annual_report_flow(self, mock_args):
        """Test main function routes to annual report generation."""
        with (
            patch("sotd.report.annual_run.cli.get_parser") as mock_get_parser,
            patch("sotd.report.annual_run.cli.validate_args"),
            patch("sotd.report.annual_run.run_annual_report") as mock_run_annual,
        ):

            mock_parser = Mock()
            mock_parser.parse_args.return_value = mock_args
            mock_get_parser.return_value = mock_parser

            # Call main function
            annual_run.main(["report", "--annual", "--year", "2024", "--type", "hardware"])

            # Verify CLI flow
            mock_get_parser.assert_called_once()
            mock_parser.parse_args.assert_called_once()
            mock_run_annual.assert_called_once_with(mock_args)

    def test_main_monthly_report_flow(self, mock_args):
        """Test main function routes to monthly report generation."""
        mock_args.annual = False
        mock_args.month = "2024-01"

        with (
            patch("sotd.report.annual_run.cli.get_parser") as mock_get_parser,
            patch("sotd.report.annual_run.cli.validate_args"),
            patch("sotd.report.annual_run.run_report") as mock_run_monthly,
        ):

            mock_parser = Mock()
            mock_parser.parse_args.return_value = mock_args
            mock_get_parser.return_value = mock_parser

            # Call main function
            annual_run.main(["report", "--month", "2024-01", "--type", "hardware"])

            # Verify CLI flow
            mock_get_parser.assert_called_once()
            mock_parser.parse_args.assert_called_once()
            mock_run_monthly.assert_called_once_with(mock_args)

    def test_main_keyboard_interrupt(self, mock_args):
        """Test main function handles keyboard interrupt gracefully."""
        with (
            patch("sotd.report.annual_run.cli.get_parser") as mock_get_parser,
            patch("sotd.report.annual_run.cli.validate_args"),
            patch("sotd.report.annual_run.run_annual_report") as mock_run_annual,
            patch("builtins.print") as mock_print,
        ):

            mock_parser = Mock()
            mock_parser.parse_args.return_value = mock_args
            mock_get_parser.return_value = mock_parser
            mock_run_annual.side_effect = KeyboardInterrupt()

            # Call main function
            annual_run.main(["report", "--annual", "--year", "2024"])

            # Verify graceful handling
            mock_print.assert_called_with("\n[INFO] Report generation interrupted by user")

    def test_main_general_exception(self, mock_args):
        """Test main function handles general exceptions gracefully."""
        with (
            patch("sotd.report.annual_run.cli.get_parser") as mock_get_parser,
            patch("sotd.report.annual_run.cli.validate_args"),
            patch("sotd.report.annual_run.run_annual_report") as mock_run_annual,
            patch("builtins.print") as mock_print,
        ):

            mock_parser = Mock()
            mock_parser.parse_args.return_value = mock_args
            mock_get_parser.return_value = mock_parser
            mock_run_annual.side_effect = RuntimeError("Test error")

            # Call main function
            annual_run.main(["report", "--annual", "--year", "2024"])

            # Verify graceful handling
            mock_print.assert_called_with("[ERROR] Report generation failed: Test error")


class TestAnnualReportSaveIntegration:
    """Test integration of annual report saving functionality."""

    def test_save_annual_report_success(self, tmp_path):
        """Test successful annual report saving."""
        report_content = "# Annual Hardware Report 2024\n\nTest report content"
        out_dir = tmp_path / "reports"
        out_dir.mkdir()

        output_path = annual_run.save_annual_report(
            report_content, out_dir, "2024", "hardware", False, False
        )

        # Verify file was created
        assert output_path.exists()
        assert output_path.name == "2024-hardware.md"

        # Verify content was written correctly
        with open(output_path, "r") as f:
            content = f.read()
        assert content == report_content

    def test_save_annual_report_with_force(self, tmp_path):
        """Test annual report saving with force flag."""
        report_content = "# Annual Hardware Report 2024\n\nTest report content"
        out_dir = tmp_path / "reports"
        out_dir.mkdir()

        # Create existing file
        existing_file = out_dir / "2024-hardware.md"
        with open(existing_file, "w") as f:
            f.write("Old content")

        # Save with force=True
        output_path = annual_run.save_annual_report(
            report_content, out_dir, "2024", "hardware", True, False
        )

        # Verify file was overwritten
        with open(output_path, "r") as f:
            content = f.read()
        assert content == report_content

    def test_save_annual_report_without_force(self, tmp_path):
        """Test annual report saving without force flag raises error."""
        report_content = "# Annual Hardware Report 2024\n\nTest report content"
        out_dir = tmp_path / "reports"
        out_dir.mkdir()

        # Create existing file
        existing_file = out_dir / "2024-hardware.md"
        with open(existing_file, "w") as f:
            f.write("Old content")

        # Save without force should raise FileExistsError
        with pytest.raises(FileExistsError):
            annual_run.save_annual_report(report_content, out_dir, "2024", "hardware", False, False)

    def test_save_annual_report_creates_directory(self, tmp_path):
        """Test that save_annual_report creates output directory if it doesn't exist."""
        report_content = "# Annual Hardware Report 2024\n\nTest report content"
        out_dir = tmp_path / "reports" / "annual"

        # Directory doesn't exist yet
        assert not out_dir.exists()

        output_path = annual_run.save_annual_report(
            report_content, out_dir, "2024", "hardware", False, False
        )

        # Verify directory was created and file was saved
        assert out_dir.exists()
        assert output_path.exists()
        assert output_path.name == "2024-hardware.md"

    def test_save_annual_report_software_type(self, tmp_path):
        """Test annual report saving for software type."""
        report_content = "# Annual Software Report 2024\n\nTest report content"
        out_dir = tmp_path / "reports"
        out_dir.mkdir()

        output_path = annual_run.save_annual_report(
            report_content, out_dir, "2024", "software", False, False
        )

        # Verify correct filename
        assert output_path.name == "2024-software.md"

        # Verify content was written correctly
        with open(output_path, "r") as f:
            content = f.read()
        assert content == report_content
