"""
Utility functions for enhanced regex error reporting.

This module provides functions to compile regex patterns with detailed error context,
making it easier to identify and fix malformed patterns in YAML catalog files.
"""

import re
from typing import Any, Dict, Optional


def compile_regex_with_context(pattern: str, context: Dict[str, Any]) -> Optional[Any]:
    """
    Compile regex pattern with detailed error context.

    Args:
        pattern: The regex pattern to compile
        context: Dict with context info (file, brand, model, line_number, etc.)

    Returns:
        Compiled regex pattern or None if compilation fails

    Raises:
        ValueError: If pattern compilation fails, with detailed context
    """
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        context_str = f"File: {context.get('file', 'unknown')}"
        if context.get("brand"):
            context_str += f", Brand: {context['brand']}"
        if context.get("model"):
            context_str += f", Model: {context['model']}"
        if context.get("format"):
            context_str += f", Format: {context['format']}"
        if context.get("maker"):
            context_str += f", Maker: {context['maker']}"
        if context.get("scent"):
            context_str += f", Scent: {context['scent']}"
        if context.get("section"):
            context_str += f", Section: {context['section']}"
        if context.get("strategy"):
            context_str += f", Strategy: {context['strategy']}"
        if context.get("field"):
            context_str += f", Field: {context['field']}"
        if context.get("line_number"):
            context_str += f", Line: {context['line_number']}"

        raise ValueError(f"Invalid regex pattern '{pattern}' in {context_str}: {e}") from e


def create_context_dict(
    file_path: str,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    format: Optional[str] = None,
    maker: Optional[str] = None,
    scent: Optional[str] = None,
    section: Optional[str] = None,
    strategy: Optional[str] = None,
    line_number: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a context dictionary for regex error reporting.

    Args:
        file_path: Path to the YAML file containing the pattern
        brand: Brand name (for razors, blades, brushes)
        model: Model name
        format: Format (for blades)
        maker: Maker name (for soaps, handles)
        scent: Scent name (for soaps)
        section: Section name (for handles)
        strategy: Strategy name (for brush matching strategies)
        line_number: Line number in the file (if known)

    Returns:
        Context dictionary for error reporting
    """
    context = {"file": file_path}

    if brand is not None:
        context["brand"] = brand
    if model is not None:
        context["model"] = model
    if format is not None:
        context["format"] = format
    if maker is not None:
        context["maker"] = maker
    if scent is not None:
        context["scent"] = scent
    if section is not None:
        context["section"] = section
    if strategy is not None:
        context["strategy"] = strategy
    if line_number is not None:
        context["line_number"] = str(line_number)

    return context
