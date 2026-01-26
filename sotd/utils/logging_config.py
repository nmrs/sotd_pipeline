"""Centralized logging configuration for the SOTD pipeline."""

import glob
import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_pipeline_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Setup logging configuration for pipeline phases.

    Automatically detects Docker environment by checking for LOG_DIR environment variable.
    If LOG_DIR is set (Docker mode), writes to $LOG_DIR/pipeline.log with weekly rotation.
    If LOG_DIR is not set (terminal mode), writes to stdout only.

    Log level is determined by:
    1. LOG_LEVEL environment variable (if set)
    2. level parameter (fallback if LOG_LEVEL not set)

    Args:
        log_file: Optional path to log file. If None, auto-detects Docker environment.
        level: Logging level (default: INFO, used as fallback if LOG_LEVEL not set)
        format_string: Custom format string. If None, uses default format with level indicator.

    Returns:
        Configured logger instance
    """
    # Read LOG_LEVEL from environment (default: INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    env_level = getattr(logging, log_level_str, level)  # Fallback to 'level' param

    # Use env level if LOG_LEVEL is set, otherwise use 'level' parameter
    effective_level = env_level if os.getenv("LOG_LEVEL") else level

    # Auto-detect Docker environment
    log_dir = os.getenv("LOG_DIR")
    if log_dir and log_file is None:
        log_file = Path(log_dir) / "pipeline.log"

    # Standardized format with level indicator: [YYYY-MM-DD HH:MM:SS] [LEVEL] MESSAGE
    if format_string is None:
        format_string = "[%(asctime)s] [%(levelname)s] %(message)s"

    # Create formatter with timestamp format matching shell script
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(effective_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # In Docker mode (log_file specified), stdout is already redirected to log file,
    # so we only need the file handler to avoid duplicates.
    # In terminal mode (log_file is None), we only need the console handler.
    if log_file:
        # Docker mode: Use TimedRotatingFileHandler with weekly rotation
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="W0",  # Weekly on Monday
            interval=1,
            backupCount=13,  # Keep ~13 weeks (90 days)
            encoding="utf-8",
        )
        file_handler.setLevel(effective_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Terminal mode: Use StreamHandler (no rotation needed)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(effective_level)
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


def cleanup_old_logs(log_dir: Path, retention_days: int = 90) -> None:
    """Delete log files older than retention_days.

    Finds all rotated log files matching pattern pipeline.log.* and deletes
    those older than the retention period.

    Args:
        log_dir: Directory containing log files
        retention_days: Number of days to retain logs (default: 90)
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    pattern = str(log_dir / "pipeline.log.*")

    for log_file in glob.glob(pattern):
        file_path = Path(log_file)
        if file_path.stat().st_mtime < cutoff_date.timestamp():
            file_path.unlink()


def should_disable_tqdm() -> bool:
    """Determine if tqdm progress bars should be disabled.

    In Docker mode (when LOG_DIR is set), tqdm progress bars add noise to log files
    since stdout is redirected. Disable them in Docker mode, but keep them in terminal mode.

    Returns:
        True if tqdm should be disabled (Docker mode), False otherwise (terminal mode)
    """
    return os.getenv("LOG_DIR") is not None
