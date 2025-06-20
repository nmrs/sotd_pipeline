"""Tests for the template processor utility."""

import pytest
from pathlib import Path

from sotd.utils.template_processor import TemplateProcessor


@pytest.fixture
def mock_template_content():
    """Shared mock template content for testing."""
    return """
hardware:
  report_template: |
    # Hardware Report for {{month}}
    
    **Total Shaves:** {{total_shaves}}
    **Unique Shavers:** {{unique_shavers}}
    **Avg Shaves/User:** {{avg_shaves_per_user}}
    
    ## Notes & Caveats
    
    This is a test template for integration testing.
    
    ## Tables
    
    ### Razor Statistics
    {{tables.razors}}
    
    ### Blade Statistics
    {{tables.blades}}
    
    ### Brush Statistics
    {{tables.brushes}}
    
    ### User Statistics
    {{tables.top-shavers}}

software:
  report_template: |
    # Software Report for {{month}}
    
    **Total Shaves:** {{total_shaves}}
    **Unique Shavers:** {{unique_shavers}}
    
    ## Notes & Caveats
    
    This is a test software template for integration testing.
    
    ## Tables
    
    ### Soap Statistics
    {{tables.soaps}}
    
    ### User Statistics
    {{tables.top-shavers}}
"""


@pytest.fixture
def mock_template_file(tmp_path, mock_template_content):
    """Create a mock template file for testing."""
    template_file = tmp_path / "report_templates.yaml"
    template_file.write_text(mock_template_content)
    return template_file


class TestTemplateProcessor:
    """Test cases for TemplateProcessor."""

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        processor = TemplateProcessor()
        assert processor.templates_path == Path("data/report_templates.yaml")

    def test_init_with_custom_path(self, tmp_path):
        """Test initialization with custom path."""
        custom_path = tmp_path / "custom_templates.yaml"
        processor = TemplateProcessor(custom_path)
        assert processor.templates_path == custom_path

    def test_load_templates_file_not_found(self, tmp_path):
        """Test loading templates when file doesn't exist."""
        non_existent_path = tmp_path / "nonexistent.yaml"
        processor = TemplateProcessor(non_existent_path)
        templates = processor._load_templates()
        assert templates == {}

    def test_load_templates_success(self, tmp_path):
        """Test loading templates successfully."""
        template_content = """
hardware:
  notes_and_caveats: |
    ## Notes & Caveats
    - **{{total_shaves}} shaves** from **{{unique_shavers}} users**
    - Users averaged **{{avg_shaves_per_user}} shaves** each

software:
  notes_and_caveats: |
    ## Notes & Caveats
    - Software refers to shaving soaps and creams
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)
        templates = processor._load_templates()

        assert "hardware" in templates
        assert "software" in templates
        assert "notes_and_caveats" in templates["hardware"]
        assert "notes_and_caveats" in templates["software"]

    def test_render_template_success(self, tmp_path):
        """Test successful template rendering."""
        template_content = """
hardware:
  notes_and_caveats: |
    ## Notes & Caveats
    - **{{total_shaves}} shaves** from **{{unique_shavers}} users**
    - Users averaged **{{avg_shaves_per_user}} shaves** each
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)
        variables = {
            "total_shaves": "1,234",
            "unique_shavers": "567",
            "avg_shaves_per_user": "2.2",
        }

        result = processor.render_template("hardware", "notes_and_caveats", variables)

        expected = """## Notes & Caveats
- **1,234 shaves** from **567 users**
- Users averaged **2.2 shaves** each"""

        assert result.strip() == expected.strip()

    def test_render_template_missing_template(self, tmp_path):
        """Test rendering with missing template."""
        template_content = """
hardware:
  notes_and_caveats: |
    ## Notes & Caveats
    - Test content
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        with pytest.raises(KeyError, match="Template 'software' not found"):
            processor.render_template("software", "notes_and_caveats", {})

    def test_render_template_missing_section(self, tmp_path):
        """Test rendering with missing section."""
        template_content = """
hardware:
  notes_and_caveats: |
    ## Notes & Caveats
    - Test content
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)

        with pytest.raises(KeyError, match="Section 'missing_section' not found"):
            processor.render_template("hardware", "missing_section", {})

    def test_get_available_templates(self, tmp_path):
        """Test getting available templates."""
        template_content = """
hardware:
  notes_and_caveats: |
    ## Notes & Caveats
    - Test content
  other_section: |
    Other content

software:
  notes_and_caveats: |
    ## Notes & Caveats
    - Software content
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)
        available = processor.get_available_templates()

        assert "hardware" in available
        assert "software" in available
        assert "notes_and_caveats" in available["hardware"]
        assert "other_section" in available["hardware"]
        assert "notes_and_caveats" in available["software"]

    def test_variable_replacement_edge_cases(self, tmp_path):
        """Test variable replacement with edge cases."""
        template_content = """
test:
  content: |
    - Number: {{number}}
    - String: {{string}}
    - Float: {{float}}
    - Zero: {{zero}}
    - Empty: {{empty}}
    - None: {{none}}
"""
        template_file = tmp_path / "templates.yaml"
        template_file.write_text(template_content)

        processor = TemplateProcessor(template_file)
        variables = {
            "number": 42,
            "string": "test",
            "float": 3.14,
            "zero": 0,
            "empty": "",
            "none": None,
        }

        result = processor.render_template("test", "content", variables)

        expected = """- Number: 42
- String: test
- Float: 3.14
- Zero: 0
- Empty: 
- None: None"""

        assert result.strip() == expected.strip()


class DummyTableGenerator:
    def __init__(self):
        self.called = []

    def generate_table_by_name(self, table_name: str) -> str:
        self.called.append(table_name)
        return f"<table for {table_name}>"


def test_template_processor_with_all_placeholders(mock_template_file):
    """Test template processor with all placeholders using shared mock template."""
    # Variables for replacement
    variables = {
        "month": "2025-01",
        "total_shaves": "1,234",
        "unique_shavers": "50",
        "avg_shaves_per_user": "24.7",
    }
    table_generator = DummyTableGenerator()

    # Use the shared mock template file
    processor = TemplateProcessor(templates_path=mock_template_file)
    result = processor.render_template("hardware", "report_template", variables, table_generator)

    # Validate variable replacement
    assert "# Hardware Report for 2025-01" in result
    assert "**Total Shaves:** 1,234" in result
    assert "**Unique Shavers:** 50" in result
    assert "**Avg Shaves/User:** 24.7" in result
    # Validate table placeholder replacement
    assert "<table for razors>" in result
    assert "<table for blades>" in result
    assert "<table for brushes>" in result
    assert "<table for top-shavers>" in result
    # Validate that all table names were called
    assert set(table_generator.called) == {"razors", "blades", "brushes", "top-shavers"}


def test_get_available_table_placeholders(mock_template_file):
    """Test getting available table placeholders from template."""
    processor = TemplateProcessor(templates_path=mock_template_file)
    placeholders = processor.get_available_table_placeholders("hardware")

    expected_placeholders = {"razors", "blades", "brushes", "top-shavers"}
    assert set(placeholders) == expected_placeholders
