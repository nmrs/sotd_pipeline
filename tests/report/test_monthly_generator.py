"""Tests for the unified monthly report generator."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from sotd.report.monthly_generator import MonthlyReportGenerator


class TestMonthlyReportGenerator:
    """Test the unified monthly report generator."""

    def test_init_with_hardware_type(self):
        """Test initialization with hardware report type."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        assert generator.report_type == "hardware"
        assert generator.metadata == metadata
        assert generator.data == data
        assert generator.comparison_data == {}
        assert generator.debug is False

    def test_init_with_software_type(self):
        """Test initialization with software report type."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"soaps": []}

        generator = MonthlyReportGenerator("software", metadata, data)

        assert generator.report_type == "software"
        assert generator.metadata == metadata
        assert generator.data == data

    def test_init_with_comparison_data(self):
        """Test initialization with comparison data."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}
        comparison_data = {"previous_month": {"razors": []}}

        generator = MonthlyReportGenerator("hardware", metadata, data, comparison_data)

        assert generator.comparison_data == comparison_data

    def test_init_with_debug_enabled(self):
        """Test initialization with debug enabled."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}

        generator = MonthlyReportGenerator("hardware", metadata, data, debug=True)

        assert generator.debug is True

    def test_init_with_custom_template_path(self):
        """Test initialization with custom template path."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}
        template_path = "/custom/templates"

        generator = MonthlyReportGenerator("hardware", metadata, data, template_path=template_path)

        assert generator.template_path == template_path

    def test_generate_header_deprecated(self):
        """Test that generate_header returns empty string (deprecated)."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        result = generator.generate_header()
        assert result == ""

    def test_generate_tables_deprecated(self):
        """Test that generate_tables returns empty list (deprecated)."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        result = generator.generate_tables()
        assert result == []

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_generate_notes_and_caveats_hardware(
        self, mock_table_generator_class, mock_template_processor_class
    ):
        """Test generate_notes_and_caveats for hardware reports."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = ["razors", "blades"]
        mock_table_generator.generate_table_by_name.side_effect = [
            "| Razor | Shaves |\n|-------|--------|\n| Test | 10 |",
            "| Blade | Shaves |\n|-------|--------|\n| Test | 10 |",
        ]
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = (
            "# Hardware Report\n\n{{tables.razors}}\n\n{{tables.blades}}"
        )
        mock_processor.process_template.return_value = "Generated report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {
            "month": "2025-01",
            "total_shaves": 1000,
            "unique_shavers": 50,
            "avg_shaves_per_user": 20.0,
            "median_shaves_per_user": 18.0,
            "unique_razors": 25,
            "unique_blades": 30,
            "unique_brushes": 20,
            "unique_soaps": 0,
            "unique_brands": 0,
            "total_samples": 0,
            "sample_percentage": 0.0,
            "sample_users": 0,
            "sample_brands": 0,
        }
        data = {"razors": [], "blades": []}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        result = generator.generate_notes_and_caveats()

        # Verify template processor was called correctly
        mock_template_processor_class.assert_called_once()
        mock_processor.process_template.assert_called_once_with(
            "hardware",
            {
                "month_year": "January 2025",
                "total_shaves": "1,000",
                "unique_shavers": "50",
                "avg_shaves_per_user": "20.0",
                "median_shaves_per_user": "18.0",
                "unique_razors": "25",
                "unique_blades": "30",
                "unique_brushes": "20",
                "unique_soaps": "0",
                "unique_brands": "0",
                "total_samples": "0",
                "sample_percentage": "0.0%",
                "sample_users": "0",
                "sample_brands": "0",
            },
            {
                "{{tables.razors}}": "| Razor | Shaves |\n|-------|--------|\n| Test | 10 |",
                "{{tables.blades}}": "| Blade | Shaves |\n|-------|--------|\n| Test | 10 |",
            },
        )

        assert result == "Generated report"

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_generate_notes_and_caveats_software(
        self, mock_table_generator_class, mock_template_processor_class
    ):
        """Test generate_notes_and_caveats for software reports."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = ["soaps", "scents"]
        mock_table_generator.generate_table_by_name.side_effect = [
            "| Soap | Shaves |\n|------|--------|\n| Test | 10 |",
            "| Scent | Shaves |\n|------|--------|\n| Test | 10 |",
        ]
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = (
            "# Software Report\n\n{{tables.soaps}}\n\n{{tables.scents}}"
        )
        mock_processor.process_template.return_value = "Generated software report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {
            "month": "2025-01",
            "total_shaves": 1000,
            "unique_shavers": 50,
            "avg_shaves_per_user": 20.0,
            "median_shaves_per_user": 18.0,
            "unique_razors": 0,
            "unique_blades": 0,
            "unique_brushes": 0,
            "unique_soaps": 25,
            "unique_brands": 20,
            "total_samples": 100,
            "sample_percentage": 10.0,
            "sample_users": 15,
            "sample_brands": 8,
        }
        data = {"soaps": [], "scents": []}

        generator = MonthlyReportGenerator("software", metadata, data)

        result = generator.generate_notes_and_caveats()

        # Verify template processor was called correctly
        mock_processor.process_template.assert_called_once_with(
            "software",
            {
                "month_year": "January 2025",
                "total_shaves": "1,000",
                "unique_shavers": "50",
                "avg_shaves_per_user": "20.0",
                "median_shaves_per_user": "18.0",
                "unique_razors": "0",
                "unique_blades": "0",
                "unique_brushes": "0",
                "unique_soaps": "25",
                "unique_brands": "20",
                "total_samples": "100",
                "sample_percentage": "10.0%",
                "sample_users": "15",
                "sample_brands": "8",
            },
            {
                "{{tables.soaps}}": "| Soap | Shaves |\n|------|--------|\n| Test | 10 |",
                "{{tables.scents}}": "| Scent | Shaves |\n|------|--------|\n| Test | 10 |",
            },
        )

        assert result == "Generated software report"

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_generate_notes_and_caveats_with_custom_template_path(
        self, mock_table_generator_class, mock_template_processor_class
    ):
        """Test generate_notes_and_caveats with custom template path."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = []
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = "# Custom Report\n\nNo tables"
        mock_processor.process_template.return_value = "Generated report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {}
        template_path = "/custom/templates"

        generator = MonthlyReportGenerator("hardware", metadata, data, template_path=template_path)

        generator.generate_notes_and_caveats()

        # Verify template processor was created with custom path
        mock_template_processor_class.assert_called_once_with(Path(template_path))

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_generate_notes_and_caveats_table_generation_error(
        self, mock_table_generator_class, mock_template_processor_class
    ):
        """Test generate_notes_and_caveats handles table generation errors."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = ["razors", "blades"]
        mock_table_generator.generate_table_by_name.side_effect = [
            "| Razor | Shaves |\n|-------|--------|\n| Test | 10 |",
            Exception("Table generation failed"),
        ]
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = (
            "# Hardware Report\n\n{{tables.razors}}\n\n{{tables.blades}}"
        )
        mock_processor.process_template.return_value = "Generated report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": []}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        # Test that error handling follows fail-fast approach
        with pytest.raises(
            ValueError, 
            match=(
                "Table generation error in template 'hardware': "
                "Failed to generate table 'blades' - Table generation failed"
            )
        ):
            generator.generate_notes_and_caveats()

    def test_month_parsing_valid_format(self):
        """Test month parsing with valid YYYY-MM format."""
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        # Access the month parsing logic through generate_notes_and_caveats
        with patch("sotd.report.monthly_generator.TemplateProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor.get_template.return_value = "# Hardware Report\n\nNo tables"
            mock_processor.process_template.return_value = "Generated report"
            mock_processor_class.return_value = mock_processor

            with patch(
                "sotd.report.monthly_generator.TableGenerator"
            ) as mock_table_generator_class:
                mock_table_generator = Mock()
                mock_table_generator.get_available_table_names.return_value = []
                mock_table_generator_class.return_value = mock_table_generator

                generator.generate_notes_and_caveats()

                # Verify month was parsed correctly
                call_args = mock_processor.process_template.call_args[0]
                variables = call_args[1]
                assert variables["month_year"] == "January 2025"

    def test_month_parsing_invalid_format(self):
        """Test month parsing with invalid format falls back to original."""
        metadata = {"month": "invalid-month", "total_shaves": 100}
        data = {}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        # Access the month parsing logic through generate_notes_and_caveats
        with patch("sotd.report.monthly_generator.TemplateProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor.get_template.return_value = "# Hardware Report\n\nNo tables"
            mock_processor.process_template.return_value = "Generated report"
            mock_processor_class.return_value = mock_processor

            with patch(
                "sotd.report.monthly_generator.TableGenerator"
            ) as mock_table_generator_class:
                mock_table_generator = Mock()
                mock_table_generator.get_available_table_names.return_value = []
                mock_table_generator_class.return_value = mock_table_generator

                generator.generate_notes_and_caveats()

                # Verify month fallback was used
                call_args = mock_processor.process_template.call_args[0]
                variables = call_args[1]
                assert variables["month_year"] == "invalid-month"

    def test_month_parsing_none_month(self):
        """Test month parsing with None month falls back to None."""
        metadata = {"month": None, "total_shaves": 100}
        data = {}

        generator = MonthlyReportGenerator("hardware", metadata, data)

        # Test the month parsing logic by calling generate_notes_and_caveats
        # and checking what variables are passed to the template processor
        with patch("sotd.report.monthly_generator.TemplateProcessor") as mock_processor_class:
            mock_processor = Mock()
            mock_processor.get_template.return_value = "# Hardware Report\n\nNo tables"
            mock_processor.process_template.return_value = "Generated report"
            mock_processor_class.return_value = mock_processor

            with patch(
                "sotd.report.monthly_generator.TableGenerator"
            ) as mock_table_generator_class:
                mock_table_generator = Mock()
                mock_table_generator.get_available_table_names.return_value = []
                mock_table_generator_class.return_value = mock_table_generator

                generator.generate_notes_and_caveats()

                # Verify month fallback was used
                # When month is None, get() returns None, and parsing fails,
                # so month_year becomes None
                call_args = mock_processor.process_template.call_args[0]
                variables = call_args[1]
                assert variables["month_year"] is None

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_debug_output_enabled(self, mock_table_generator_class, mock_template_processor_class):
        """Test debug output when debug is enabled."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = []
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = "# Hardware Report\n\nNo tables"
        mock_processor.process_template.return_value = "Generated report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": [{"name": "Test Razor"}]}

        generator = MonthlyReportGenerator("hardware", metadata, data, debug=True)

        # Capture print output
        with patch("builtins.print") as mock_print:
            generator.generate_notes_and_caveats()

            # Verify debug output was generated
            assert mock_print.call_count >= 3  # At least 3 debug prints
            debug_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Creating TableGenerator" in call for call in debug_calls)
            assert any("self.data keys:" in call for call in debug_calls)
            assert any("Processing template:" in call for call in debug_calls)

    @patch("sotd.report.monthly_generator.TemplateProcessor")
    @patch("sotd.report.monthly_generator.TableGenerator")
    def test_debug_output_disabled(self, mock_table_generator_class, mock_template_processor_class):
        """Test no debug output when debug is disabled."""
        # Mock dependencies
        mock_table_generator = Mock()
        mock_table_generator.get_available_table_names.return_value = []
        mock_table_generator_class.return_value = mock_table_generator

        mock_processor = Mock()
        mock_processor.get_template.return_value = "# Hardware Report\n\nNo tables"
        mock_processor.process_template.return_value = "Generated report"
        mock_template_processor_class.return_value = mock_processor

        # Test data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {"razors": [{"name": "Test Razor"}]}

        generator = MonthlyReportGenerator("hardware", metadata, data, debug=False)

        # Capture print output
        with patch("builtins.print") as mock_print:
            generator.generate_notes_and_caveats()

            # Verify no debug output was generated
            assert mock_print.call_count == 0
