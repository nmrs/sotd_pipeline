"""Shared fixtures for report tests."""

import pytest
import yaml
from pathlib import Path


@pytest.fixture(scope="session")
def report_template():
    """Load the shared report template YAML for testing."""
    template_path = Path(__file__).parent.parent / "fixtures" / "report_template.yaml"
    with open(template_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def template_file(tmp_path, report_template):
    """Create a temporary template file with the shared template content."""
    template_file = tmp_path / "report_templates.yaml"
    with open(template_file, "w") as f:
        yaml.dump(report_template, f)
    return template_file
