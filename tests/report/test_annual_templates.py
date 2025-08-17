# noqa
"""
Tests for annual template system functionality.

This module tests the annual template system, including template loading for annual templates,
variable substitution in annual templates, template validation and structure, integration with
existing template system, error handling for malformed templates, template performance and
caching, and compatibility with monthly templates.
"""

import pytest

from sotd.utils.template_processor import TemplateProcessor


class TestAnnualTemplateSystem:
    """Test the annual template system functionality."""

    def test_annual_template_loading(self, tmp_path):
        """Test loading annual templates from directory."""
        # Create test template directory with annual templates
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create annual hardware template
        annual_hardware_file = template_dir / "annual_hardware.md"
        annual_hardware_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "## Annual Summary\n\n"
            "* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers "
            "during {{year}} were analyzed to produce this report.\n\n"
            "## Razors\n\n"
            "{{tables.razors}}"
        )

        # Create annual software template
        annual_software_file = template_dir / "annual_software.md"
        annual_software_file.write_text(
            "# Annual Software Report - {{year}}\n\n"
            "* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers "
            "during {{year}} were analyzed to produce this report.\n\n"
            "## Soaps\n\n"
            "{{tables.soaps}}"
        )

        processor = TemplateProcessor(template_dir)

        # Test that annual templates are loaded correctly
        templates = processor._load_templates()
        assert "annual_hardware" in templates
        assert "annual_software" in templates
        assert "Annual Hardware Report" in templates["annual_hardware"]
        assert "Annual Software Report" in templates["annual_software"]

    def test_annual_variable_substitution(self, tmp_path):
        """Test variable substitution in annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}}.\n"
            "* Average shaves per user: {{avg_shaves_per_user}}\n"
            "* Included months: {{included_months}}\n"
            "* Missing months: {{missing_months}}"
        )

        processor = TemplateProcessor(template_dir)

        variables = {
            "year": "2024",
            "total_shaves": "12,345",
            "unique_shavers": "567",
            "avg_shaves_per_user": "21.8",
            "included_months": "12",
            "missing_months": "0",
        }

        result = processor.process_template("annual_hardware", variables)

        assert "Annual Hardware Report - 2024" in result
        assert "12,345 shave reports from 567 distinct shavers during 2024" in result
        assert "Average shaves per user: 21.8" in result
        assert "Included months: 12" in result
        assert "Missing months: 0" in result

    def test_annual_template_validation(self, tmp_path):
        """Test template validation and structure for annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report\n\n"
            "Annual hardware report template\n\n"
            "## Summary\n\n"
            "Annual summary template"
        )

        processor = TemplateProcessor(template_dir)

        # Test valid template
        result = processor.process_template("annual_hardware", {})
        assert "Annual Hardware Report" in result
        assert "Annual hardware report template" in result
        assert "Annual summary template" in result

    def test_annual_template_integration_with_existing_system(self, tmp_path):
        """Test integration with existing template system."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create monthly hardware template
        monthly_file = template_dir / "hardware.md"
        monthly_file.write_text(
            "# Hardware Report - {{month_year}}\n\n"
            "Monthly hardware report for {{month_year}}\n\n"
            "{{tables.razors}}"
        )

        # Create annual hardware template
        annual_file = template_dir / "annual_hardware.md"
        annual_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "Annual hardware report for {{year}}\n\n"
            "{{tables.razors}}"
        )

        processor = TemplateProcessor(template_dir)

        # Test that both monthly and annual templates coexist
        monthly_result = processor.process_template("hardware", {"month_year": "January 2024"})
        annual_result = processor.process_template("annual_hardware", {"year": "2024"})

        assert "Monthly hardware report for January 2024" in monthly_result
        assert "Annual hardware report for 2024" in annual_result

    def test_annual_template_error_handling_malformed_templates(self, tmp_path):
        """Test error handling for malformed annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Test with template that has unclosed braces (should still work for basic processing)
        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}\n"
            "* This template has unclosed braces\n"
            "* But basic processing should still work"
        )

        processor = TemplateProcessor(template_dir)

        # Should handle malformed template gracefully
        variables = {"year": "2024"}
        result = processor.process_template("annual_hardware", variables)

        # The unclosed brace won't be replaced, but the rest should work
        assert "Annual Hardware Report - {{year}" in result
        assert "This template has unclosed braces" in result

    def test_annual_template_missing_template(self, tmp_path):
        """Test error handling for missing annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create only monthly template
        template_file = template_dir / "hardware.md"
        template_file.write_text("Monthly hardware report template")

        processor = TemplateProcessor(template_dir)

        # Test missing template
        with pytest.raises(KeyError, match="Template 'annual_hardware' not found"):
            processor.process_template("annual_hardware", {})

    def test_annual_template_performance_and_caching(self, tmp_path):
        """Test template performance and caching."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}}."
        )

        processor = TemplateProcessor(template_dir)

        variables = {"year": "2024", "total_shaves": "12,345", "unique_shavers": "567"}

        # First render should load templates
        result1 = processor.process_template("annual_hardware", variables)
        assert "Annual Hardware Report - 2024" in result1
        assert "12,345 shave reports from 567 distinct shavers during 2024" in result1

        # Second render should use cached templates
        result2 = processor.process_template("annual_hardware", variables)
        assert result1 == result2

        # Verify caching by checking that templates are loaded only once
        templates1 = processor._load_templates()
        templates2 = processor._load_templates()
        assert templates1 is templates2  # Same object reference

    def test_annual_template_table_placeholders(self, tmp_path):
        """Test table placeholder replacement in annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "## Razors\n\n"
            "{{tables.razors}}\n\n"
            "## Blades\n\n"
            "{{tables.blades}}"
        )

        processor = TemplateProcessor(template_dir)

        variables = {"year": "2024"}
        tables = {
            "razors": "| Razor | Shaves | Users |\n|-------|--------|-------|\n| Test Razor | 100 | 50 |",
            "blades": "| Blade | Shaves | Users |\n|-------|--------|-------|\n| Test Blade | 150 | 75 |",
        }

        result = processor.process_template("annual_hardware", variables, tables)

        assert "Annual Hardware Report - 2024" in result
        assert "| Test Razor | 100 | 50 |" in result
        assert "| Test Blade | 150 | 75 |" in result

    def test_annual_template_available_templates(self, tmp_path):
        """Test getting available annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create templates
        (template_dir / "hardware.md").write_text("Monthly hardware report template")
        (template_dir / "annual_hardware.md").write_text("Annual hardware report template")
        (template_dir / "annual_software.md").write_text("Annual software report template")

        processor = TemplateProcessor(template_dir)

        available_templates = processor.list_templates()

        # Should include all templates, sorted alphabetically
        assert "annual_hardware" in available_templates
        assert "annual_software" in available_templates
        assert "hardware" in available_templates
        assert available_templates == ["annual_hardware", "annual_software", "hardware"]

    def test_annual_template_complex_variables(self, tmp_path):
        """Test complex variable substitution in annual templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "## Annual Statistics\n\n"
            "* Total shaves: {{total_shaves}}\n"
            "* Unique shavers: {{unique_shavers}}\n"
            "* Average shaves per user: {{avg_shaves_per_user}}\n"
            "* Included months: {{included_months}}\n"
            "* Missing months: {{missing_months}}\n"
            "* Data completeness: {{data_completeness}}%"
        )

        processor = TemplateProcessor(template_dir)

        variables = {
            "year": "2024",
            "total_shaves": "12,345",
            "unique_shavers": "567",
            "avg_shaves_per_user": "21.8",
            "included_months": "12",
            "missing_months": "0",
            "data_completeness": "100.0",
        }

        result = processor.process_template("annual_hardware", variables)

        assert "Annual Hardware Report - 2024" in result
        assert "Total shaves: 12,345" in result
        assert "Unique shavers: 567" in result
        assert "Average shaves per user: 21.8" in result
        assert "Included months: 12" in result
        assert "Missing months: 0" in result
        assert "Data completeness: 100.0%" in result

    def test_annual_template_with_missing_months(self, tmp_path):
        """Test annual template with missing months scenario."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "annual_hardware.md"
        template_file.write_text(
            "# Annual Hardware Report - {{year}}\n\n"
            "## Annual Summary\n\n"
            "* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}}.\n"
            "* Data includes {{included_months}} months of the year.\n"
            "{% if missing_months > 0 %}\n"
            "* Note: {{missing_months}} months were missing from the data set.\n"
            "{% endif %}"
        )

        processor = TemplateProcessor(template_dir)

        # Test with missing months
        variables_with_missing = {
            "year": "2024",
            "total_shaves": "10,000",
            "unique_shavers": "500",
            "included_months": "10",
            "missing_months": "2",
        }

        result = processor.process_template("annual_hardware", variables_with_missing)

        assert "Annual Hardware Report - 2024" in result
        assert "Data includes 10 months of the year" in result
        assert "Note: 2 months were missing from the data set" in result

        # Test with no missing months
        variables_no_missing = {
            "year": "2024",
            "total_shaves": "12,000",
            "unique_shavers": "600",
            "included_months": "12",
            "missing_months": "0",
        }

        result_no_missing = processor.process_template("annual_hardware", variables_no_missing)
        assert "Data includes 12 months of the year" in result_no_missing
        assert "Note: 0 months were missing from the data set" in result_no_missing
