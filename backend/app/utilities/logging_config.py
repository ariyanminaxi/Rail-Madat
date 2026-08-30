"""Logging Configuration — consistent logging across all modules."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name.

    All loggers use the same formatter so that output is consistent
    across the application. In production, replace the StreamHandler
    with a file or external log collector handler.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
