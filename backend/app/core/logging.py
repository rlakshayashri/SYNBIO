import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
