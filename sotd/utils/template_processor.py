"""Template processor utility for the SOTD pipeline."""

from pathlib import Path
from typing import Any, Dict, Optional


class TemplateProcessor:
    """Template processor with mustache-style variable replacement and table placeholders."""

    def __init__(self, templates_path: Path = Path("data/report_templates")):
        """Initialize the template processor.

        Args:
            templates_path: Path to the templates directory
        """
        self.templates_path = templates_path
        self._templates = None

    def _load_templates(self) -> Dict[str, Any]:
        """Load templates from directory."""
        if self._templates is None:
            if not self.templates_path.exists():
                raise FileNotFoundError(f"Templates directory not found: {self.templates_path}")

            if not self.templates_path.is_dir():
                raise NotADirectoryError(
                    f"Templates path is not a directory: {self.templates_path}"
                )

            templates = {}
            for template_file in self.templates_path.glob("*.md"):
                template_name = template_file.stem
                template_content = template_file.read_text(encoding="utf-8")
                templates[template_name] = template_content

            if not templates:
                raise ValueError(f"No template files found in {self.templates_path}")

            self._templates = templates

        return self._templates

    def get_template(self, template_name: str) -> str:
        """Get a template by name.

        Args:
            template_name: Name of the template to retrieve

        Returns:
            Template content as string

        Raises:
            KeyError: If template name not found
        """
        templates = self._load_templates()
        if template_name not in templates:
            available = ", ".join(sorted(templates.keys()))
            raise KeyError(
                f"Template '{template_name}' not found. Available templates: {available}"
            )
        return templates[template_name]

    def process_template(
        self, template_name: str, variables: Dict[str, Any], tables: Optional[Dict[str, str]] = None
    ) -> str:
        """Process a template with variables and tables.

        Args:
            template_name: Name of the template to process
            variables: Dictionary of variables to substitute
            tables: Optional dictionary of table placeholders

        Returns:
            Processed template content
        """
        template = self.get_template(template_name)
        return self._process_content(template, variables, tables)

    def _process_content(
        self, content: str, variables: Dict[str, Any], tables: Optional[Dict[str, str]] = None
    ) -> str:
        """Process template content with variables and tables.

        Args:
            content: Template content to process
            variables: Dictionary of variables to substitute
            tables: Optional dictionary of table placeholders

        Returns:
            Processed content
        """
        # Process variables first
        processed = self._substitute_variables(content, variables)

        # Process table placeholders if provided
        if tables:
            processed = self._substitute_tables(processed, tables)

        return processed

    def _substitute_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template content.

        Args:
            content: Template content
            variables: Dictionary of variables to substitute

        Returns:
            Content with variables substituted
        """
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        return content

    def _substitute_tables(self, content: str, tables: Dict[str, str]) -> str:
        """Substitute table placeholders in template content.

        Args:
            content: Template content
            tables: Dictionary of table placeholders to substitute

        Returns:
            Content with table placeholders substituted
        """
        for key, value in tables.items():
            placeholder = f"{{{{tables.{key}}}}}"
            content = content.replace(placeholder, value)
        return content

    def list_templates(self) -> list[str]:
        """List available template names.

        Returns:
            List of available template names
        """
        templates = self._load_templates()
        return sorted(templates.keys())
