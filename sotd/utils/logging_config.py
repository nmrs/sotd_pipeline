"""Centralized logging configuration for the SOTD pipeline."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_pipeline_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Setup logging configuration for pipeline phases.

    Automatically detects Docker environment by checking for LOG_DIR environment variable.
    If LOG_DIR is set (Docker mode), writes to $LOG_DIR/pipeline.log.
    If LOG_DIR is not set (terminal mode), writes to stdout only.

    Args:
        log_file: Optional path to log file. If None, auto-detects Docker environment.
        level: Logging level (default: INFO)
        format_string: Custom format string. If None, uses default format matching shell script.

    Returns:
        Configured logger instance
    """
    # Auto-detect Docker environment
    log_dir = os.getenv("LOG_DIR")
    if log_dir and log_file is None:
        log_file = Path(log_dir) / "pipeline.log"

    # Default format matches shell script: [YYYY-MM-DD HH:MM:SS] MESSAGE
    if format_string is None:
        format_string = "[%(asctime)s] %(message)s"

    # Create formatter with timestamp format matching shell script
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler (stdout) - always add for terminal mode
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log file specified (Docker mode)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
