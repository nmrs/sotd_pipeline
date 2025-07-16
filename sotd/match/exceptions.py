"""
Custom exceptions for brush matching operations.

Provides structured error handling with clear context and debugging information.
"""

from typing import Any, Dict, Optional


class BrushMatchingError(Exception):
    """Base exception for all brush matching errors."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}

    def __str__(self):
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{super().__str__()} (Context: {context_str})"
        return super().__str__()


class ConfigurationError(BrushMatchingError):
    """Configuration-related errors."""

    pass


class CatalogLoadError(BrushMatchingError):
    """Errors related to loading catalog files."""

    pass


class InvalidMatchDataError(BrushMatchingError):
    """Errors related to invalid match data or results."""

    pass


class ValidationError(BrushMatchingError):
    """Data validation errors."""

    pass


class CacheError(BrushMatchingError):
    """Cache-related errors."""

    pass
