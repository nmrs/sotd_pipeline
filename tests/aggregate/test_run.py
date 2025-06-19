"""Unit tests for the aggregate run module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from sotd.aggregate.run import main, process_month, run_aggregate


class TestProcessMonth:
    """Test the process_month function."""

    def test_invalid_year(self):
        """Test with invalid year."""
        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        result = process_month(1999, 1, args)  # Invalid year
        assert result["status"] == "error"
        assert "Invalid year" in result["error"]

    def test_invalid_month(self):
        """Test with invalid month."""
        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        result = process_month(2025, 13, args)  # Invalid month
        assert result["status"] == "error"
        assert "Invalid month" in result["error"]

    def test_missing_enriched_file(self):
        """Test with missing enriched file."""
        args = Mock()
        args.out_dir = "/nonexistent"
        args.debug = False
        args.force = False

        result = process_month(2025, 1, args)
        assert result["status"] == "skipped"
        assert result["reason"] == "missing_enriched_file"

    @patch("sotd.aggregate.run.load_enriched_data")
    @patch("sotd.aggregate.run.filter_matched_records")
    @patch("sotd.aggregate.run.calculate_basic_metrics")
    @patch("sotd.aggregate.run.aggregate_razors")
    @patch("sotd.aggregate.run.aggregate_blades")
    @patch("sotd.aggregate.run.aggregate_soaps")
    @patch("sotd.aggregate.run.aggregate_brushes")
    @patch("sotd.aggregate.run.aggregate_users")
    @patch("sotd.aggregate.run.aggregate_blackbird_plates")
    @patch("sotd.aggregate.run.aggregate_christopher_bradley_plates")
    @patch("sotd.aggregate.run.aggregate_game_changer_plates")
    @patch("sotd.aggregate.run.aggregate_super_speed_tips")
    @patch("sotd.aggregate.run.aggregate_straight_razor_specs")
    @patch("sotd.aggregate.run.aggregate_razor_blade_combinations")
    @patch("sotd.aggregate.run.aggregate_user_blade_usage")
    @patch("sotd.aggregate.run.save_aggregated_data")
    def test_specialized_aggregation_flags_handling(
        self,
        mock_save,
        mock_user_blade_usage,
        mock_razor_blade_combinations,
        mock_straight_razor_specs,
        mock_super_speed_tips,
        mock_game_changer_plates,
        mock_christopher_bradley_plates,
        mock_blackbird_plates,
        mock_users,
        mock_brushes,
        mock_soaps,
        mock_blades,
        mock_razors,
        mock_metrics,
        mock_filter,
        mock_load,
    ):
        """Test that specialized aggregation flags are properly handled."""
        # Mock return values
        mock_load.return_value = (
            {"month": "2025-01", "extracted_at": "2025-01-01T00:00:00Z"},
            [
                {
                    "id": "test123",
                    "author": "testuser",
                    "created_utc": 1640995200,
                    "body": "Test comment",
                }
            ],
        )
        mock_filter.return_value = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        mock_metrics.return_value = {
            "total_shaves": 1,
            "unique_shavers": 1,
            "avg_shaves_per_user": 1.0,
        }
        mock_razors.return_value = []
        mock_blades.return_value = []
        mock_soaps.return_value = []
        mock_brushes.return_value = []
        mock_users.return_value = []
        mock_blackbird_plates.return_value = []
        mock_christopher_bradley_plates.return_value = []
        mock_game_changer_plates.return_value = []
        mock_super_speed_tips.return_value = []
        mock_straight_razor_specs.return_value = []
        mock_razor_blade_combinations.return_value = []
        mock_user_blade_usage.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the enriched file
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist (so it won't be skipped)
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"

                # Test with specialized aggregations disabled
                args = Mock()
                args.out_dir = "data"
                args.debug = False
                args.force = False
                args.enable_specialized = False
                args.disable_specialized = True
                args.enable_cross_product = False
                args.disable_cross_product = True

                result = process_month(2025, 1, args)

                # Verify specialized aggregations were not called
                mock_blackbird_plates.assert_not_called()
                mock_christopher_bradley_plates.assert_not_called()
                mock_game_changer_plates.assert_not_called()
                mock_super_speed_tips.assert_not_called()
                mock_straight_razor_specs.assert_not_called()
                mock_razor_blade_combinations.assert_not_called()
                mock_user_blade_usage.assert_not_called()

                # Test with specialized aggregations enabled
                args.enable_specialized = True
                args.disable_specialized = False
                args.enable_cross_product = True
                args.disable_cross_product = False

                result = process_month(2025, 1, args)

                # Verify specialized aggregations were called
                mock_blackbird_plates.assert_called()
                mock_christopher_bradley_plates.assert_called()
                mock_game_changer_plates.assert_called()
                mock_super_speed_tips.assert_called()
                mock_straight_razor_specs.assert_called()
                mock_razor_blade_combinations.assert_called()
                mock_user_blade_usage.assert_called()

                assert result["status"] == "success"

    @patch("sotd.aggregate.run.load_enriched_data")
    @patch("sotd.aggregate.run.filter_matched_records")
    @patch("sotd.aggregate.run.calculate_basic_metrics")
    @patch("sotd.aggregate.run.aggregate_razors")
    @patch("sotd.aggregate.run.aggregate_blades")
    @patch("sotd.aggregate.run.aggregate_soaps")
    @patch("sotd.aggregate.run.aggregate_brushes")
    @patch("sotd.aggregate.run.aggregate_users")
    @patch("sotd.aggregate.run.save_aggregated_data")
    def test_successful_processing(
        self,
        mock_save,
        mock_users,
        mock_brushes,
        mock_soaps,
        mock_blades,
        mock_razors,
        mock_metrics,
        mock_filter,
        mock_load,
    ):
        """Test successful processing of a month."""
        # Mock return values
        mock_load.return_value = (
            {"month": "2025-01", "extracted_at": "2025-01-01T00:00:00Z"},
            [
                {
                    "id": "test123",
                    "author": "testuser",
                    "created_utc": 1640995200,
                    "body": "Test comment",
                }
            ],
        )
        mock_filter.return_value = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        mock_metrics.return_value = {
            "total_shaves": 1,
            "unique_shavers": 1,
            "avg_shaves_per_user": 1.0,
        }
        mock_razors.return_value = []
        mock_blades.return_value = []
        mock_soaps.return_value = []
        mock_brushes.return_value = []
        mock_users.return_value = []

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the enriched file
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist (so it won't be skipped)
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "success"
        assert result["year"] == 2025
        assert result["month"] == 1
        assert "basic_metrics" in result
        assert "aggregations" in result
        assert "summary" in result

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_no_data_to_process(self, mock_load):
        """Test when there's no data to process."""
        mock_load.return_value = (
            {"month": "2025-01", "extracted_at": "2025-01-01T00:00:00Z"},
            [],  # No data
        )

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "skipped"
        assert result["reason"] == "no_data"

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_file_not_found_error(self, mock_load):
        """Test handling of FileNotFoundError."""
        mock_load.side_effect = FileNotFoundError("File not found")

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "error"
        assert "File not found" in result["error"]

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_value_error(self, mock_load):
        """Test handling of ValueError."""
        mock_load.side_effect = ValueError("Data validation error")

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "error"
        assert "Data validation error" in result["error"]

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_json_decode_error(self, mock_load):
        """Test handling of JSONDecodeError."""
        import json

        mock_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "error"
        assert "JSON decode error" in result["error"]

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_os_error(self, mock_load):
        """Test handling of OSError."""
        mock_load.side_effect = OSError("File system error")

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "error"
        assert "File system error" in result["error"]

    @patch("sotd.aggregate.run.load_enriched_data")
    def test_unexpected_error(self, mock_load):
        """Test handling of unexpected errors."""
        mock_load.side_effect = Exception("Unexpected error")

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        assert result["status"] == "error"
        assert "Unexpected error" in result["error"]

    @patch("sotd.aggregate.run.load_enriched_data")
    @patch("sotd.aggregate.run.filter_matched_records")
    @patch("sotd.aggregate.run.calculate_basic_metrics")
    @patch("sotd.aggregate.run.aggregate_razors")
    @patch("sotd.aggregate.run.aggregate_blades")
    @patch("sotd.aggregate.run.aggregate_soaps")
    @patch("sotd.aggregate.run.aggregate_brushes")
    @patch("sotd.aggregate.run.aggregate_users")
    @patch("sotd.aggregate.run.save_aggregated_data")
    def test_aggregation_errors_handled(
        self,
        mock_save,
        mock_users,
        mock_brushes,
        mock_soaps,
        mock_blades,
        mock_razors,
        mock_metrics,
        mock_filter,
        mock_load,
    ):
        """Test that aggregation errors are handled gracefully."""
        # Mock return values
        mock_load.return_value = (
            {"month": "2025-01", "extracted_at": "2025-01-01T00:00:00Z"},
            [
                {
                    "id": "test123",
                    "author": "testuser",
                    "created_utc": 1640995200,
                    "body": "Test comment",
                }
            ],
        )
        mock_filter.return_value = [
            {
                "id": "test123",
                "author": "testuser",
                "created_utc": 1640995200,
                "body": "Test comment",
            }
        ]
        mock_metrics.return_value = {
            "total_shaves": 1,
            "unique_shavers": 1,
            "avg_shaves_per_user": 1.0,
        }

        # Mock aggregation functions to raise errors
        mock_razors.side_effect = Exception("Razor aggregation error")
        mock_blades.return_value = []
        mock_soaps.return_value = []
        mock_brushes.return_value = []
        mock_users.return_value = []

        args = Mock()
        args.out_dir = "data"
        args.debug = True  # Enable debug to see error messages
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            enriched_dir = Path(temp_dir) / "enriched"
            enriched_dir.mkdir()
            enriched_file = enriched_dir / "2025-01.json"
            enriched_file.write_text('{"meta": {}, "data": []}')

            with (
                patch("sotd.aggregate.run.get_enriched_file_path") as mock_enriched_path,
                patch("sotd.aggregate.run.get_aggregated_file_path") as mock_aggregated_path,
            ):
                mock_enriched_path.return_value = enriched_file
                # Mock aggregated file to not exist
                mock_aggregated_path.return_value = Path(temp_dir) / "aggregated" / "2025-01.json"
                result = process_month(2025, 1, args)

        # Should now fail fast and return error status
        assert result["status"] == "error"
        assert "Razor aggregation error" in result["error"]


