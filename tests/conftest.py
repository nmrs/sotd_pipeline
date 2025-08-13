"""Root-level pytest configuration for SOTD Pipeline tests."""

import logging
import pytest


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging to suppress debug messages during tests."""
    # Set all loggers to WARNING level to suppress debug messages
    logging.getLogger().setLevel(logging.WARNING)

    # Set specific loggers that might be noisy to WARNING
    logging.getLogger("sotd").setLevel(logging.WARNING)
    logging.getLogger("sotd.match").setLevel(logging.WARNING)
    logging.getLogger("sotd.report").setLevel(logging.WARNING)
    logging.getLogger("sotd.aggregate").setLevel(logging.WARNING)
    logging.getLogger("sotd.extract").setLevel(logging.WARNING)

    # Set root logger to WARNING to catch any other loggers
    logging.getLogger().setLevel(logging.WARNING)
