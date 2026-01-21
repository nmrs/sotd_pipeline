"""
Utility functions for enhanced regex error reporting.

This module provides functions to compile regex patterns with detailed error context,
making it easier to identify and fix malformed patterns in YAML catalog files.
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional


def _find_pattern_line_number(
    file_path: str, pattern: str, brand: Optional[str] = None, scent: Optional[str] = None
) -> Optional[int]:
    """
    Find the line number where a pattern appears in a YAML file.

    Args:
        file_path: Path to the YAML file
        pattern: The regex pattern to find
        brand: Optional brand name to narrow search
        scent: Optional scent name to narrow search

    Returns:
        Line number (1-indexed) or None if not found
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # Search for the pattern in the file
        # Patterns in YAML are typically on lines starting with "- " followed by the pattern
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Check if this line contains the pattern
            # Patterns can be:
            #   - pattern_text
            #   - "pattern_text"
            #   - 'pattern_text'
            if stripped.startswith("-"):
                # Extract the value after the dash
                value_part = stripped[1:].strip()
                # Remove quotes if present
                if value_part.startswith('"') and value_part.endswith('"'):
                    value_part = value_part[1:-1]
                elif value_part.startswith("'") and value_part.endswith("'"):
                    value_part = value_part[1:-1]

                # Check if this matches our pattern
                if value_part == pattern:
                    # If we have brand/scent context, try to verify we're in the right section
                    # This is a best-effort check - we look backwards for the brand/scent
                    if brand or scent:
                        # Look backwards up to 50 lines to find brand/scent context
                        found_brand = brand is None
                        found_scent = scent is None
                        for i in range(max(0, line_num - 50), line_num):
                            check_line = lines[i].strip()
                            if (
                                brand
                                and not found_brand
                                and brand in check_line
                                and check_line.endswith(":")
                            ):
                                found_brand = True
                            if (
                                scent
                                and not found_scent
                                and scent in check_line
                                and check_line.endswith(":")
                            ):
                                found_scent = True
                        # If we have context but didn't find it, continue searching
                        if not (found_brand and found_scent):
                            continue
                    return line_num

        return None
    except Exception:
        # If anything goes wrong, return None (line number is optional)
        return None


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
        # If line_number is not in context, try to find it
        if "line_number" not in context or context.get("line_number") is None:
            file_path = context.get("file")
            if file_path:
                line_number = _find_pattern_line_number(
                    file_path,
                    pattern,
                    brand=context.get("brand"),
                    scent=context.get("scent"),
                )
                if line_number:
                    context["line_number"] = str(line_number)

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
