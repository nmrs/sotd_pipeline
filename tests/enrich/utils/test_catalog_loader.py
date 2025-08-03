"""Tests for catalog_loader.py."""

import pytest
from unittest.mock import patch, mock_open

from sotd.enrich.utils.catalog_loader import CatalogLoader


class TestCatalogLoader:
    """Test the CatalogLoader class."""

    def test_enhanced_regex_error_reporting(self):
        """Test that malformed regex patterns produce detailed error messages."""
        # Create a mock catalog with malformed regex
        mock_catalog_content = """
artisan_handles:
  Test Brand:
    Test Model:
      patterns:
        - "invalid[regex"  # Malformed regex - missing closing bracket
"""

        with patch("builtins.open", mock_open(read_data=mock_catalog_content)):
            with patch(
                "yaml.safe_load",
                return_value={
                    "artisan_handles": {
                        "Test Brand": {"Test Model": {"patterns": ["invalid[regex"]}}
                    }
                },
            ):
                loader = CatalogLoader()

                # This should raise an error when compiling patterns
                with pytest.raises(ValueError) as exc_info:
                    loader.load_compiled_handle_patterns("Test Brand", "Test Model")

                error_message = str(exc_info.value)
                assert "Invalid regex pattern" in error_message
                assert "invalid[regex" in error_message
                assert "File: data/handles.yaml" in error_message
                assert "Brand: Test Brand" in error_message
                assert "Model: Test Model" in error_message
                assert "unterminated character set" in error_message  # The actual regex error
