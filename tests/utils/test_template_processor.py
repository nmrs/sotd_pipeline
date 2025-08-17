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
    Welcome to your SOTD Hardware Report for {{month_year}}

    ## Observations

    * [Observations will be generated based on data analysis]

    ## Notes & Caveats

    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report.

    * Average shaves per user: {{avg_shaves_per_user}}

    * I only show the top n results per category to keep the tables readable and avoid max post length issues.

    * Custom template content for testing

    ## Razor Formats

    {{tables.razor-formats}}

    ## Razors

    {{tables.razors}}

    ## Razor Manufacturers

    {{tables.razor-manufacturers}}

    ## Blades

    {{tables.blades}}

    ## Blade Manufacturers

    {{tables.blade-manufacturers}}

    ## Brushes

    {{tables.brushes}}

    ## Brush Handle Makers

    {{tables.brush-handle-makers}}

    ## Brush Knot Makers

    {{tables.brush-knot-makers}}

    ## Knot Fibers

    {{tables.knot-fibers}}

    ## Knot Sizes

    {{tables.knot-sizes}}

    ## Blackbird Plates

    {{tables.blackbird-plates}}

    ## Christopher Bradley Plates

    {{tables.christopher-bradley-plates}}

    ## Game Changer Plates

    {{tables.game-changer-plates}}

    ## Super Speed Tips

    {{tables.super-speed-tips}}

    ## Straight Widths

    {{tables.straight-widths}}

    ## Straight Grinds

    {{tables.straight-grinds}}

    ## Straight Points

    {{tables.straight-points}}

    ## Most Used Blades in Most Used Razors

    {{tables.razor-blade-combinations}}

    ## Highest Use Count per Blade

    {{tables.highest-use-count-per-blade}}

    ## Top Shavers

    {{tables.top-shavers}}

software:
  report_template: |
    Welcome to your SOTD Lather Log for {{month_year}}

    * {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report. Collectively, these shavers used {{unique_soaps}} distinct soaps from {{unique_brands}} distinct brands.

    ## Observations

    * [Observations will be generated based on data analysis]

    ## Notes & Caveats

    * I only show the top n results per category to keep the tables readable and avoid max post length issues.

    * The unique user column shows the number of different users who used a given brand/soap/etc in the month.

    * The Brand Diversity table details the number of distinct soaps used during the month from that particular brand.

    * The change Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

    ## Soap Makers

    {{tables.soap-makers}}

    ## Soaps

    {{tables.soaps}}

    ## Brand Diversity

    {{tables.brand-diversity}}

    ## Top Shavers

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
        assert processor.templates_path == Path("data/report_templates")

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
        assert "report_template" in templates["hardware"]
        assert "report_template" in templates["software"]
        assert "# Hardware Report" in templates["hardware"]["report_template"]
        assert "# Software Report" in templates["software"]["report_template"]

    def test_load_templates_directory_not_found(self, tmp_path):
        """Test loading templates from non-existent directory."""
        non_existent_dir = tmp_path / "nonexistent_templates"
        processor = TemplateProcessor(non_existent_dir)
        templates = processor._load_templates()
        assert templates == {}

    def test_load_templates_directory_empty(self, tmp_path):
        """Test loading templates from empty directory."""
        empty_dir = tmp_path / "empty_templates"
        empty_dir.mkdir()
        
        processor = TemplateProcessor(empty_dir)
        templates = processor._load_templates()
        assert templates == {}


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
        "month_year": "January 2025",
        "total_shaves": "1,234",
        "unique_shavers": "50",
        "avg_shaves_per_user": "24.7",
        "unique_soaps": "100",
        "unique_brands": "25",
    }
    table_generator = DummyTableGenerator()

    # Use the shared mock template file
    processor = TemplateProcessor(templates_path=mock_template_file)
    result = processor.render_template("hardware", "report_template", variables, table_generator)

    # Validate variable replacement
    assert "Welcome to your SOTD Hardware Report for January 2025" in result
    assert "1,234 shave reports from 50 distinct shavers" in result
    assert "Average shaves per user: 24.7" in result

    # Validate table placeholder replacement
    assert "<table for razor-formats>" in result
    assert "<table for razors>" in result
    assert "<table for razor-manufacturers>" in result
    assert "<table for blades>" in result
    assert "<table for brushes>" in result
    assert "<table for brush-handle-makers>" in result
    assert "<table for brush-knot-makers>" in result
    assert "<table for knot-fibers>" in result
    assert "<table for knot-sizes>" in result
    assert "<table for blackbird-plates>" in result
    assert "<table for christopher-bradley-plates>" in result
    assert "<table for game-changer-plates>" in result
    assert "<table for straight-widths>" in result
    assert "<table for straight-grinds>" in result
    assert "<table for straight-points>" in result
    assert "<table for razor-blade-combinations>" in result
    assert "<table for highest-use-count-per-blade>" in result
    assert "<table for top-shavers>" in result
    # Validate that all table names were called
    expected_tables = {
        "razor-formats",
        "razors",
        "razor-manufacturers",
        "blades",
        "blade-manufacturers",
        "brushes",
        "brush-handle-makers",
        "brush-knot-makers",
        "knot-fibers",
        "knot-sizes",
        "blackbird-plates",
        "christopher-bradley-plates",
        "game-changer-plates",
        "super-speed-tips",
        "straight-widths",
        "straight-grinds",
        "straight-points",
        "razor-blade-combinations",
        "highest-use-count-per-blade",
        "top-shavers",
    }
    assert set(table_generator.called) == expected_tables


def test_get_available_table_placeholders(mock_template_file):
    """Test getting available table placeholders from template."""
    processor = TemplateProcessor(templates_path=mock_template_file)
    placeholders = processor.get_available_table_placeholders("hardware")

    expected_placeholders = {
        "razor-formats",
        "razors",
        "razor-manufacturers",
        "blades",
        "blade-manufacturers",
        "brushes",
        "brush-handle-makers",
        "brush-knot-makers",
        "knot-fibers",
        "knot-sizes",
        "blackbird-plates",
        "christopher-bradley-plates",
        "game-changer-plates",
        "super-speed-tips",
        "straight-widths",
        "straight-grinds",
        "straight-points",
        "razor-blade-combinations",
        "highest-use-count-per-blade",
        "top-shavers",
    }
    assert set(placeholders) == expected_placeholders