class TestRunAggregate:
    """Test the run_aggregate function."""

    @patch("sotd.aggregate.run.month_span")
    @patch("sotd.aggregate.run.process_month")
    def test_successful_run(self, mock_process, mock_span):
        """Test successful run with multiple months."""
        # Mock month span
        mock_span.return_value = [(2025, 1), (2025, 2)]

        # Mock process_month results
        mock_process.side_effect = [
            {
                "year": 2025,
                "month": 1,
                "status": "success",
                "basic_metrics": {"total_shaves": 10, "unique_shavers": 5},
            },
            {
                "year": 2025,
                "month": 2,
                "status": "success",
                "basic_metrics": {"total_shaves": 15, "unique_shavers": 8},
            },
        ]

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            args.out_dir = temp_dir
            run_aggregate(args)

        # Verify process_month was called for each month
        assert mock_process.call_count == 2

    @patch("sotd.aggregate.run.month_span")
    @patch("sotd.aggregate.run.process_month")
    def test_mixed_results(self, mock_process, mock_span):
        """Test run with mixed success, skip, and error results."""
        # Mock month span
        mock_span.return_value = [(2025, 1), (2025, 2), (2025, 3)]

        # Mock process_month results
        mock_process.side_effect = [
            {
                "year": 2025,
                "month": 1,
                "status": "success",
                "basic_metrics": {"total_shaves": 10, "unique_shavers": 5},
            },
            {
                "year": 2025,
                "month": 2,
                "status": "skipped",
                "reason": "missing_enriched_file",
            },
            {
                "year": 2025,
                "month": 3,
                "status": "error",
                "error": "Test error",
            },
        ]

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            args.out_dir = temp_dir
            run_aggregate(args)

        # Verify process_month was called for each month
        assert mock_process.call_count == 3

    @patch("sotd.aggregate.run.month_span")
    def test_no_months_to_process(self, mock_span):
        """Test when no months are available to process."""
        mock_span.return_value = []

        args = Mock()
        args.out_dir = "data"
        args.debug = False
        args.force = False

        with tempfile.TemporaryDirectory() as temp_dir:
            args.out_dir = temp_dir
            run_aggregate(args)

    def test_output_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        args = Mock()
        args.out_dir = "/nonexistent/directory"
        args.debug = False
        args.force = False

        with patch("sotd.aggregate.run.month_span") as mock_span:
            mock_span.return_value = []

            # Should handle the directory creation gracefully
            run_aggregate(args)

    def test_output_directory_creation_error(self):
        """Test handling of output directory creation error."""
        args = Mock()
        args.out_dir = "/root/nonexistent"  # Should fail on Unix systems

        with patch("sotd.aggregate.run.month_span") as mock_span:
            mock_span.return_value = []

            # Should handle the error gracefully
            run_aggregate(args)


