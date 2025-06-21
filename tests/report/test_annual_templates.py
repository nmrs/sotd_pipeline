# noqa
"""
Tests for annual template system functionality.

This module tests the annual template system, including template loading for annual sections,
variable substitution in annual templates, section validation and structure, integration with
existing template system, error handling for malformed templates, template performance and
caching, and backward compatibility with monthly templates.
"""

import pytest

from sotd.utils.template_processor import TemplateProcessor


class TestAnnualTemplateSystem:
    """Test the annual template system functionality."""

    def test_annual_template_loading(self, tmp_path):
        """Test loading annual templates from YAML file."""
        # Create test template file with annual sections
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}

    ## Annual Summary

    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}} were analyzed to produce this report.

    ## Razors

    {{tables.razors}}

annual_software:
  report_template: |
    Welcome to your Annual SOTD Lather Log for {{year}}

    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}} were analyzed to produce this report.

    ## Soaps

    {{tables.soaps}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test that annual templates are loaded correctly
        templates = processor._load_templates()
        assert "annual_hardware" in templates
        assert "annual_software" in templates
        assert "report_template" in templates["annual_hardware"]
        assert "report_template" in templates["annual_software"]

    def test_annual_variable_substitution(self, tmp_path):
        """Test variable substitution in annual templates."""
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}
    
    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}}.
    * Average shaves per user: {{avg_shaves_per_user}}
    * Included months: {{included_months}}
    * Missing months: {{missing_months}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        variables = {
            "year": "2024",
            "total_shaves": "12,345",
            "unique_shavers": "567",
            "avg_shaves_per_user": "21.8",
            "included_months": "12",
            "missing_months": "0",
        }

        result = processor.render_template("annual_hardware", "report_template", variables)

        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "12,345 shave reports from 567 distinct shavers during 2024" in result
        assert "Average shaves per user: 21.8" in result
        assert "Included months: 12" in result
        assert "Missing months: 0" in result

    def test_annual_template_section_validation(self, tmp_path):
        """Test section validation and structure for annual templates."""
        template_content = """
annual_hardware:
  report_template: |
    Annual hardware report template
  summary_template: |
    Annual summary template
annual_software:
  report_template: |
    Annual software report template
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test valid sections
        result1 = processor.render_template("annual_hardware", "report_template", {})
        assert "Annual hardware report template" in result1

        result2 = processor.render_template("annual_hardware", "summary_template", {})
        assert "Annual summary template" in result2

        result3 = processor.render_template("annual_software", "report_template", {})
        assert "Annual software report template" in result3

    def test_annual_template_integration_with_existing_system(self, tmp_path):
        """Test integration with existing template system."""
        template_content = """
hardware:
  report_template: |
    Monthly hardware report for {{month_year}}
    
    {{tables.razors}}

annual_hardware:
  report_template: |
    Annual hardware report for {{year}}
    
    {{tables.razors}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test that both monthly and annual templates coexist
        monthly_result = processor.render_template(
            "hardware", "report_template", {"month_year": "January 2024"}
        )
        annual_result = processor.render_template(
            "annual_hardware", "report_template", {"year": "2024"}
        )

        assert "Monthly hardware report for January 2024" in monthly_result
        assert "Annual hardware report for 2024" in annual_result

    def test_annual_template_error_handling_malformed_templates(self, tmp_path):
        """Test error handling for malformed annual templates."""
        # Test with invalid YAML
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}
    * This template has unclosed braces
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Should handle malformed template gracefully
        variables = {"year": "2024"}
        result = processor.render_template("annual_hardware", "report_template", variables)

        # Should still process what it can - unclosed braces are passed through
        assert "Welcome to your Annual SOTD Hardware Report for {{year}" in result
        assert "This template has unclosed braces" in result

    def test_annual_template_missing_section(self, tmp_path):
        """Test error handling for missing annual template sections."""
        template_content = """
annual_hardware:
  report_template: |
    Annual hardware report template
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test missing section
        with pytest.raises(KeyError, match="Section 'missing_section' not found"):
            processor.render_template("annual_hardware", "missing_section", {})

    def test_annual_template_missing_template(self, tmp_path):
        """Test error handling for missing annual templates."""
        template_content = """
hardware:
  report_template: |
    Monthly hardware report template
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test missing template
        with pytest.raises(KeyError, match="Template 'annual_hardware' not found"):
            processor.render_template("annual_hardware", "report_template", {})

    def test_annual_template_performance_and_caching(self, tmp_path):
        """Test template performance and caching."""
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}
    
    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}}.
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        variables = {"year": "2024", "total_shaves": "12,345", "unique_shavers": "567"}

        # First render should load templates
        result1 = processor.render_template("annual_hardware", "report_template", variables)

        # Second render should use cached templates
        result2 = processor.render_template("annual_hardware", "report_template", variables)

        # Results should be identical
        assert result1 == result2
        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result1
        assert "12,345 shave reports from 567 distinct shavers during 2024" in result1

    def test_annual_template_backward_compatibility(self, tmp_path):
        """Test backward compatibility with monthly templates."""
        template_content = """
hardware:
  report_template: |
    Monthly hardware report for {{month_year}}
    
    {{tables.razors}}

annual_hardware:
  report_template: |
    Annual hardware report for {{year}}
    
    {{tables.razors}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        # Test that existing monthly templates still work
        monthly_variables = {"month_year": "January 2024"}
        monthly_result = processor.render_template("hardware", "report_template", monthly_variables)
        assert "Monthly hardware report for January 2024" in monthly_result

        # Test that new annual templates work
        annual_variables = {"year": "2024"}
        annual_result = processor.render_template(
            "annual_hardware", "report_template", annual_variables
        )
        assert "Annual hardware report for 2024" in annual_result

    def test_annual_template_table_placeholders(self, tmp_path):
        """Test table placeholder replacement in annual templates."""
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}
    
    ## Razors
    
    {{tables.razors}}
    
    ## Blades
    
    {{tables.blades}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        variables = {"year": "2024"}

        # Mock table generator
        class MockTableGenerator:
            def generate_table_by_name(self, table_name):
                if table_name == "razors":
                    return "| Razor | Shaves | Users |\n|-------|--------|-------|\n| Test Razor | 100 | 50 |"
                elif table_name == "blades":
                    return "| Blade | Shaves | Users |\n|-------|--------|-------|\n| Test Blade | 150 | 75 |"
                else:
                    return f"*No data available for {table_name}*"

        table_generator = MockTableGenerator()

        result = processor.render_template(
            "annual_hardware", "report_template", variables, table_generator
        )

        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "## Razors" in result
        assert "## Blades" in result
        assert "Test Razor" in result
        assert "Test Blade" in result

    def test_annual_template_available_templates(self, tmp_path):
        """Test getting available annual templates."""
        template_content = """
