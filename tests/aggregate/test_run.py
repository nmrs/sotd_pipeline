"""Unit tests for the aggregate run module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
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

            with patch("sotd.aggregate.run.get_enriched_file_path") as mock_path:
                mock_path.return_value = enriched_file
                result = process_month(2025, 1, args)

        # Should still succeed but with empty razors list
        assert result["status"] == "success"
        assert result["aggregations"]["razors"] == []
        assert result["aggregations"]["blades"] == []


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

                main(["--out-dir", "data"])

                # Verify run_aggregate was called
                mock_run.assert_called_once()

    def test_month_argument(self):
        """Test with --month argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--month", "2025-04", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_year_argument(self):
        """Test with --year argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--year", "2025", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_range_argument(self):
        """Test with --range argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--range", "2025-01:2025-03", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_start_end_arguments(self):
        """Test with --start and --end arguments."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--start", "2025-01", "--end", "2025-03", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_debug_argument(self):
        """Test with --debug argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--debug", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_force_argument(self):
        """Test with --force argument."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            main(["--force", "--out-dir", "data"])

            # Verify run_aggregate was called
            mock_run.assert_called_once()

    def test_output_directory_creation_in_main(self):
        """Test output directory creation in main function."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            with tempfile.TemporaryDirectory() as temp_dir:
                main(["--out-dir", temp_dir])

                # Verify run_aggregate was called
                mock_run.assert_called_once()

    def test_output_directory_creation_error_in_main(self):
        """Test output directory creation error in main function."""
        with patch("sotd.aggregate.run.run_aggregate") as mock_run:
            # Try to create a directory in a location that should fail
            main(["--out-dir", "/root/nonexistent"])

            # Should handle the error gracefully
            # run_aggregate might not be called due to the error
