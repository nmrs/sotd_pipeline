"""Template processor utility for the SOTD pipeline."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from .yaml_loader import load_yaml_with_nfc


class TemplateProcessor:
    """Template processor with mustache-style variable replacement and table placeholders."""

    def __init__(self, templates_path: Path = Path("data/report_templates.yaml")):
        """Initialize the template processor.

        Args:
            templates_path: Path to the YAML templates file
        """
        self.templates_path = templates_path
        self._templates = None

    def _load_templates(self) -> Dict[str, Any]:
        """Load templates from YAML file."""
        if self._templates is None:
            try:
                self._templates = load_yaml_with_nfc(self.templates_path)
            except FileNotFoundError:
                # Return empty dict if templates file doesn't exist
                self._templates = {}
        return self._templates

    def render_template(
        self,
        template_name: str,
        section: str,
        variables: Dict[str, Any],
        table_generator: Optional[Any] = None,
    ) -> str:
        """Render a template with variable replacement and table placeholders.

        Args:
            template_name: Name of the template (e.g., 'hardware', 'software')
            section: Section within the template (e.g., 'report_template')
            variables: Dictionary of variables to replace in the template
            table_generator: Optional table generator instance for table placeholders

        Returns:
            Rendered template string with variables and tables replaced

        Raises:
            KeyError: If template or section doesn't exist
        """
        templates = self._load_templates()

        if template_name not in templates:
            raise KeyError(f"Template '{template_name}' not found in {self.templates_path}")

        if section not in templates[template_name]:
            raise KeyError(f"Section '{section}' not found in template '{template_name}'")

        template_content = templates[template_name][section]

        # Perform variable replacement using simple regex
        result = template_content
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))

        # Perform table placeholder replacement if table_generator is provided
        if table_generator:
            result = self._replace_table_placeholders(result, table_generator)

        return result

    def _replace_table_placeholders(self, content: str, table_generator: Any) -> str:
        """Replace table placeholders with actual table content.

        Args:
            content: Template content with table placeholders
            table_generator: Table generator instance with generate_table method

        Returns:
            Content with table placeholders replaced
        """
        # Find all table placeholders: {{tables.table-name}}
        table_pattern = r"\{\{tables\.([^}]+)\}\}"

        def replace_table_placeholder(match):
            table_name = match.group(1)
            try:
                # Generate the table content
                table_content = table_generator.generate_table_by_name(table_name)
                return table_content if table_content else f"*No data available for {table_name}*"
            except Exception as e:
                return f"*Error generating table {table_name}: {e}*"

        return re.sub(table_pattern, replace_table_placeholder, content)

    def get_available_templates(self) -> Dict[str, list]:
        """Get list of available templates and their sections.

        Returns:
            Dictionary mapping template names to lists of available sections
        """
        templates = self._load_templates()
        return {name: list(content.keys()) for name, content in templates.items()}

    def get_available_table_placeholders(self, template_name: str) -> list:
        """Get list of available table placeholders for a template.

        Args:
            template_name: Name of the template (e.g., 'hardware', 'software')

        Returns:
            List of available table placeholder names
        """
        templates = self._load_templates()
        if template_name not in templates:
            return []

        # Extract table placeholders from the template content
        template_content = templates[template_name].get("report_template", "")
        table_pattern = r"\{\{tables\.([^}]+)\}\}"
        placeholders = re.findall(table_pattern, template_content)
        return list(set(placeholders))  # Remove duplicates
