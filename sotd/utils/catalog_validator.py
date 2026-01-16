"""Catalog validation utilities for detecting formatting errors in YAML catalog files."""

from pathlib import Path
from typing import Any, Dict, Optional


def validate_patterns_format(
    data: Dict[str, Any], catalog_path: Path, path_prefix: str = ""
) -> None:
    """
    Recursively validate that all 'patterns' keys in catalog data are lists, not strings.

    This function traverses the entire YAML structure and checks every 'patterns' key
    to ensure it's formatted as a list (with '-' prefix in YAML). If a 'patterns' key
    contains a string instead of a list, it raises a ValueError with clear context.

    Args:
        data: The catalog data dictionary to validate
        catalog_path: Path to the catalog file (for error messages)
        path_prefix: Current path in the structure (for error messages)

    Raises:
        ValueError: If any 'patterns' key contains a string instead of a list

    Examples:
        Valid structure:
            Brand:
              patterns:
              - pattern1
              - pattern2

        Invalid structure (will raise ValueError):
            Brand:
              patterns:
                pattern1  # Missing '-' prefix, treated as string
    """
    if not isinstance(data, dict):
        return

    for key, value in data.items():
        current_path = f"{path_prefix} -> {key}" if path_prefix else key

        if key == "patterns":
            # Found a patterns key - must be a list
            if not isinstance(value, list):
                # Find line number for better error reporting
                line_number = _find_line_number(catalog_path, current_path)
                # Build error message with context
                error_msg = _build_patterns_error_message(
                    catalog_path, current_path, value, line_number
                )
                raise ValueError(error_msg)
        elif isinstance(value, dict):
            # Recursively check nested dictionaries
            validate_patterns_format(value, catalog_path, current_path)
        elif isinstance(value, list):
            # Check if list contains dictionaries (for nested structures)
            for item in value:
                if isinstance(item, dict):
                    validate_patterns_format(item, catalog_path, current_path)


def _find_line_number(catalog_path: Path, location: str) -> Optional[int]:
    """
    Find the line number where a patterns key is located in the YAML file.

    Args:
        catalog_path: Path to the catalog file
        location: Location in the structure (e.g., "Miraculum -> patterns")

    Returns:
        Line number (1-indexed) or None if not found
    """
    try:
        # Parse the location path to get the key hierarchy
        # e.g., "Miraculum -> patterns" -> ["Miraculum", "patterns"]
        # or "DE -> Brand1 -> Model1 -> patterns" -> ["DE", "Brand1", "Model1", "patterns"]
        path_parts = [part.strip() for part in location.split(" -> ")]

        if len(path_parts) < 2 or path_parts[-1] != "patterns":
            return None

        # Read the file as text
        with catalog_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the parent key (the key that contains patterns)
        parent_key = path_parts[-2] if len(path_parts) >= 2 else None
        if not parent_key:
            return None

        # Search for the parent key, then find "patterns:" that follows it
        # We need to match the structure based on indentation
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Look for the parent key (must end with ":")
            if parent_key in stripped and stripped.endswith(":"):
                # Found the parent key, now look for "patterns:" in the following lines
                # Check indentation - patterns should be indented more than the parent
                parent_indent = len(line) - len(line.lstrip())

                for j in range(i + 1, min(len(lines), i + 20)):  # Check up to 20 lines ahead
                    check_line = lines[j]
                    check_stripped = check_line.strip()
                    check_indent = len(check_line) - len(check_line.lstrip())

                    # If we hit a line with same or less indentation, we've gone too far
                    if (
                        check_stripped
                        and check_indent <= parent_indent
                        and not check_stripped.startswith("#")
                    ):
                        break

                    # Look for "patterns:" that's indented more than parent
                    if check_stripped.startswith("patterns:") and check_indent > parent_indent:
                        # Found patterns line - check if it's followed by a non-list value
                        # (which would indicate the error)
                        for k in range(j + 1, min(len(lines), j + 3)):
                            next_line = lines[k]
                            next_stripped = next_line.strip()
                            next_indent = len(next_line) - len(next_line.lstrip())

                            # If we hit a line with same or less indentation, stop
                            if (
                                next_stripped
                                and next_indent <= check_indent
                                and not next_stripped.startswith("#")
                            ):
                                break

                            # If we find a non-list value (no "-" prefix), this is the error
                            if (
                                next_stripped
                                and not next_stripped.startswith("-")
                                and not next_stripped.startswith("#")
                            ):
                                return k + 1  # 1-indexed

                        # If patterns: is found but we can't find the value line, return patterns line
                        return j + 1  # 1-indexed

        return None
    except Exception:
        # If anything goes wrong, return None (line number is optional)
        return None


def _build_patterns_error_message(
    catalog_path: Path, location: str, actual_value: Any, line_number: Optional[int] = None
) -> str:
    """
    Build a clear, actionable error message for patterns formatting errors.

    Args:
        catalog_path: Path to the catalog file
        location: Location in the structure (e.g., "Miraculum -> patterns")
        actual_value: The actual value found (should be a string)

    Returns:
        Formatted error message string
    """
    # Get the key name from location (last part before "-> patterns")
    if " -> patterns" in location:
        key_name = location.split(" -> patterns")[0].split(" -> ")[-1]
    else:
        key_name = location.replace(" -> patterns", "")

    # Format the actual value for display
    if isinstance(actual_value, str):
        actual_display = f"str ('{actual_value}')"
        example_value = actual_value
    else:
        actual_display = f"{type(actual_value).__name__} ({actual_value!r})"
        example_value = "pattern1"

    # Build base error message
    location_str = f"'{location}'"
    if line_number:
        location_str += f" (line {line_number})"

    error_msg = (
        f"Invalid patterns format in {catalog_path} at {location_str}:\n"
        f"  Expected: list (e.g., ['pattern1', 'pattern2'])\n"
        f"  Got: {actual_display}\n"
        f"\n"
        f"  Fix: Change from:\n"
        f"    {key_name}:\n"
        f"      patterns:\n"
        f"        {example_value}\n"
        f"\n"
        f"  To:\n"
        f"    {key_name}:\n"
        f"      patterns:\n"
        f"      - {example_value}"
    )

    return error_msg
