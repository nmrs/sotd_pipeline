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

    Uses the full path (e.g. "Nomad Theory -> scents -> Kyoto -> patterns") so
    duplicate key names in different branches (e.g. two "Kyoto" scents under
    different brands) report the correct line.

    Args:
        catalog_path: Path to the catalog file
        location: Location in the structure (e.g., "Miraculum -> patterns")

    Returns:
        Line number (1-indexed) or None if not found
    """
    try:
        # Parse the location path to get the key hierarchy
        # e.g., "Nomad Theory -> scents -> Kyoto -> patterns" -> ["Nomad Theory", "scents", "Kyoto", "patterns"]
        path_parts = [part.strip() for part in location.split(" -> ")]

        if len(path_parts) < 2 or path_parts[-1] != "patterns":
            return None

        # Read the file as text
        with catalog_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # Walk the full path so we match the right occurrence when keys repeat (e.g. two "Kyoto" scents)
        # path_parts[:-1] = hierarchy leading to the key that contains "patterns"
        key_chain = path_parts[:-1]  # e.g. ["Nomad Theory", "scents", "Kyoto"]
        if not key_chain:
            return None

        # Find each key in order at the correct indentation level
        # Candidates: list of (line_index, indent) for the current key level
        candidates = [(0, -1)]  # start at line 0 with indent -1 so any indent is deeper

        for key_idx, key_name in enumerate(key_chain):
            next_candidates = []
            for start_i, parent_indent in candidates:
                # Start after the parent line when we have a real parent, so we don't break on the parent's own indent
                start = start_i + 1 if parent_indent >= 0 else start_i
                for i in range(start, len(lines)):
                    line = lines[i]
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    indent = len(line) - len(line.lstrip())
                    # Same or less indent than parent means we left the parent block
                    if indent <= parent_indent and parent_indent >= 0:
                        break
                    # Exact match: key name followed by ":" (key: or "key":)
                    if stripped == f"{key_name}:" or stripped.startswith(f'"{key_name}"'):
                        next_candidates.append((i, indent))
                        # Don't break: there might be another occurrence later (wrong branch)
            if not next_candidates:
                return None
            candidates = next_candidates

        # candidates now holds (line_index, indent) for the last key in the chain (e.g. Kyoto)
        # Find "patterns:" under that key and return its line or the following invalid value line
        for parent_i, parent_indent in candidates:
            for j in range(parent_i + 1, min(len(lines), parent_i + 25)):
                check_line = lines[j]
                check_stripped = check_line.strip()
                check_indent = len(check_line) - len(check_line.lstrip())

                if (
                    check_stripped
                    and check_indent <= parent_indent
                    and not check_stripped.startswith("#")
                ):
                    break

                if check_stripped.startswith("patterns:") and check_indent > parent_indent:
                    for k in range(j + 1, min(len(lines), j + 3)):
                        next_line = lines[k]
                        next_stripped = next_line.strip()
                        next_indent = len(next_line) - len(next_line.lstrip())

                        if next_stripped and not next_stripped.startswith("#"):
                            # Check for non-list value first (same indent as patterns: is the value line)
                            if (
                                not next_stripped.startswith("-")
                                and (next_indent <= check_indent or next_indent == check_indent)
                            ):
                                return k + 1  # 1-indexed (value line)
                            if next_indent <= check_indent:
                                break

                    return j + 1  # 1-indexed (patterns line)

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