hardware:
  report_template: |
    Monthly hardware report template

annual_hardware:
  report_template: |
    Annual hardware report template
  summary_template: |
    Annual summary template

annual_software:
  report_template: |
    Annual software report template
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        available_templates = processor.get_available_templates()

        assert "hardware" in available_templates
        assert "annual_hardware" in available_templates
        assert "annual_software" in available_templates
        assert "report_template" in available_templates["hardware"]
        assert "report_template" in available_templates["annual_hardware"]
        assert "summary_template" in available_templates["annual_hardware"]
        assert "report_template" in available_templates["annual_software"]

    def test_annual_template_table_placeholders_extraction(self, tmp_path):
        """Test extraction of table placeholders from annual templates."""
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}
    
    ## Razors
    
    {{tables.razors}}
    
    ## Blades
    
    {{tables.blades}}
    
    ## Brushes
    
    {{tables.brushes}}
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        placeholders = processor.get_available_table_placeholders("annual_hardware")

        assert "razors" in placeholders
        assert "blades" in placeholders
        assert "brushes" in placeholders
        assert len(placeholders) == 3

    def test_annual_template_complex_variables(self, tmp_path):
        """Test complex variable substitution in annual templates."""
        template_content = """
annual_hardware:
  report_template: |
    Welcome to your Annual SOTD Hardware Report for {{year}}
    
    ## Annual Statistics
    
    * Total shaves: {{total_shaves}}
    * Unique shavers: {{unique_shavers}}
    * Average shaves per user: {{avg_shaves_per_user}}
    * Included months: {{included_months}}
    * Missing months: {{missing_months}}
    * Data completeness: {{data_completeness}}%
"""
        template_file = tmp_path / "test_templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        variables = {
            "year": "2024",
            "total_shaves": "12,345",
            "unique_shavers": "567",
            "avg_shaves_per_user": "21.8",
            "included_months": "12",
            "missing_months": "0",
            "data_completeness": "100.0",
        }

        result = processor.render_template("annual_hardware", "report_template", variables)

        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "Total shaves: 12,345" in result
        assert "Unique shavers: 567" in result
        assert "Average shaves per user: 21.8" in result
        assert "Included months: 12" in result
        assert "Missing months: 0" in result
        assert "Data completeness: 100.0%" in result
