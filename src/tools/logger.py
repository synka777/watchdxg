from pythonjsonlogger import jsonlogger
from config import settings
import logging
import sys


def setup_logger(name="etl"):
    """
    Sets up and returns a logger instance.

    Args:
        name (str): Name of the logger (usually your module or app name).
        use_json (bool): If True, use JSON format for structured logging (for Docker/log aggregators).

    Returns:
        logging.Logger: Configured logger instance.
    """

    # Create (or retrieve) a logger with the given name
    logger = logging.getLogger(name)
    level = logging.DEBUG if settings['logs']['debug'] else logging.INFO # Self-explanatory
    logger.setLevel(level)

    # Create a handler that outputs to stdout (console)
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter depending on format type requested
    use_json = True if settings['logs']['json'] else False
    if use_json:
        # JSON format for logs (Docker/Grafana/Loki-compatible)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(message)s'
        )
    else:
        # Simple, human-readable format (ideal for local dev)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Clear existing handlers to avoid duplicate logs
    logger.handlers = []

    # Attach the new handler
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Avoid propagating logs to root logger
    logger.propagate = False

    return logger


logger = setup_logger()