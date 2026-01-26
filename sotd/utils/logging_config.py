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

    # In Docker mode (log_file specified), stdout is already redirected to log file,
    # so we only need the file handler to avoid duplicates.
    # In terminal mode (log_file is None), we only need the console handler.
    if log_file:
        # Docker mode: only add file handler (stdout is already redirected)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Terminal mode: only add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def should_disable_tqdm() -> bool:
    """Determine if tqdm progress bars should be disabled.

    In Docker mode (when LOG_DIR is set), tqdm progress bars add noise to log files
    since stdout is redirected. Disable them in Docker mode, but keep them in terminal mode.

    Returns:
        True if tqdm should be disabled (Docker mode), False otherwise (terminal mode)
    """
    return os.getenv("LOG_DIR") is not None
