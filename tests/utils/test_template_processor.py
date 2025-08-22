"""Tests for the template processor utility."""

import pytest
from pathlib import Path

from sotd.utils.template_processor import TemplateProcessor


class TestTemplateProcessor:
    """Test the TemplateProcessor class."""

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        processor = TemplateProcessor()
        assert processor.templates_path == Path("data/report_templates")

    def test_init_with_custom_path(self):
        """Test initialization with custom path."""
        custom_path = Path("/custom/templates")
        processor = TemplateProcessor(custom_path)
        assert processor.templates_path == custom_path

    def test_load_templates_directory_success(self, tmp_path):
        """Test loading templates from directory successfully."""
        # Create a template directory
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create hardware template
        hardware_file = template_dir / "hardware.md"
        hardware_file.write_text("# Hardware Report\n\n{{tables.razors}}")

        # Create software template
        software_file = template_dir / "software.md"
        software_file.write_text("# Software Report\n\n{{tables.soaps}}")

        processor = TemplateProcessor(template_dir)
        templates = processor._load_templates()

        assert "hardware" in templates
        assert "software" in templates
        assert templates["hardware"] == "# Hardware Report\n\n{{tables.razors}}"
        assert templates["software"] == "# Software Report\n\n{{tables.soaps}}"

    def test_load_templates_directory_not_found(self, tmp_path):
        """Test loading templates from non-existent directory."""
        non_existent_dir = tmp_path / "non_existent"
        processor = TemplateProcessor(non_existent_dir)

        with pytest.raises(FileNotFoundError):
            processor._load_templates()

    def test_load_templates_directory_empty(self, tmp_path):
        """Test loading templates from empty directory."""
        empty_dir = tmp_path / "empty_templates"
        empty_dir.mkdir()

        processor = TemplateProcessor(empty_dir)

        with pytest.raises(ValueError, match="No template files found"):
            processor._load_templates()

    def test_load_templates_not_directory(self, tmp_path):
        """Test loading templates when path is not a directory."""
        file_path = tmp_path / "not_a_dir"
        file_path.write_text("not a directory")

        processor = TemplateProcessor(file_path)

        with pytest.raises(NotADirectoryError):
            processor._load_templates()

    def test_get_template_success(self, tmp_path):
        """Test getting a template successfully."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        hardware_file = template_dir / "hardware.md"
        hardware_file.write_text("# Hardware Report\n\n{{tables.razors}}")

        processor = TemplateProcessor(template_dir)
        template = processor.get_template("hardware")
        assert template == "# Hardware Report\n\n{{tables.razors}}"

    def test_get_template_not_found(self, tmp_path):
        """Test getting a non-existent template."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create a template file so the directory is not empty
        template_file = template_dir / "existing.md"
        template_file.write_text("Existing template")

        processor = TemplateProcessor(template_dir)

        with pytest.raises(KeyError, match="Template 'missing' not found"):
            processor.get_template("missing")

    def test_process_template_variables_only(self, tmp_path):
        """Test processing template with variables only."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "test.md"
        template_file.write_text("Hello {{name}}, you have {{count}} items.")

        processor = TemplateProcessor(template_dir)
        result = processor.process_template("test", {"name": "John", "count": 5})
        assert result == "Hello John, you have 5 items."

    def test_process_template_with_tables(self, tmp_path):
        """Test processing template with tables."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "test.md"
        template_file.write_text("Report:\n\n{{tables.summary}}\n\n{{tables.details}}")

        processor = TemplateProcessor(template_dir)
        result = processor.process_template(
            "test", 
            {}, 
            {"{{tables.summary}}": "Summary table", "{{tables.details}}": "Details table"}
        )
        assert result == "Report:\n\nSummary table\n\nDetails table"

    def test_process_template_variables_and_tables(self, tmp_path):
        """Test processing template with both variables and tables."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "test.md"
        template_file.write_text("Report for {{month}}:\n\n{{tables.summary}}")

        processor = TemplateProcessor(template_dir)
        result = processor.process_template(
            "test", {"month": "January"}, {"{{tables.summary}}": "Monthly summary"}
        )
        assert result == "Report for January:\n\nMonthly summary"

    def test_list_templates(self, tmp_path):
        """Test listing available templates."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        # Create templates in non-alphabetical order
        (template_dir / "software.md").write_text("Software template")
        (template_dir / "hardware.md").write_text("Hardware template")
        (template_dir / "annual.md").write_text("Annual template")

        processor = TemplateProcessor(template_dir)
        templates = processor.list_templates()

        # Should be sorted alphabetically
        assert templates == ["annual", "hardware", "software"]

    def test_template_caching(self, tmp_path):
        """Test that templates are cached after first load."""
        template_dir = tmp_path / "report_templates"
        template_dir.mkdir()

        template_file = template_dir / "test.md"
        template_file.write_text("Test content")

        processor = TemplateProcessor(template_dir)

        # First call should load templates
        templates1 = processor._load_templates()
        assert "test" in templates1

        # Second call should use cached templates
        templates2 = processor._load_templates()
        assert templates1 is templates2  # Same object reference
