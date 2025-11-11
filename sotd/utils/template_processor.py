"""Template processor utility for the SOTD pipeline."""

import re
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

    def _validate_placeholders(
        self, content: str, variables: Dict[str, Any], tables: Optional[Dict[str, str]] = None
    ) -> None:
        """Validate that all placeholders in the template are recognized.

        Args:
            content: Template content to validate
            variables: Dictionary of available variables
            tables: Optional dictionary of available table placeholders

        Raises:
            ValueError: If any unrecognized placeholders are found
        """
        # Find all variable placeholders: {{variable_name}}
        variable_pattern = r"\{\{([^}]+)\}\}"
        all_placeholders = re.findall(variable_pattern, content)

        unrecognized_placeholders = []
        available_base_tables = set()

        for placeholder in all_placeholders:
            # Skip table placeholders as they're handled separately
            if placeholder.startswith("tables."):
                continue

            # Check if this is a variable placeholder
            if placeholder not in variables:
                unrecognized_placeholders.append(placeholder)

        # Check table placeholders if tables are provided
        if tables:
            table_pattern = r"\{\{tables\.([^|}]+)(?:\|[^}]*)?\}\}"
            table_placeholders = re.findall(table_pattern, content)

            # Extract base table names from available tables (remove parameters)
            for table_key in tables.keys():
                # Extract the base table name from enhanced table keys
                # e.g., "{{tables.razors|ranks:50|deltas:true}}" -> "razors"
                base_match = re.match(r"\{\{tables\.([^|}]+)(?:\|[^}]*)?\}\}", table_key)
                if base_match:
                    available_base_tables.add(base_match.group(1))
                else:
                    # Handle simple table keys (e.g., "blades", "razors")
                    available_base_tables.add(table_key)

            for table_name in table_placeholders:
                # Check if this base table name exists in available base tables
                if table_name not in available_base_tables:
                    unrecognized_placeholders.append(f"tables.{table_name}")

        if unrecognized_placeholders:
            # Sort for consistent error messages
            unrecognized_placeholders.sort()
            available_variables = sorted(variables.keys()) if variables else []
            available_base_tables_sorted = sorted(available_base_tables)

            error_msg = (
                f"Unrecognized template placeholders found: {', '.join(unrecognized_placeholders)}"
            )
            if available_variables:
                error_msg += f"\nAvailable variables: {', '.join(available_variables)}"
            if available_base_tables_sorted:
                error_msg += f"\nAvailable tables: {', '.join(available_base_tables_sorted)}"

            raise ValueError(error_msg)

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

        Raises:
            ValueError: If any unrecognized placeholders are found
        """
        template = self.get_template(template_name)

        # Validate all placeholders before processing (fail-fast)
        self._validate_placeholders(template, variables, tables)

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
        # OPTIMIZED: Use pandas operations for vectorized string replacement
        import pandas as pd

        if not variables:
            return content

        # Convert to pandas Series for vectorized string operations
        content_series = pd.Series([content])

        # Apply all replacements using vectorized operations
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content_series = content_series.str.replace(placeholder, str(value), regex=False)

        return content_series.iloc[0]

    def _substitute_tables(self, content: str, tables: Dict[str, str]) -> str:
        """Substitute table placeholders in template content.

        Args:
            content: Template content
            tables: Dictionary of table placeholders to substitute

        Returns:
            Content with table placeholders substituted
        """
        # OPTIMIZED: Use pandas operations for vectorized table replacement
        import pandas as pd

        if not tables:
            return content

        # Sort tables by length (longest first) to ensure enhanced placeholders
        # are replaced before basic ones, preventing partial replacements
        sorted_tables = sorted(tables.items(), key=lambda x: len(x[0]), reverse=True)

        # Convert to pandas Series for vectorized string operations
        content_series = pd.Series([content])

        # Apply all replacements using vectorized operations
        for placeholder, value in sorted_tables:
            # Replace the exact placeholder string using vectorized operations
            content_series = content_series.str.replace(placeholder, value, regex=False)

        return content_series.iloc[0]

    def list_templates(self) -> list[str]:
        """List available template names.

        Returns:
            List of available template names
        """
        templates = self._load_templates()
        return sorted(templates.keys())
