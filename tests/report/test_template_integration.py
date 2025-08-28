"""Integration tests for template processor with report generators."""

from sotd.report.monthly_generator import MonthlyReportGenerator


class TestTemplateIntegration:
    """Test integration between report generators and template processor."""

    def test_hardware_report_with_directory_templates(self, template_dir):
        """Test hardware report uses directory-based template processor correctly."""
        # Create report generator with custom template directory
        metadata = {
            "month": "2025-01",
            "total_shaves": 1234,
            "unique_shavers": 567,
            "avg_shaves_per_user": 2.2,
        }
        data = {"razors": [{"name": "Test Razor", "shaves": 1}]}  # Minimal valid data

        generator = MonthlyReportGenerator(
            "hardware", metadata, data, template_path=str(template_dir)
        )

        # Generate notes and caveats using template
        notes = generator.generate_notes_and_caveats()

        # Verify template variables are replaced
        assert "Welcome to your SOTD Hardware Report for January 2025" in notes
        assert "1,234 shave reports from 567 distinct shavers" in notes
        assert "Average shaves per user: 2.2" in notes
        assert "Custom template content for testing" in notes

    def test_software_report_with_directory_templates(self, template_dir):
        """Test software report uses directory-based template processor correctly."""
        # Create report generator with custom template directory
        metadata = {
            "month": "2025-01",
            "total_shaves": 1234,
            "unique_shavers": 567,
            "unique_soaps": 100,
            "unique_brands": 25,
        }
        data = {"soaps": [{"name": "Test Soap", "shaves": 1}]}  # Minimal valid data

        generator = MonthlyReportGenerator(
            "software", metadata, data, template_path=str(template_dir)
        )

        # Generate notes and caveats using template
        notes = generator.generate_notes_and_caveats()

        # Verify template variables are replaced
        assert "Welcome to your SOTD Lather Log for January 2025" in notes
        assert "1,234 shave reports from 567 distinct shavers" in notes
        assert "100 distinct soaps from 25 distinct brands" in notes