class TestMain:
    """Test the main CLI function."""

    def test_no_date_arguments(self):
        """Test with no date arguments (should use current month)."""
        import datetime as real_datetime

        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            with patch("sotd.aggregate.run.datetime") as mock_datetime:
                mock_datetime.datetime.now.return_value = real_datetime.datetime(2025, 4, 1)

                main(["aggregate", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        # The default month logic is now handled inside run_aggregate, not in main
        assert args.out_dir == "data"

    def test_month_argument(self):
        """Test with --month argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--month", "2025-04", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.month == "2025-04"
        assert args.out_dir == "data"

    def test_year_argument(self):
        """Test with --year argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--year", "2025", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.year == 2025
        assert args.out_dir == "data"

    def test_range_argument(self):
        """Test with --range argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--range", "2025-01:2025-03", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.range == "2025-01:2025-03"
        assert args.out_dir == "data"

    def test_start_end_arguments(self):
        """Test with --start and --end arguments."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            # Test with just --start (single month)
            main(["aggregate", "--start", "2025-01", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.start == "2025-01"
        assert args.out_dir == "data"

    def test_debug_argument(self):
        """Test with --debug argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--debug", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.debug is True
        assert args.out_dir == "data"

    def test_force_argument(self):
        """Test with --force argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--force", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.force is True
        assert args.out_dir == "data"

    def test_output_directory_creation_in_main(self):
        """Test output directory creation in main function."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            with tempfile.TemporaryDirectory() as temp_dir:
                main(["aggregate", "--out-dir", temp_dir])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.out_dir == temp_dir

    def test_output_directory_creation_error_in_main(self):
        """Test output directory creation error in main function."""
        # Try to create a directory in a location that should fail
        main(["aggregate", "--out-dir", "/root/nonexistent"])

        # Should handle the error gracefully

    def test_benchmark_command(self):
        """Test benchmark command."""
        with patch("sotd.aggregate.run.run_benchmark") as mock_run:
            main(["benchmark", "--debug"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.debug is True

    def test_benchmark_command_with_month(self):
        """Test benchmark command with month argument."""
        with patch("sotd.aggregate.run.run_benchmark") as mock_run:
            main(["benchmark", "--month", "2025-04", "--save-results"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.month == "2025-04"
        assert args.save_results is True

    def test_unknown_command(self):
        """Test handling of unknown command."""
        with pytest.raises(SystemExit):
            main(["unknown"])

    def test_specialized_aggregation_flags(self):
        """Test specialized aggregation CLI flags."""
        # Test enable-specialized flag
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--enable-specialized", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_specialized is True
        assert args.disable_specialized is False

        # Test disable-specialized flag
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--disable-specialized", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_specialized is False
        assert args.disable_specialized is True

        # Test enable-cross-product flag
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--enable-cross-product", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_cross_product is True
        assert args.disable_cross_product is False

        # Test disable-cross-product flag
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--disable-cross-product", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_cross_product is False
        assert args.disable_cross_product is True

        # Test both flags together
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(
                [
                    "aggregate",
                    "--enable-specialized",
                    "--disable-cross-product",
                    "--out-dir",
                    "data",
                ]
            )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_specialized is True
        assert args.disable_cross_product is True

    def test_specialized_aggregation_defaults(self):
        """Test default values for specialized aggregation flags."""
        # Test defaults (both should be enabled by default)
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["aggregate", "--out-dir", "data"])

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.enable_specialized is False  # Not explicitly set
        assert args.disable_specialized is False  # Not explicitly set
        assert args.enable_cross_product is False  # Not explicitly set
        assert args.disable_cross_product is False  # Not explicitly set
