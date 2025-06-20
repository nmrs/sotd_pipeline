"""Integration tests for template processor with report generators."""

from sotd.report.hardware_report import HardwareReportGenerator
from sotd.report.software_report import SoftwareReportGenerator


class TestTemplateIntegration:
    """Test integration between report generators and template processor."""

    def test_hardware_report_with_template(self, template_file):
        """Test hardware report uses template processor correctly."""
        # Create report generator with custom template path
        metadata = {
            "total_shaves": 1234,
            "unique_shavers": 567,
            "avg_shaves_per_user": 2.2,
        }
        data = {}

        generator = HardwareReportGenerator(metadata, data, template_path=str(template_file))
        result = generator.generate_notes_and_caveats()

        # Check that template variables were replaced
        assert "**1,234 shaves**" in result
        assert "**567 unique users**" in result
        assert "**2.2 shaves**" in result
        assert "Custom template content for testing" in result

    def test_software_report_with_template(self, template_file):
        """Test software report uses template processor correctly."""
        # Create report generator
        metadata = {}
        data = {}

        generator = SoftwareReportGenerator(metadata, data, template_path=str(template_file))
        result = generator.generate_notes_and_caveats()

        # Check that template content was used
        assert "Custom software template content" in result
        assert "This is a test template" in result
