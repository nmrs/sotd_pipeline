"""Shared fixtures for report tests."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture(autouse=True)
def reset_rank_tracer():
    """Reset rank tracer state between tests to prevent global state issues."""
    from sotd.report.utils.rank_tracer import disable_rank_tracing

    # Ensure rank tracing is disabled before each test
    disable_rank_tracing()
    yield
    # Ensure rank tracing is disabled after each test
    disable_rank_tracing()


@pytest.fixture(scope="session")
def report_template():
    """Load the shared report template YAML for testing (backward compatibility)."""
    template_path = Path(__file__).parent.parent / "fixtures" / "report_template.yaml"
    with open(template_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def template_file(tmp_path, report_template):
    """Create a temporary template file with the shared template content (backward compatibility)."""
    template_file = tmp_path / "report_templates.yaml"
    with open(template_file, "w") as f:
        yaml.dump(report_template, f)
    return template_file


@pytest.fixture(scope="session")
def template_directory():
    """Get the path to the test template directory."""
    return Path(__file__).parent.parent / "fixtures" / "report_templates"


@pytest.fixture
def template_dir(tmp_path, template_directory):
    """Create a temporary template directory with the shared template content."""
    temp_dir = tmp_path / "report_templates"
    temp_dir.mkdir()

    # Copy all template files from the fixture directory
    for template_file in template_directory.glob("*.md"):
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        temp_template_file = temp_dir / template_file.name
        with open(temp_template_file, "w", encoding="utf-8") as f:
            f.write(content)

    return temp_dir
