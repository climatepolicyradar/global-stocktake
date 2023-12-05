import logging

from rich.logging import RichHandler


def get_logger(name: str) -> logging.Logger:
    """Return a logger with RichHandler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(RichHandler(rich_tracebacks=True))
    return logger
