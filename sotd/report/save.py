#!/usr/bin/env python3
"""File output functionality for the report phase."""

from pathlib import Path


def get_report_file_path(base_dir: Path, year: int, month: int, report_type: str) -> Path:
    """Get the path for the output report file.

    Args:
        base_dir: Base output directory
        year: Year of the report
        month: Month of the report
        report_type: Type of report ('hardware' or 'software')

    Returns:
        Path to the output report file
    """
    filename = f"{year:04d}-{month:02d}-{report_type}.md"
    return base_dir / "reports" / filename


def save_report(
    content: str,
    output_path: Path,
    force: bool = False,
    debug: bool = False,
) -> None:
    """Save report content to a markdown file.

    Args:
        content: Report content to save
        output_path: Path where to save the file
        force: Whether to force overwrite existing files
        debug: Enable debug logging

    Raises:
        OSError: If there are file system errors
    """
    if debug:
        print(f"[DEBUG] Saving report to: {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing file if force is True
    if force and output_path.exists():
        if debug:
            print(f"[DEBUG] Force flag set, removing existing file: {output_path}")
        output_path.unlink()

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        raise OSError(f"Failed to write report file {output_path}: {e}") from e

    if debug:
        print(f"[DEBUG] Successfully saved report to: {output_path}")


def generate_and_save_report(
    content: str,
    base_dir: Path,
    year: int,
    month: int,
    report_type: str,
    force: bool = False,
    debug: bool = False,
) -> Path:
    """Generate report file path and save content.

    Args:
        content: Report content to save
        base_dir: Base output directory
        year: Year of the report
        month: Month of the report
        report_type: Type of report ('hardware' or 'software')
        force: Whether to force overwrite existing files
        debug: Enable debug logging

    Returns:
        Path to the saved report file

    Raises:
        FileExistsError: If file exists and force=False
        OSError: If there are file system errors
    """
    output_path = get_report_file_path(base_dir, year, month, report_type)
    save_report(content, output_path, force, debug)
    return output_path
